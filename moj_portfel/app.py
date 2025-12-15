# coding: utf-8
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

# -----------------------------
# SETTINGS
# -----------------------------
APP_TITLE = "Portfolio Tracker"
PASSWORD = "mojehaslo"  # docelowo: st.secrets["PASSWORD"]

# -----------------------------
# CSS (force light + własna tabela)
# -----------------------------
def inject_css():
    st.markdown(
        """
        <style>
        /* ===== FORCE LIGHT ===== */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f6f7fb !important;
            color: #0f172a !important;
        }
        .block-container { max-width: 980px; padding-top: 1rem; padding-bottom: 2rem; }

        /* ===== SIDEBAR ===== */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e5e7eb;
        }
        [data-testid="stSidebar"] * { color: #0f172a !important; }

        /* ===== HERO ===== */
        .hero {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 10px 25px rgba(15,23,42,0.06);
            margin-bottom: 16px;
        }
        .hero-title { margin: 0; font-size: 1.35rem; font-weight: 800; }
        .hero-subtitle { margin: 6px 0 0 0; font-size: 0.96rem; color: #475569; }

        /* ===== METRICS ===== */
        div[data-testid="metric-container"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 16px !important;
            padding: 14px !important;
            box-shadow: 0 8px 20px rgba(15,23,42,0.05);
        }
        div[data-testid="stMetricLabel"] { color: #475569 !important; font-weight: 600; }
        div[data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 800; }

        /* ===== INPUTS ===== */
        input, textarea {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 10px !important;
        }

        /* ===== MULTISELECT TAGS (BaseWeb) ===== */
        [data-baseweb="tag"] {
            background-color: #e0e7ff !important;
            color: #1e3a8a !important;
            border-radius: 999px !important;
            font-weight: 700 !important;
        }
        [data-baseweb="tag"] * { color: #1e3a8a !important; }

        /* ===== BUTTONS ===== */
        button {
            background-color: #2563eb !important;
            color: #ffffff !important;
            border-radius: 999px !important;
            border: none !important;
            font-weight: 800 !important;
        }
        button:hover { background-color: #1d4ed8 !important; }

        /* ===== CUSTOM TABLE ===== */
        .table-wrap {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(15,23,42,0.05);
            padding: 10px 10px 2px 10px;
            overflow-x: auto;
        }
        table.portfolio {
            width: 100%;
            border-collapse: collapse;
            min-width: 860px;
        }
        table.portfolio th {
            text-align: left;
            font-size: 0.85rem;
            color: #334155;
            background: #f8fafc;
            border-bottom: 1px solid #e5e7eb;
            padding: 10px 10px;
            position: sticky;
            top: 0;
        }
        table.portfolio td {
            font-size: 0.9rem;
            color: #0f172a;
            border-bottom: 1px solid #eef2f7;
            padding: 10px 10px;
            vertical-align: middle;
            white-space: nowrap;
        }
        .muted { color: #64748b; }
        .right { text-align: right; }
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 800;
        }
        .up { background: rgba(22,163,74,0.12); color: #166534; }
        .down { background: rgba(220,38,38,0.12); color: #991b1b; }
        .flat { background: rgba(100,116,139,0.14); color: #475569; }

        .pos { color: #166534; font-weight: 800; }
        .neg { color: #991b1b; font-weight: 800; }

        /* Hide streamlit chrome */
        #MainMenu {visibility:hidden;}
        footer {visibility:hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# PARSE POSITIONS
# -----------------------------
def parse_positions(text: str) -> pd.DataFrame:
    """
    Format:
    TICKER, ILOŚĆ [, CENA_ZAKUPU] [, KONTO]
    KONTO: IKE / IKZE / STANDARD (domyślnie STANDARD)
    """
    rows = []
    for line in text.splitlines():
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
            {"Ticker": ticker, "Quantity": qty, "PurchasePrice": purchase_price, "Account": account}
        )

    if not rows:
        return pd.DataFrame(columns=["Ticker", "Quantity", "PurchasePrice", "Account", "Category", "CurrencyHint"])

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

# -----------------------------
# MARKET DATA (BULK)
# -----------------------------
@st.cache_data(ttl=300)
def get_prices_bulk(tickers: list[str]) -> pd.DataFrame:
    """
    Pobiera 1mo danych dla wszystkich tickerów w 1 request (znacznie stabilniejsze na Cloud).
    Zwraca DataFrame z kolumnami: Ticker, Price, First1m, First1w
    """
    if not tickers:
        return pd.DataFrame(columns=["Ticker", "Price", "First1m", "First1w"])

    # threads=True pomaga, ale nadal to 1 endpoint; group_by="ticker" daje MultiIndex dla wielu tickerów
    raw = yf.download(
        tickers=" ".join(tickers),
        period="1mo",
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )

    # Normalizacja do: dict[ticker] -> series close
    results = []
    if raw.empty:
        return pd.DataFrame(columns=["Ticker", "Price", "First1m", "First1w"])

    # Jeśli tylko 1 ticker, raw ma zwykłe kolumny
    if isinstance(raw.columns, pd.Index) and "Close" in raw.columns:
        close = raw["Close"].dropna()
        if close.empty:
            results.append({"Ticker": tickers[0], "Price": np.nan, "First1m": np.nan, "First1w": np.nan})
        else:
            price = float(close.iloc[-1])
            first1m = float(close.iloc[0])
            last5 = close.tail(5)
            first1w = float(last5.iloc[0]) if len(last5) > 0 else np.nan
            results.append({"Ticker": tickers[0], "Price": price, "First1m": first1m, "First1w": first1w})
        return pd.DataFrame(results)

    # Wiele tickerów: MultiIndex (ticker, field)
    for t in tickers:
        try:
            # bywa, że Yahoo zwróci część tickerów
            if (t, "Close") in raw.columns:
                close = raw[(t, "Close")].dropna()
            else:
                # alternatywa: czasem jest układ (field, ticker)
                close = None
                if isinstance(raw.columns, pd.MultiIndex):
                    # spróbuj znaleźć po poziomach
                    cols = [c for c in raw.columns if len(c) == 2 and c[0] == t and c[1] == "Close"]
                    if cols:
                        close = raw[cols[0]].dropna()
                if close is None:
                    close = pd.Series(dtype=float)

            if close.empty:
                results.append({"Ticker": t, "Price": np.nan, "First1m": np.nan, "First1w": np.nan})
            else:
                price = float(close.iloc[-1])
                first1m = float(close.iloc[0])
                last5 = close.tail(5)
                first1w = float(last5.iloc[0]) if len(last5) > 0 else np.nan
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

def trend_badge(trend: str) -> str:
    if trend == "up":
        return '<span class="badge up">↑</span>'
    if trend == "down":
        return '<span class="badge down">↓</span>'
    if trend == "flat":
        return '<span class="badge flat">→</span>'
    return '<span class="badge flat">–</span>'

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

# -----------------------------
# APP
# -----------------------------
def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="💰", layout="wide")
    inject_css()

    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-title">💰 {APP_TITLE}</div>
          <div class="hero-subtitle">Akcje/ETF, krypto, IKE/IKZE. Stabilne pobieranie cen (bulk) + czytelna tabela.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar: Access
    st.sidebar.header("🔒 Dostęp")
    pw = st.sidebar.text_input("Hasło", type="password")
    if pw != PASSWORD:
        st.warning("Podaj poprawne hasło, aby zobaczyć portfel.")
        st.stop()

    st.sidebar.markdown("---")
    st.sidebar.header("🧾 Pozycje")
    st.sidebar.caption("Format: TICKER,ILOŚĆ[,CENA_ZAKUPU][,KONTO]")
    st.sidebar.caption("KONTO: IKE / IKZE (opcjonalnie). Krypto: BTC-USD, ETH-USD.")

    default_positions = (
        "BTC-USD,0.02,35000\n"
        "ETH-USD,0.5,2000\n"
        "TSLA,3,250\n"
        "ETFSP500.WA,10,125,IKZE\n"
        "ACN,26,320\n"
        "VWCE.DE,2,100,IKE"
    )

    positions_text = st.sidebar.text_area(
        "Twoje pozycje (1 linia = 1 pozycja)",
        value=default_positions,
        height=220,
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Odśwież"):
        st.cache_data.clear()
        st.rerun()

    df = parse_positions(positions_text)
    if df.empty:
        st.info("Dodaj pozycje w panelu po lewej.")
        return

    # FX
    usd_pln = fx_rate("USDPLN=X")
    eur_pln = fx_rate("EURPLN=X")

    # Bulk market data
    tickers = df["Ticker"].dropna().unique().tolist()
    with st.spinner("Pobieram ceny rynkowe (bulk)…"):
        bulk = get_prices_bulk(tickers)

    df = df.merge(bulk, on="Ticker", how="left")

    # Trendy
    df["Trend1m"] = df.apply(lambda r: compute_trend(r["Price"], r["First1m"]), axis=1)
    df["Trend1w"] = df.apply(lambda r: compute_trend(r["Price"], r["First1w"]), axis=1)

    # Currency (hint-based, stabilniejsze niż info z Yahoo)
    df["Currency"] = df["CurrencyHint"]

    # Value in PLN
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
    total_pln = float(valid["Value_PLN"].sum(skipna=True)) if not valid.empty else 0.0
    total_pl = float(valid["PL_Value_PLN"].sum(skipna=True)) if not valid.empty else np.nan

    # KPI
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Wartość portfela (PLN)", fmt_num(total_pln, 2))
    with c2:
        st.metric("USD/PLN", fmt_num(usd_pln, 4) if usd_pln is not None else "brak")
    with c3:
        st.metric("EUR/PLN", fmt_num(eur_pln, 4) if eur_pln is not None else "brak")
    with c4:
        st.metric("P/L (PLN)", fmt_num(total_pl, 2) if pd.notna(total_pl) else "—")

    st.caption("Aktualizacja: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Filters
    st.markdown("## Filtry")
    f1, f2 = st.columns(2)
    with f1:
        account_filter = st.multiselect(
            "Konto",
            ["STANDARD", "IKE", "IKZE"],
            default=["STANDARD", "IKE", "IKZE"],
        )
    with f2:
        cat_filter = st.multiselect(
            "Kategoria",
            ["STOCK", "CRYPTO", "IKE", "IKZE"],
            default=["STOCK", "CRYPTO", "IKE", "IKZE"],
        )

    view = df.copy()
    view = view[view["Account"].isin(account_filter)]
    view = view[view["Category"].isin(cat_filter)]

    # Missing prices report
    missing = view[view["Price"].isna()]["Ticker"].dropna().unique().tolist()
    if missing:
        st.warning("Brak danych cenowych dla: " + ", ".join(missing) + ". (Jeśli to ETF/GPW: sprawdź ticker w Yahoo.)")

    # Render table as HTML (light, nie czarny)
    st.markdown("## 📊 Pozycje")

    # w tej odchudzonej wersji „Name” = Ticker (stabilnie, bez info z Yahoo)
    view["Name"] = view["Ticker"]

    rows_html = []
    for _, r in view.iterrows():
        pl_val = r["PL_Value_PLN"]
        pl_cls = "pos" if pd.notna(pl_val) and pl_val >= 0 else "neg" if pd.notna(pl_val) else "muted"
        pl_txt = fmt_num(pl_val, 2)

        rows_html.append(
            f"""
            <tr>
              <td>{r["Name"]}</td>
              <td class="muted">{r["Ticker"]}</td>
              <td>{r["Account"]}</td>
              <td>{r["Category"]}</td>
              <td>{r["Currency"]}</td>
              <td class="right">{fmt_num(r["Quantity"], 4)}</td>
              <td class="right">{fmt_num(r["PurchasePrice"], 4)}</td>
              <td class="right">{fmt_num(r["Price"], 4)}</td>
              <td class="right">{fmt_num(r["Value_PLN"], 2)}</td>
              <td class="right {pl_cls}">{pl_txt}</td>
              <td class="right">{fmt_num(r["PL_Percent"], 2)}</td>
              <td>{trend_badge(r["Trend1w"])}</td>
              <td>{trend_badge(r["Trend1m"])}</td>
            </tr>
            """
        )

    table_html = f"""
    <div class="table-wrap">
      <table class="portfolio">
        <thead>
          <tr>
            <th>Name</th>
            <th>Ticker</th>
            <th>Account</th>
            <th>Category</th>
            <th>Curr</th>
            <th class="right">Qty</th>
            <th class="right">Buy</th>
            <th class="right">Price</th>
            <th class="right">Value (PLN)</th>
            <th class="right">P/L (PLN)</th>
            <th class="right">P/L %</th>
            <th>1W</th>
            <th>1M</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows_html)}
        </tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)

    # Export CSV
    export_cols = [
        "Ticker", "Account", "Category", "Currency", "Quantity",
        "PurchasePrice", "Price", "Value_PLN", "PL_Value_PLN", "PL_Percent",
        "Trend1w", "Trend1m",
    ]
    csv = view[export_cols].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Pobierz CSV", csv, file_name="portfolio.csv", mime="text/csv")

    # Portfolio composition
    st.markdown("## 📈 Struktura portfela")
    if not valid.empty and total_pln > 0:
        grp = (
            valid.groupby("Category", as_index=False)["Value_PLN"]
            .sum()
            .sort_values("Value_PLN", ascending=False)
        )
        fig = px.pie(grp, names="Category", values="Value_PLN", title="Udział kategorii (PLN)", template="plotly_white")
        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_color="#0f172a",
            title_font=dict(color="#0f172a"),
            legend_font_color="#0f172a",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brak danych do wykresu struktury (albo brak kursów FX).")


if __name__ == "__main__":
    main()
