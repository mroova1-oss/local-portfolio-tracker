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
PASSWORD = "mojehaslo"  # najlepiej przenieść do st.secrets na Streamlit Cloud


# -----------------------------
# STYLING (FORCE LIGHT + MOBILE FRIENDLY)
# -----------------------------
def inject_css():
    st.markdown(
        """
        <style>
        /* ===== FORCE LIGHT MODE ===== */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f6f7fb !important;
            color: #0f172a !important;
        }

        /* App container spacing */
        .block-container {
            max-width: 980px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }

        /* ===== SIDEBAR ===== */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e5e7eb;
        }
        [data-testid="stSidebar"] * {
            color: #0f172a !important;
        }

        /* ===== HEADERS & TEXT ===== */
        h1, h2, h3, h4, h5, h6, p, span, label, small {
            color: #0f172a !important;
        }
        .stCaption, [data-testid="stCaptionContainer"] {
            color: #475569 !important;
        }

        /* ===== HERO CARD ===== */
        .hero {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 10px 25px rgba(15,23,42,0.06);
            margin-bottom: 16px;
        }
        .hero-title {
            margin: 0;
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: 0.01em;
        }
        .hero-subtitle {
            margin: 6px 0 0 0;
            font-size: 0.96rem;
            color: #475569 !important;
        }

        /* ===== METRICS ===== */
        div[data-testid="metric-container"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 16px !important;
            padding: 14px !important;
            box-shadow: 0 8px 20px rgba(15,23,42,0.05);
        }
        div[data-testid="stMetricLabel"] {
            color: #475569 !important;
            font-size: 0.9rem;
            font-weight: 600;
        }
        div[data-testid="stMetricValue"] {
            color: #0f172a !important;
            font-size: 1.8rem;
            font-weight: 800;
        }

        /* ===== INPUTS ===== */
        input, textarea, select {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 10px !important;
        }

        /* ===== MULTISELECT TAGS (BaseWeb) ===== */
        div[data-baseweb="tag"] {
            background-color: #e0e7ff !important;
            color: #1e3a8a !important;
            border-radius: 999px !important;
            font-weight: 600 !important;
        }
        div[data-baseweb="tag"] span {
            color: #1e3a8a !important;
        }

        /* ===== BUTTONS ===== */
        button {
            background-color: #2563eb !important;
            color: #ffffff !important;
            border-radius: 999px !important;
            border: none !important;
            font-weight: 700 !important;
        }
        button:hover {
            background-color: #1d4ed8 !important;
        }

        /* ===== DATAFRAME ===== */
        [data-testid="stDataFrame"] {
            background-color: #ffffff !important;
            border-radius: 12px !important;
            border: 1px solid #e5e7eb !important;
            overflow: hidden !important;
        }

        /* Plotly container */
        [data-testid="stPlotlyChart"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 16px !important;
            padding: 12px !important;
            box-shadow: 0 8px 20px rgba(15,23,42,0.05) !important;
        }

        /* Hide Streamlit chrome */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
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
        return pd.DataFrame(columns=["Ticker", "Quantity", "PurchasePrice", "Account", "Category"])

    df = pd.DataFrame(rows)

    def categorize(row):
        if row["Account"] in ("IKE", "IKZE"):
            return row["Account"]
        if str(row["Ticker"]).endswith("-USD"):
            return "CRYPTO"
        return "STOCK"

    df["Category"] = df.apply(categorize, axis=1)
    return df


# -----------------------------
# MARKET DATA
# -----------------------------
@st.cache_data(ttl=300)
def get_ticker_data(ticker: str):
    """
    Returns: price, name, trend_1m, trend_1w, currency
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


def trend_symbol(x):
    return "↑" if x == "up" else "↓" if x == "down" else "→" if x == "flat" else "–"


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
          <div class="hero-subtitle">Akcje/ETF, krypto, IKE/IKZE. Live ceny z Yahoo Finance. Widok mobilny-friendly.</div>
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
    st.sidebar.caption("KONTO: IKE / IKZE (opcjonalnie). Krypto zwykle kończy się na -USD.")
    st.sidebar.caption("Przykład: VWCE.DE,2,100,IKE")

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

    # Fetch market data
    prices, names, t1m, t1w, currs, missing = [], [], [], [], [], []
    with st.spinner("Pobieram ceny rynkowe..."):
        for _, row in df.iterrows():
            p, n, m, w, c = get_ticker_data(row["Ticker"])
            if p is None:
                prices.append(np.nan)
                names.append(None)
                t1m.append(None)
                t1w.append(None)
                currs.append(None)
                missing.append(row["Ticker"])
            else:
                prices.append(p)
                names.append(n)
                t1m.append(m)
                t1w.append(w)
                currs.append(c)

    df["Name"] = names
    df["Price"] = prices
    df["Trend1m"] = t1m
    df["Trend1w"] = t1w
    df["Currency"] = currs

    # Value in PLN
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
    df["PL_Percent"] = np.where(
        df["PurchaseValue_PLN"] > 0,
        df["PL_Value_PLN"] / df["PurchaseValue_PLN"] * 100,
        np.nan
    )

    # Convenience USD value
    if usd_pln is not None:
        df["Value_USD"] = df["Value_PLN"] / usd_pln
    else:
        df["Value_USD"] = np.nan

    valid = df.dropna(subset=["Price"])

    total_pln = float(valid["Value_PLN"].sum(skipna=True)) if not valid.empty else 0.0
    total_pl = float(valid["PL_Value_PLN"].sum(skipna=True)) if not valid.empty else np.nan

    # KPI
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Wartość portfela (PLN)", f"{total_pln:,.2f}")
    with c2:
        st.metric("USD/PLN", f"{usd_pln:,.4f}" if usd_pln is not None else "brak")
    with c3:
        st.metric("EUR/PLN", f"{eur_pln:,.4f}" if eur_pln is not None else "brak")
    with c4:
        st.metric("P/L (PLN)", f"{total_pl:,.2f}" if pd.notna(total_pl) else "—")

    st.caption("Aktualizacja: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Filters
    st.markdown("### Filtry")
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

    view["T1W"] = view["Trend1w"].apply(trend_symbol)
    view["T1M"] = view["Trend1m"].apply(trend_symbol)

    st.markdown("### 📊 Pozycje")

    display = view[[
        "Name", "Ticker", "Account", "Category", "Currency",
        "Quantity", "PurchasePrice", "Price",
        "Value_PLN", "PL_Value_PLN", "PL_Percent",
        "T1W", "T1M"
    ]].copy()

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Quantity": st.column_config.NumberColumn("Qty", format="%.4f"),
            "PurchasePrice": st.column_config.NumberColumn("Buy Price", format="%.4f"),
            "Price": st.column_config.NumberColumn("Price", format="%.4f"),
            "Value_PLN": st.column_config.NumberColumn("Value (PLN)", format="%.2f"),
            "PL_Value_PLN": st.column_config.NumberColumn("P/L (PLN)", format="%.2f"),
            "PL_Percent": st.column_config.NumberColumn("P/L (%)", format="%.2f"),
        },
    )

    csv = display.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Pobierz CSV", csv, file_name="portfolio.csv", mime="text/csv")

    if missing:
        st.warning("Brak danych cenowych dla: " + ", ".join(sorted(set(missing))))

    st.markdown("### 📈 Struktura portfela")
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
        st.info("Brak danych do wykresu struktury.")


if __name__ == "__main__":
    main()
