# coding: utf-8
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

# -----------------------------
# USTAWIENIA
# -----------------------------
APP_TITLE = "Portfolio Tracker"
PASSWORD = "mojehaslo"  # najlepiej przenieść do secrets (patrz niżej)

# -----------------------------
# CSS (lekko mobilne)
# -----------------------------
def inject_css():
    st.markdown(
        """
        <style>
        :root{
          --bg:#f5f7fb; --card:#ffffff; --border:#e6e9f2;
          --text:#0f172a; --muted:#64748b;
          --primary:#2563eb; --good:#16a34a; --bad:#dc2626;
        }

        [data-testid="stAppViewContainer"] { background: var(--bg); }
        [data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--border); }

        /* zwężenie contentu na desktop, a na mobile i tak się układa */
        .block-container { max-width: 980px; padding-top: 1rem; }

        .hero {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 16px;
          padding: 14px 16px;
          box-shadow: 0 8px 22px rgba(15,23,42,0.06);
          margin-bottom: 12px;
        }
        .hero h1 { margin: 0; font-size: 1.35rem; }
        .hero p  { margin: 4px 0 0 0; color: var(--muted); font-size: 0.95rem; }

        /* przyciski */
        button { border-radius: 999px !important; }

        /* metric cards */
        div[data-testid="metric-container"]{
          background: var(--card) !important;
          border: 1px solid var(--border) !important;
          border-radius: 16px !important;
          padding: 14px 12px !important;
          box-shadow: 0 8px 22px rgba(15,23,42,0.05) !important;
        }

        /* małe “badge” */
        .badge { display:inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.82rem; }
        .up { background: rgba(22,163,74,0.10); color: var(--good); }
        .down { background: rgba(220,38,38,0.10); color: var(--bad); }
        .flat { background: rgba(100,116,139,0.12); color: var(--muted); }

        /* ukryj menu */
        #MainMenu {visibility:hidden;}
        footer {visibility:hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# PARSOWANIE POZYCJI
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

        qty = None
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

    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Ticker","Quantity","PurchasePrice","Account"])

    def categorize(row):
        if row["Account"] in ("IKE", "IKZE"):
            return row["Account"]
        if str(row["Ticker"]).endswith("-USD"):
            return "CRYPTO"
        return "STOCK"

    if not df.empty:
        df["Category"] = df.apply(categorize, axis=1)

    return df

# -----------------------------
# DANE RYNKOWE
# -----------------------------
@st.cache_data(ttl=300)
def get_ticker_data(ticker: str):
    """
    Zwraca: price, name, trend_1m, trend_1w, currency
    """
    try:
        t = yf.Ticker(ticker)
        hist_m = t.history(period="1mo")
        hist_w = t.history(period="5d")

        if hist_m.empty:
            return None, None, None, None, None

        price = float(hist_m["Close"].iloc[-1])
        first_m = float(hist_m["Close"].iloc[0])

        if price > first_m:
            trend_m = "up"
        elif price < first_m:
            trend_m = "down"
        else:
            trend_m = "flat"

        trend_w = None
        if not hist_w.empty:
            first_w = float(hist_w["Close"].iloc[0])
            if price > first_w:
                trend_w = "up"
            elif price < first_w:
                trend_w = "down"
            else:
                trend_w = "flat"

        info = getattr(t, "info", {}) or {}
        name = info.get("longName") or info.get("shortName") or ticker
        currency = info.get("currency") or "USD"

        return price, name, trend_m, trend_w, currency
    except Exception:
        return None, None, None, None, None

@st.cache_data(ttl=300)
def fx_rate(symbol: str):
    try:
        fx = yf.Ticker(symbol)
        hist = fx.history(period="1d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None

def trend_badge(t):
    if t == "up":
        return '<span class="badge up">↑</span>'
    if t == "down":
        return '<span class="badge down">↓</span>'
    if t == "flat":
        return '<span class="badge flat">→</span>'
    return '<span class="badge flat">–</span>'

# -----------------------------
# APP
# -----------------------------
def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="💰", layout="wide")
    inject_css()

    st.markdown(
        f"""
        <div class="hero">
          <h1>💰 {APP_TITLE}</h1>
          <p>Akcje/ETF, krypto, IKE/IKZE. Live ceny z Yahoo Finance. Widok mobilny-friendly.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Sidebar: dostęp ---
    st.sidebar.header("🔒 Dostęp")
    pw = st.sidebar.text_input("Hasło", type="password")
    if pw != PASSWORD:
        st.warning("Podaj poprawne hasło, aby zobaczyć portfel.")
        st.stop()

    st.sidebar.markdown("---")
    st.sidebar.header("🧾 Pozycje")
    st.sidebar.caption("Format: TICKER,ILOŚĆ[,CENA_ZAKUPU][,KONTO]")
    st.sidebar.caption("KONTO: IKE / IKZE (opcjonalnie). Krypto najczęściej kończy się na -USD.")

    default_positions = (
        "BTC-USD,0.02,35000\n"
        "ETH-USD,0.5,2000\n"
        "TSLA,3,250\n"
        "ETFSP500.WA,10,125,IKZE\n"
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

    # pobranie rynkowe
    prices, names, t1m, t1w, currs, missing = [], [], [], [], [], []
    with st.spinner("Pobieram ceny rynkowe..."):
        for _, row in df.iterrows():
            p, n, m, w, c = get_ticker_data(row["Ticker"])
            if p is None:
                prices.append(np.nan); names.append(None); t1m.append(None); t1w.append(None); currs.append(None)
                missing.append(row["Ticker"])
            else:
                prices.append(p); names.append(n); t1m.append(m); t1w.append(w); currs.append(c)

    df["Name"] = names
    df["Price"] = prices
    df["Trend1m"] = t1m
    df["Trend1w"] = t1w
    df["Currency"] = currs

    def value_pln(row):
        if pd.isna(row["Price"]) or pd.isna(row["Quantity"]) or row["Currency"] is None:
            return np.nan
        if row["Currency"] == "PLN":
            return row["Price"] * row["Quantity"]
        if row["Currency"] == "USD":
            return np.nan if usd_pln is None else row["Price"] * row["Quantity"] * usd_pln
        if row["Currency"] == "EUR":
            return np.nan if eur_pln is None else row["Price"] * row["Quantity"] * eur_pln
        return np.nan

    def purchase_value_pln(row):
        if pd.isna(row["PurchasePrice"]) or pd.isna(row["Quantity"]) or row["Currency"] is None:
            return np.nan
        if row["Currency"] == "PLN":
            return row["PurchasePrice"] * row["Quantity"]
        if row["Currency"] == "USD":
            return np.nan if usd_pln is None else row["PurchasePrice"] * row["Quantity"] * usd_pln
        if row["Currency"] == "EUR":
            return np.nan if eur_pln is None else row["PurchasePrice"] * row["Quantity"] * eur_pln
        return np.nan

    df["Value_PLN"] = df.apply(value_pln, axis=1)
    df["PurchaseValue_PLN"] = df.apply(purchase_value_pln, axis=1)
    df["PL_Value_PLN"] = df["Value_PLN"] - df["PurchaseValue_PLN"]
    df["PL_Percent"] = np.where(df["PurchaseValue_PLN"] > 0, df["PL_Value_PLN"] / df["PurchaseValue_PLN"] * 100, np.nan)

    # USD value only as convenience
    if usd_pln is not None:
        df["Value_USD"] = df["Value_PLN"] / usd_pln
    else:
        df["Value_USD"] = np.nan

    valid = df.dropna(subset=["Price"])

    # --- KPI (mobilne: i tak się zwiną w dół) ---
    c1, c2, c3, c4 = st.columns(4)
    total_pln = float(valid["Value_PLN"].sum(skipna=True)) if not valid.empty else 0.0
    total_pl = float(valid["PL_Value_PLN"].sum(skipna=True)) if not valid.empty else np.nan

    with c1:
        st.metric("Wartość portfela (PLN)", f"{total_pln:,.2f}")
    with c2:
        if usd_pln is not None:
            st.metric("USD/PLN", f"{usd_pln:,.4f}")
        else:
            st.metric("USD/PLN", "brak")
    with c3:
        if eur_pln is not None:
            st.metric("EUR/PLN", f"{eur_pln:,.4f}")
        else:
            st.metric("EUR/PLN", "brak")
    with c4:
        if pd.notna(total_pl):
            st.metric("P/L (PLN)", f"{total_pl:,.2f}")
        else:
            st.metric("P/L (PLN)", "—")

    st.caption("Aktualizacja: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # --- Filtry (ważne na mobile) ---
    f1, f2 = st.columns([1, 1])
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

    # --- Tabela: responsywna (streamlit dataframe) ---
    # Dodajemy proste kolumny trendu jako badge (HTML w markdown obok tabeli byłoby cięższe),
    # więc tu trzymamy symbole tekstowe.
    def trend_symbol(x):
        return "↑" if x == "up" else "↓" if x == "down" else "→" if x == "flat" else "–"

    view["T1W"] = view["Trend1w"].apply(trend_symbol)
    view["T1M"] = view["Trend1m"].apply(trend_symbol)

    display = view[[
        "Name", "Ticker", "Account", "Category", "Currency",
        "Quantity", "PurchasePrice", "Price",
        "Value_PLN", "PL_Value_PLN", "PL_Percent",
        "T1W", "T1M"
    ]].copy()

    # formatowanie liczb
    for col in ["Quantity", "PurchasePrice", "Price", "Value_PLN", "PL_Value_PLN", "PL_Percent"]:
        display[col] = pd.to_numeric(display[col], errors="coerce")

    st.subheader("📊 Pozycje")
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Value_PLN": st.column_config.NumberColumn("Value (PLN)", format="%.2f"),
            "PL_Value_PLN": st.column_config.NumberColumn("P/L (PLN)", format="%.2f"),
            "PL_Percent": st.column_config.NumberColumn("P/L (%)", format="%.2f"),
            "PurchasePrice": st.column_config.NumberColumn("Buy Price", format="%.4f"),
            "Price": st.column_config.NumberColumn("Price", format="%.4f"),
            "Quantity": st.column_config.NumberColumn("Qty", format="%.4f"),
        },
    )

    # Export CSV
    csv = display.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Pobierz CSV", csv, file_name="portfolio.csv", mime="text/csv")

    if missing:
        st.warning("Brak danych cenowych dla: " + ", ".join(sorted(set(missing))))

    # --- Mini-wykres: udział kategorii (PLN) ---
    st.subheader("📈 Struktura portfela")
    if not valid.empty and total_pln > 0:
        grp = (
            valid.groupby("Category", as_index=False)["Value_PLN"]
            .sum()
            .sort_values("Value_PLN", ascending=False)
        )
        fig = px.pie(grp, names="Category", values="Value_PLN", title="Udział kategorii (PLN)", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Brak danych do wykresu struktury.")

if __name__ == "__main__":
    main()
