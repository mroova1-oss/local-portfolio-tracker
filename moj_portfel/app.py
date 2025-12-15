# coding: utf-8
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

# ======================================================
# SETTINGS
# ======================================================
APP_TITLE = "Portfolio Tracker"
PASSWORD = st.secrets["PASSWORD"]  # Streamlit Cloud -> Settings -> Secrets

SAVE_FILE = Path("saved_positions.txt")  # proste zapisywanie między sesjami (single-user)
SETTINGS_FILE = Path("saved_settings.json")

# ======================================================
# CSS (Light, readable metrics, mobile-friendly)
# ======================================================
def inject_css():
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f6f7fb !important;
            color: #0f172a !important;
        }
        .block-container { max-width: 1020px; padding-top: 0.75rem; padding-bottom: 2rem; }

        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e5e7eb;
        }
        [data-testid="stSidebar"] * { color: #0f172a !important; }

        .hero {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 10px 25px rgba(15,23,42,0.06);
            margin-bottom: 14px;
        }
        .hero-title { margin: 0; font-size: 1.25rem; font-weight: 850; }
        .hero-subtitle { margin: 6px 0 0 0; font-size: 0.95rem; color: #475569; }

        /* Metrics - ensure label visible */
        div[data-testid="metric-container"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 16px !important;
            padding: 14px !important;
            box-shadow: 0 8px 20px rgba(15,23,42,0.05);
        }
        div[data-testid="stMetricLabel"] {
            color: #475569 !important;
            font-weight: 700 !important;
            font-size: 0.90rem !important;
        }
        div[data-testid="stMetricValue"] {
            color: #0f172a !important;
            font-weight: 900 !important;
            font-size: 1.65rem !important;
        }

        input, textarea {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 10px !important;
        }

        button {
            background-color: #2563eb !important;
            color: #ffffff !important;
            border-radius: 999px !important;
            border: none !important;
            font-weight: 900 !important;
        }
        button:hover { background-color: #1d4ed8 !important; }

        /* Multiselect tags (BaseWeb) */
        [data-baseweb="tag"] {
            background-color: #e0e7ff !important;
            color: #1e3a8a !important;
            border-radius: 999px !important;
            font-weight: 800 !important;
        }
        [data-baseweb="tag"] * { color: #1e3a8a !important; }

        #MainMenu {visibility:hidden;}
        footer {visibility:hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ======================================================
# Persistence (simple local file)
# ======================================================
def load_saved_positions() -> str | None:
    if SAVE_FILE.exists():
        try:
            return SAVE_FILE.read_text(encoding="utf-8")
        except Exception:
            return None
    return None


def save_positions(text: str):
    try:
        SAVE_FILE.write_text(text or "", encoding="utf-8")
    except Exception:
        pass


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_settings(d: dict):
    try:
        SETTINGS_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ======================================================
# Parsing
# ======================================================
def parse_positions(text: str) -> pd.DataFrame:
    """
    Format:
    TICKER, ILOŚĆ [, CENA_ZAKUPU] [, KONTO]

    KONTO: IKE / IKZE / STANDARD
    """
    rows = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue

        ticker = parts[0].upper()

        try:
            qty = float(parts[1].replace(",", "."))
        except ValueError:
            continue

        purchase_price = np.nan
        if len(parts) >= 3 and parts[2] != "":
            try:
                purchase_price = float(parts[2].replace(",", "."))
            except ValueError:
                purchase_price = np.nan

        account = "STANDARD"
        if len(parts) >= 4:
            acc = parts[3].upper()
            if acc.startswith("IKE"):
                account = "IKE"
            elif acc.startswith("IKZE"):
                account = "IKZE"

        rows.append(
            {
                "Ticker": ticker,
                "Quantity": qty,
                "PurchasePrice": purchase_price,
                "Account": account,
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=["Ticker", "Quantity", "PurchasePrice", "Account", "Category", "CurrencyHint"]
        )

    df = pd.DataFrame(rows)

    def category(row):
        if row["Account"] in ("IKE", "IKZE"):
            return row["Account"]
        if str(row["Ticker"]).endswith("-USD"):
            return "CRYPTO"
        return "STOCK"

    def currency_hint(ticker: str) -> str:
        t = ticker.upper()
        if t.endswith("-USD"):
            return "USD"
        if t.endswith(".WA") or t.endswith(".PL"):
            return "PLN"
        if t.endswith(".DE") or t.endswith(".F") or t.endswith(".AS") or t.endswith(".PA") or t.endswith(".MI"):
            return "EUR"
        return "USD"

    df["Category"] = df.apply(category, axis=1)
    df["CurrencyHint"] = df["Ticker"].apply(currency_hint)
    return df


# ======================================================
# Market data (bulk)
# ======================================================
@st.cache_data(ttl=300)
def get_prices_bulk(tickers: list[str]) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame(columns=["Ticker", "Price", "First1m", "First1w"])

    raw = yf.download(
        tickers=" ".join(tickers),
        period="1mo",
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )

    if raw is None or raw.empty:
        return pd.DataFrame(columns=["Ticker", "Price", "First1m", "First1w"])

    # single ticker
    if isinstance(raw.columns, pd.Index) and "Close" in raw.columns:
        close = raw["Close"].dropna()
        if close.empty:
            return pd.DataFrame([{"Ticker": tickers[0], "Price": np.nan, "First1m": np.nan, "First1w": np.nan}])
        price = float(close.iloc[-1])
        first1m = float(close.iloc[0])
        last5 = close.tail(5)
        first1w = float(last5.iloc[0]) if len(last5) else np.nan
        return pd.DataFrame([{"Ticker": tickers[0], "Price": price, "First1m": first1m, "First1w": first1w}])

    results = []
    for t in tickers:
        try:
            if (t, "Close") in raw.columns:
                close = raw[(t, "Close")].dropna()
            else:
                close = pd.Series(dtype=float)

            if close.empty:
                results.append({"Ticker": t, "Price": np.nan, "First1m": np.nan, "First1w": np.nan})
            else:
                price = float(close.iloc[-1])
                first1m = float(close.iloc[0])
                last5 = close.tail(5)
                first1w = float(last5.iloc[0]) if len(last5) else np.nan
                results.append({"Ticker": t, "Price": price, "First1m": first1m, "First1w": first1w})
        except Exception:
            results.append({"Ticker": t, "Price": np.nan, "First1m": np.nan, "First1w": np.nan})

    return pd.DataFrame(results)


@st.cache_data(ttl=300)
def fx_rate(symbol: str):
    try:
        fx = yf.download(symbol, period="5d", interval="1d", progress=False)
        if fx is None or fx.empty or "Close" not in fx.columns:
            return None
        close = fx["Close"].dropna()
        if close.empty:
            return None
        return float(close.iloc[-1])
    except Exception:
        return None


# Name lookup – minimal + stable
NAME_MAP = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "SOL-USD": "Solana",
    "ADA-USD": "Cardano",
    "XRP-USD": "XRP",
    "DOGE-USD": "Dogecoin",
}


@st.cache_data(ttl=86400)
def get_name_slow(ticker: str) -> str:
    # Nie polegamy na tym w 100% (Yahoo bywa kapryśne), ale jako uzupełnienie jest OK.
    if ticker in NAME_MAP:
        return NAME_MAP[ticker]
    try:
        t = yf.Ticker(ticker)
        info = getattr(t, "info", {}) or {}
        nm = info.get("shortName") or info.get("longName")
        if nm and isinstance(nm, str):
            # skróć absurdalnie długie nazwy
            nm = nm.strip()
            return nm[:60]
    except Exception:
        pass
    return ticker


def compute_trend(price: float, first: float) -> str | None:
    if np.isnan(price) or np.isnan(first) or first == 0:
        return None
    if price > first:
        return "up"
    if price < first:
        return "down"
    return "flat"


def fmt_num(x, digits=2):
    if pd.isna(x):
        return "—"
    return f"{x:,.{digits}f}"


def badge(trend: str | None) -> str:
    if trend == "up":
        return '<span class="badge up">↑</span>'
    if trend == "down":
        return '<span class="badge down">↓</span>'
    if trend == "flat":
        return '<span class="badge flat">→</span>'
    return '<span class="badge flat">–</span>'


# ======================================================
# HTML table rendered via components.html (so it never prints <tr> text)
# Column order requested:
# Name, Value Since Purchase (VPN) PLN, %, 1M, 1W, Ticker, Category, Currency, Qty, Buy, Price
# ======================================================
def render_table_component(view: pd.DataFrame):
    css = """
    <style>
      body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 0; }
      .table-wrap{
        background:#fff; border:1px solid #e5e7eb; border-radius:16px;
        box-shadow:0 10px 25px rgba(15,23,42,0.05);
        padding:10px 10px 2px 10px; overflow-x:auto;
      }
      table{ width:100%; border-collapse:collapse; min-width: 980px; }
      th{
        text-align:left; font-size:0.85rem; color:#334155; background:#f8fafc;
        border-bottom:1px solid #e5e7eb; padding:10px 10px; position:sticky; top:0;
        white-space:nowrap;
      }
      td{
        font-size:0.9rem; color:#0f172a; border-bottom:1px solid #eef2f7;
        padding:10px 10px; white-space:nowrap; vertical-align:middle;
      }
      .muted{ color:#64748b; }
      .right{ text-align:right; }
      .pos{ color:#166534; font-weight:900; }
      .neg{ color:#991b1b; font-weight:900; }
      .badge{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:0.82rem; font-weight:900; }
      .up{ background:rgba(22,163,74,0.12); color:#166534; }
      .down{ background:rgba(220,38,38,0.12); color:#991b1b; }
      .flat{ background:rgba(100,116,139,0.14); color:#475569; }
    </style>
    """

    rows = []
    for _, r in view.iterrows():
        vpn = r["PL_Value_PLN"]
        vpn_cls = "pos" if pd.notna(vpn) and vpn >= 0 else "neg" if pd.notna(vpn) else "muted"

        pct = r["PL_Percent"]
        pct_txt = fmt_num(pct, 2)

        rows.append(
            f"""
            <tr>
              <td>{r["Name"]}</td>
              <td class="right {vpn_cls}">{fmt_num(vpn, 2)}</td>
              <td class="right">{pct_txt}</td>
              <td>{badge(r["Trend1m"])}</td>
              <td>{badge(r["Trend1w"])}</td>
              <td class="muted">{r["Ticker"]}</td>
              <td>{r["Category"]}</td>
              <td>{r["Currency"]}</td>
              <td class="right">{fmt_num(r["Quantity"], 4)}</td>
              <td class="right">{fmt_num(r["PurchasePrice"], 4)}</td>
              <td class="right">{fmt_num(r["Price"], 4)}</td>
            </tr>
            """
        )

    html = f"""
    {css}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th class="right">Value Since Purchase (VPN) PLN</th>
            <th class="right">%</th>
            <th>1M</th>
            <th>1W</th>
            <th>Ticker</th>
            <th>Category</th>
            <th>Currency</th>
            <th class="right">Qty</th>
            <th class="right">Buy</th>
            <th class="right">Price</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>
    """

    height = min(820, 150 + 44 * max(1, len(view)))
    components.html(html, height=height, scrolling=True)


# ======================================================
# App
# ======================================================
def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="💰", layout="wide")
    inject_css()

    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-title">💰 {APP_TITLE}</div>
          <div class="hero-subtitle">Portfel (akcje/ETF, krypto, IKE/IKZE). Mobilny widok, stabilne ceny (bulk), prywatne hasło.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- Sidebar: Access
    st.sidebar.header("🔒 Dostęp")
    pw = st.sidebar.text_input("Hasło", type="password")
    if pw != PASSWORD:
        st.warning("Podaj poprawne hasło, aby zobaczyć portfel.")
        st.stop()

    # ---------------- Sidebar: Positions (persisted)
    st.sidebar.markdown("---")
    st.sidebar.header("🧾 Pozycje")
    st.sidebar.caption("Format: TICKER,ILOŚĆ[,CENA_ZAKUPU][,KONTO]  (KONTO: IKE/IKZE opcjonalnie)")

    default_positions = (
        "BTC-USD,0.02,35000\n"
        "ETH-USD,0.5,2000\n"
        "TSLA,3,250\n"
        "ETFSP500.WA,10,125,IKZE\n"
        "ACN,26,320\n"
        "VWCE.DE,2,100,IKE"
    )

    if "positions_text" not in st.session_state:
        saved = load_saved_positions()
        st.session_state["positions_text"] = saved if (saved and saved.strip()) else default_positions

    def on_positions_change():
        save_positions(st.session_state["positions_text"])

    positions_text = st.sidebar.text_area(
        "Twoje pozycje (1 linia = 1 pozycja)",
        key="positions_text",
        height=220,
        on_change=on_positions_change,
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Odśwież"):
        st.cache_data.clear()
        st.rerun()

    # ---------------- Parse
    df = parse_positions(positions_text)
    if df.empty:
        st.info("Dodaj pozycje w panelu po lewej.")
        return

    # ---------------- FX + Prices
    usd_pln = fx_rate("USDPLN=X")
    eur_pln = fx_rate("EURPLN=X")

    tickers = df["Ticker"].dropna().unique().tolist()
    with st.spinner("Pobieram ceny rynkowe (bulk)…"):
        bulk = get_prices_bulk(tickers)

    df = df.merge(bulk, on="Ticker", how="left")
    df["Trend1m"] = df.apply(lambda r: compute_trend(r["Price"], r["First1m"]), axis=1)
    df["Trend1w"] = df.apply(lambda r: compute_trend(r["Price"], r["First1w"]), axis=1)
    df["Currency"] = df["CurrencyHint"]

    # ---------------- Names
    # (cache 1/day; for crypto uses map)
    df["Name"] = df["Ticker"].apply(get_name_slow)

    # ---------------- Values
    def value_pln(row):
        if pd.isna(row["Price"]) or pd.isna(row["Quantity"]):
            return np.nan
        curr = row["Currency"]
        if curr == "PLN":
            return row["Price"] * row["Quantity"]
        if curr == "USD":
            return np.nan if usd_pln is None else row["Price"] * row["Quantity"] * usd_pln
        if curr == "EUR":
            return np.nan if eur_pln is None else row["Price"] * row["Quantity"] * eur_pln
        return np.nan

    def purchase_value_pln(row):
        if pd.isna(row["PurchasePrice"]) or pd.isna(row["Quantity"]):
            return np.nan
        curr = row["Currency"]
        if curr == "PLN":
            return row["PurchasePrice"] * row["Quantity"]
        if curr == "USD":
            return np.nan if usd_pln is None else row["PurchasePrice"] * row["Quantity"] * usd_pln
        if curr == "EUR":
            return np.nan if eur_pln is None else row["PurchasePrice"] * row["Quantity"] * eur_pln
        return np.nan

    df["Value_PLN"] = df.apply(value_pln, axis=1)
    df["PurchaseValue_PLN"] = df.apply(purchase_value_pln, axis=1)
    df["PL_Value_PLN"] = df["Value_PLN"] - df["PurchaseValue_PLN"]
    df["PL_Percent"] = np.where(
        df["PurchaseValue_PLN"] > 0,
        df["PL_Value_PLN"] / df["PurchaseValue_PLN"] * 100,
        np.nan,
    )

    valid = df.dropna(subset=["Price"])

    # ---------------- Top Metrics (requested order)
    total_pln = float(valid["Value_PLN"].sum(skipna=True)) if not valid.empty else 0.0

    by_curr = (
        valid.groupby("Currency", as_index=False)["Value_PLN"]
        .sum()
        .set_index("Currency")["Value_PLN"]
        .to_dict()
        if not valid.empty
        else {}
    )
    total_usd_assets_pln = float(by_curr.get("USD", 0.0))
    total_eur_assets_pln = float(by_curr.get("EUR", 0.0))
    total_pln_assets_pln = float(by_curr.get("PLN", 0.0))

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total value (PLN)", fmt_num(total_pln, 2))
    with k2:
        st.metric("Assets in USD (PLN)", fmt_num(total_usd_assets_pln, 2))
    with k3:
        st.metric("Assets in EUR (PLN)", fmt_num(total_eur_assets_pln, 2))
    with k4:
        st.metric("Assets in PLN (PLN)", fmt_num(total_pln_assets_pln, 2))

    st.caption("Aktualizacja: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # ---------------- Filters (one consolidated space)
    st.markdown("## Filtry")
    with st.container():
        a, b, c = st.columns([1.2, 1.2, 1.0])

        with a:
            account_filter = st.multiselect(
                "Konto",
                ["STANDARD", "IKE", "IKZE"],
                default=["STANDARD", "IKE", "IKZE"],
            )
        with b:
            cat_filter = st.multiselect(
                "Kategoria",
                ["STOCK", "CRYPTO", "IKE", "IKZE"],
                default=["STOCK", "CRYPTO", "IKE", "IKZE"],
            )
        with c:
            curr_filter = st.multiselect(
                "Waluta",
                ["USD", "EUR", "PLN"],
                default=["USD", "EUR", "PLN"],
            )

    view = df[
        df["Account"].isin(account_filter)
        & df["Category"].isin(cat_filter)
        & df["Currency"].isin(curr_filter)
    ].copy()

    missing = view[view["Price"].isna()]["Ticker"].dropna().unique().tolist()
    if missing:
        st.warning("Brak danych cenowych dla: " + ", ".join(missing) + ". (Sprawdź ticker w Yahoo Finance.)")

    # ---------------- Table
    st.markdown("## 📊 Pozycje")
    render_table_component(view)

    # ---------------- Export
    export_cols = [
        "Name",
        "PL_Value_PLN",
        "PL_Percent",
        "Trend1m",
        "Trend1w",
        "Ticker",
        "Category",
        "Currency",
        "Quantity",
        "PurchasePrice",
        "Price",
        "Value_PLN",
    ]
    csv = view[export_cols].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Pobierz CSV", csv, file_name="portfolio.csv", mime="text/csv")

    # ---------------- Composition chart
    st.markdown("## 📈 Struktura portfela")
    if not valid.empty and total_pln > 0:
        grp = (
            valid.groupby("Category", as_index=False)["Value_PLN"]
            .sum()
            .sort_values("Value_PLN", ascending=False)
        )
        fig = px.pie(grp, names="Category", values="Value_PLN", title="Udział kategorii (PLN)", template="plotly_white")
        fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_color="#0f172a")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brak danych do wykresu struktury.")


if __name__ == "__main__":
    main()
