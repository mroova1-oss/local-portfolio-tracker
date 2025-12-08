# coding: utf-8
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

# ------------------------------------------------------
# KONFIGURACJA HASŁA
# ------------------------------------------------------
PASSWORD = "mojehaslo"   # ZMIEŃ NA SWOJE HASŁO


# ------------------------------------------------------
# ZAŁOŻENIA DO PROGNOZ
# ------------------------------------------------------
BONDS_RATE_ANNUAL = 0.03
PPK_RATE_ANNUAL = 0.04

PPK_EMP_RATE = 0.015
PPK_ER_RATE = 0.015
PPK_STATE_ANNUAL = 240.0


# ------------------------------------------------------
# STYLIZACJA (CSS)
# ------------------------------------------------------
def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --primary-color: #2563eb;      /* niebieski */
            --accent-color:  #f97316;      /* lekko pomaranczowy */
            --bg-main:       #f3f4f6;      /* jasnoszary */
            --bg-card:       #ffffff;
            --border-soft:   #e5e7eb;
            --text-main:     #111827;
            --text-muted:    #6b7280;
        }

        html, body {
            background: var(--bg-main);
        }

        /* Globalne wymuszenie jasnego tekstu */
        body, body * {
            color: var(--text-main) !important;
            box-shadow: none;
        }

        /* Glowna kolumna - centrowanie i max szerokosc */
        [data-testid="stAppViewContainer"] > .main .block-container {
            max-width: 1000px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            margin: 0 auto;
        }

        [data-testid="stAppViewContainer"] {
            background: var(--bg-main);
        }

        /* Sidebar - jasny, bez czerni */
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--border-soft);
        }

        [data-testid="stSidebar"] * {
            color: var(--text-main) !important;
        }

        /* Pola input / textarea / select - jasne tlo, ciemny tekst */
        input, textarea, select {
            background: #f9fafb !important;
            color: var(--text-main) !important;
            border: 1px solid var(--border-soft) !important;
        }

        /* Przyciski (w tym "Odswiez") */
        button, [data-testid="stSidebar"] button {
            background: var(--primary-color) !important;
            color: #ffffff !important;
            border-radius: 999px !important;
            border: none !important;
        }
        button:hover, [data-testid="stSidebar"] button:hover {
            filter: brightness(0.95);
        }

        /* Naglowek aplikacji */
        .app-title {
            font-weight: 700;
            letter-spacing: 0.02em;
            margin-bottom: 0.3rem;
        }

        .app-subtitle {
            text-align: center;
            color: var(--text-muted) !important;
            max-width: 620px;
            margin: 0 auto 1.5rem auto;
            font-size: 0.95rem;
        }

        /* Karty metric - hero sekcja */
        div[data-testid="metric-container"] {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border-soft) !important;
            padding: 20px 18px !important;
            border-radius: 16px !important;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06) !important;
        }

        div[data-testid="stMetricLabel"] {
            color: #4b5563 !important;
            font-size: 0.95rem !important;
            font-weight: 500 !important;
        }

        div[data-testid="stMetricValue"] {
            font-size: 2.0rem !important;
            font-weight: 700 !important;
            color: #111827 !important;
        }

        /* 3. metric (FX) - mniejsza liczba */
        div[data-testid="metric-container"]:nth-of-type(3) div[data-testid="stMetricValue"] {
            font-size: 1.4rem !important;
        }

        /* Tabele - pandas HTML (overview & savings) */
        table.dataframe {
            border-collapse: collapse;
            width: 100%;
            background: var(--bg-card);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 10px rgba(15, 23, 42, 0.03);
        }
        table.dataframe th, table.dataframe td {
            border: 1px solid #e5e7eb;
            padding: 0.45rem 0.65rem;
            font-size: 0.9rem;
            color: var(--text-main) !important;
        }
        table.dataframe th {
            background-color: #f9fafb;
            font-weight: 600;
        }

        /* Tabela w zakladce Pozycje rynkowe */
        .portfolio-table {
            max-width: 1000px;
            margin: 0 auto;
        }
        .portfolio-table table {
            border-collapse: collapse;
            width: 100%;
            background: var(--bg-card);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 10px rgba(15, 23, 42, 0.03);
        }
        .portfolio-table th, .portfolio-table td {
            border: 1px solid #e5e7eb;
            padding: 0.45rem 0.65rem;
            font-size: 0.9rem;
            text-align: right;
            color: var(--text-main) !important;
        }
        .portfolio-table th:nth-child(1),
        .portfolio-table td:nth-child(1),
        .portfolio-table th:nth-child(2),
        .portfolio-table td:nth-child(2) {
            text-align: left;
        }
        .portfolio-table th {
            background-color: #f9fafb;
            font-weight: 600;
        }

        /* Ikony trendu i P/L */
        .trend-up { color: #16a34a !important; font-weight: 600; }
        .trend-down { color: #dc2626 !important; font-weight: 600; }
        .trend-flat { color: #6b7280 !important; }

        .pl-positive { color: #16a34a !important; font-weight: 600; }
        .pl-negative { color: #dc2626 !important; font-weight: 600; }

        /* Zakladki - zawsze widoczne */
        button[role="tab"] {
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
            color: var(--text-muted) !important;
            border-bottom: 2px solid transparent !important;
            background: transparent !important;
        }
        button[role="tab"][aria-selected="true"] {
            color: var(--text-main) !important;
            border-bottom: 2px solid var(--accent-color) !important;
        }

        /* Plotly - jasne tlo, zadnej czerni */
        .stPlotlyChart {
            background-color: var(--bg-card) !important;
            padding: 1rem !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06) !important;
        }

        /* Alerty (info, warning, success) - jasne tlo, ciemny tekst */
        .stAlert {
            background-color: #fefce8 !important;  /* pastelowy zolty */
            color: #92400e !important;
            border-radius: 12px !important;
            border: 1px solid #facc15 !important;
        }

        /* Usuniecie defaultowego menu/footera Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: visible;}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------
# FUNKCJE POBIERANIA DANYCH
# ------------------------------------------------------
def parse_positions(text: str) -> pd.DataFrame:
    """
    Format linii:
    TICKER,ILOŚĆ[,CENA_ZAKUPU][,KONTO]
    """
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            st.warning(f"Niepoprawna linia: {line}")
            continue

        ticker = parts[0].upper()

        qty_str = parts[1].replace(",", ".")
        try:
            qty = float(qty_str)
        except ValueError:
            st.warning(f"Nie mogę odczytać ilości z: {line}")
            continue

        purchase_price = None
        if len(parts) >= 3 and parts[2] != "":
            purchase_str = parts[2].replace(",", ".")
            try:
                purchase_price = float(purchase_str)
            except ValueError:
                purchase_price = None

        if len(parts) >= 4:
            acc_raw = parts[3].upper()
            if acc_raw.startswith("IKE"):
                account = "IKE"
            elif acc_raw.startswith("IKZE"):
                account = "IKZE"
            else:
                account = "STANDARD"
        else:
            account = "STANDARD"

        rows.append(
            {
                "Ticker": ticker,
                "Quantity": qty,
                "PurchasePrice": purchase_price,
                "Account": account,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["Ticker", "Quantity", "PurchasePrice", "Account"])

    df = pd.DataFrame(rows)

    def categorize(row):
        if row["Account"] in ("IKE", "IKZE"):
            return row["Account"]
        if row["Ticker"].endswith("-USD"):
            return "CRYPTO"
        return "STOCK/OTHER"

    df["Category"] = df.apply(categorize, axis=1)
    return df


@st.cache_data(ttl=300)
def get_ticker_data(ticker: str):
    """
    Zwraca:
    - price
    - name
    - trend_m (up/down/flat/None)
    - trend_w (up/down/flat/None)
    - currency (USD/PLN/EUR/...)
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

        if not hist_w.empty:
            first_w = float(hist_w["Close"].iloc[0])
            if price > first_w:
                trend_w = "up"
            elif price < first_w:
                trend_w = "down"
            else:
                trend_w = "flat"
        else:
            trend_w = None

        info = getattr(t, "info", {}) or {}
        name = info.get("longName") or info.get("shortName") or ticker
        currency = info.get("currency") or "USD"

        return price, name, trend_m, trend_w, currency

    except Exception:
        return None, None, None, None, None


@st.cache_data(ttl=300)
def get_fx_rate_usd_pln():
    try:
        fx = yf.Ticker("USDPLN=X")
        hist = fx.history(period="1d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_fx_rate_eur_pln():
    try:
        fx = yf.Ticker("EURPLN=X")
        hist = fx.history(period="1d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None


# ------------------------------------------------------
# FUNKCJE – PROJEKCJE
# ------------------------------------------------------
def project_bonds(value, years):
    return value * ((1 + BONDS_RATE_ANNUAL) ** years)


def project_ppk_custom(current_value_pln, salary_brutto, years):
    """
    Projekcja PPK:
    - value = obecna wartość
    - salary_brutto = Twoje wynagrodzenie brutto miesięcznie
    """
    months = years * 12
    monthly_rate = (1 + PPK_RATE_ANNUAL) ** (1 / 12) - 1
    monthly_contrib = salary_brutto * (PPK_EMP_RATE + PPK_ER_RATE) + PPK_STATE_ANNUAL / 12.0

    total = current_value_pln
    for _ in range(months):
        total = total * (1 + monthly_rate) + monthly_contrib
    return total


# ------------------------------------------------------
# FUNKCJA – RETIREMENT (MODEL „DO 90 LAT”)
# ------------------------------------------------------
def required_capital_finite_horizon(
    monthly_needs_today: float,
    years_to_retirement: int,
    years_of_retirement: int,
    inflation: float,
    zus_monthly_today: float,
    real_return: float,
):
    """
    Zwraca:
    - required_capital: wymagany kapitał na starcie emerytury
    - future_monthly_needs: przyszłe miesięczne koszty (po inflacji)
    - future_yearly_needs: roczne koszty (po inflacji, przed ZUS)
    - yearly_gap_after_zus: roczne koszty do pokrycia z oszczędności
    """
    growth_factor = (1 + inflation) ** years_to_retirement

    future_monthly_needs = monthly_needs_today * growth_factor
    future_yearly_needs = future_monthly_needs * 12

    zus_annual_today = zus_monthly_today * 12.0
    zus_annual_future = zus_annual_today * growth_factor

    yearly_gap_after_zus = max(future_yearly_needs - zus_annual_future, 0.0)

    if years_of_retirement <= 0 or yearly_gap_after_zus == 0:
        return 0.0, future_monthly_needs, future_yearly_needs, yearly_gap_after_zus

    if real_return > 0:
        factor = (1 - (1 + real_return) ** (-years_of_retirement)) / real_return
        required_capital = yearly_gap_after_zus * factor
    else:
        required_capital = yearly_gap_after_zus * years_of_retirement

    return required_capital, future_monthly_needs, future_yearly_needs, yearly_gap_after_zus


# ------------------------------------------------------
# FUNKCJA – PROGNOZA KAPITAŁU (PENSION PROGRESS)
# ------------------------------------------------------
def simulate_future_wealth(initial, monthly_saving, years_to_retirement, annual_return):
    """
    Symuluje wzrost kapitału z miesięcznymi wpłatami.
    Zwraca listę wartości kapitału na koniec każdego roku.
    """
    value = initial
    if years_to_retirement <= 0:
        return []

    monthly_rate = (1 + annual_return) ** (1 / 12) - 1
    values = []
    for _ in range(years_to_retirement):
        for _m in range(12):
            value = (value + monthly_saving) * (1 + monthly_rate)
        values.append(value)
    return values


def required_monthly_saving(target, current, years_to_retirement, annual_return):
    """
    Liczy, ile trzeba odkładać miesięcznie, aby osiągnąć target
    przy danej stopie zwrotu (annual_return) i current kapitale startowym.
    """
    if years_to_retirement <= 0:
        return 0.0

    if target <= current:
        return 0.0

    months = years_to_retirement * 12
    monthly_rate = (1 + annual_return) ** (1 / 12) - 1

    if monthly_rate == 0:
        return (target - current) / months

    future_current = current * ((1 + monthly_rate) ** months)
    numerator = (target - future_current) * monthly_rate
    denominator = ((1 + monthly_rate) ** months - 1)

    if denominator <= 0:
        return 0.0

    pmt = numerator / denominator
    return max(pmt, 0.0)


# ------------------------------------------------------
# GŁÓWNA FUNKCJA APLIKACJI
# ------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Local Portfolio Tracker & Pension Plan",
        page_icon="💰",
        layout="wide",
    )
    inject_css()

    # GŁÓWNY NAGŁÓWEK
    st.markdown('<h1 class="app-title">💰 Local Portfolio Tracker & Pension Plan</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="app-subtitle">Twoje portfolio, Twoje bezpieczeństwo. Dane rynkowe + planowanie finansowe.</p>',
        unsafe_allow_html=True,
    )

    # ---------------- SIDEBAR – dostęp ----------------
    st.sidebar.header("🔒 Dostęp")
    pw = st.sidebar.text_input("Hasło dostępu", type="password", key="password_input")

    if pw != PASSWORD:
        st.warning("Podaj poprawne hasło, aby zobaczyć swój portfel.")
        st.stop()

    st.sidebar.markdown("---")

    st.sidebar.header("🧾 Twoje pozycje")

    st.sidebar.markdown(
        """
Format wprowadzania pozycji:

`TICKER,ILOŚĆ[,CENA_ZAKUPU][,KONTO]`

Przykłady:
- `BTC-USD,0.02,35000`
- `TSLA,3,250`
- `ETFSP500.WA,10,125,IKZE`
- `ETFABC.DE,7,90,IKE`
"""
    )

    default_positions = (
        "BTC-USD,0.02,35000\n"
        "ETH-USD,0.5,2000\n"
        "TSLA,3,250\n"
        "ETFSP500.WA,10,125,IKZE"
    )

    positions_text = st.sidebar.text_area(
        "Positions (jedna linia = jedna pozycja)",
        value=default_positions,
        height=220,
    )

    st.sidebar.subheader("🏦 Inne oszczędności (PLN)")
    bonds_value = st.sidebar.number_input("Obligacje skarbowe", min_value=0.0, value=0.0, step=1000.0)
    ppk_value = st.sidebar.number_input("PPK – obecna wartość", min_value=0.0, value=0.0, step=1000.0)

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Odswież dane rynkowe"):
        st.cache_data.clear()
        st.rerun()

    # ---------------- PARSOWANIE ----------------
    df = parse_positions(positions_text)
    if df.empty:
        st.info("Dodaj swoje aktywa w panelu po lewej, żeby zobaczyć portfel.")
        return

    # ---------------- POBIERANIE CEN ----------------
    prices, names, trend_m, trend_w, currencies = [], [], [], [], []
    missing = []

    with st.spinner("Pobieram najnowsze ceny rynkowe..."):
        for _, row in df.iterrows():
            price, name, t_m, t_w, curr = get_ticker_data(row["Ticker"])
            if price is None:
                prices.append(None)
                names.append(None)
                trend_m.append(None)
                trend_w.append(None)
                currencies.append(None)
                missing.append(row["Ticker"])
            else:
                prices.append(price)
                names.append(name)
                trend_m.append(t_m)
                trend_w.append(t_w)
                currencies.append(curr)

    df["Price"] = prices
    df["Name"] = names
    df["Trend1m"] = trend_m
    df["Trend1w"] = trend_w
    df["Currency"] = currencies

    usd_pln = get_fx_rate_usd_pln()
    eur_pln = get_fx_rate_eur_pln()

    # ---------------- WARTOŚĆ W PLN / USD ----------------
    def compute_value_pln(row):
        if pd.isna(row["Price"]) or pd.isna(row["Quantity"]):
            return np.nan
        curr = row["Currency"]
        if curr == "PLN":
            return row["Price"] * row["Quantity"]
        elif curr == "USD":
            if usd_pln is None:
                return np.nan
            return row["Price"] * row["Quantity"] * usd_pln
        elif curr == "EUR":
            if eur_pln is None:
                return np.nan
            return row["Price"] * row["Quantity"] * eur_pln
        else:
            return np.nan

    df["Value_PLN"] = df.apply(compute_value_pln, axis=1)

    if usd_pln is not None:
        df["Value_USD"] = df["Value_PLN"] / usd_pln
    else:
        df["Value_USD"] = np.nan

    def compute_purchase_pln(row):
        if pd.isna(row["PurchasePrice"]) or pd.isna(row["Quantity"]):
            return np.nan
        curr = row["Currency"]
        if curr == "PLN":
            return row["PurchasePrice"] * row["Quantity"]
        elif curr == "USD":
            if usd_pln is None:
                return np.nan
            return row["PurchasePrice"] * row["Quantity"] * usd_pln
        elif curr == "EUR":
            if eur_pln is None:
                return np.nan
            return row["PurchasePrice"] * row["Quantity"] * eur_pln
        else:
            return np.nan

    df["PurchaseValue"] = df.apply(compute_purchase_pln, axis=1)
    df["PL_Value"] = df["Value_PLN"] - df["PurchaseValue"]
    df["PL_Percent"] = np.where(
        df["PurchaseValue"] > 0,
        df["PL_Value"] / df["PurchaseValue"] * 100,
        np.nan,
    )

    valid = df.dropna(subset=["Price"])

    # ---------------- KAFELKI GŁÓWNE ----------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_usd = valid["Value_USD"].sum(skipna=True)
        st.metric("Wartość portfela (USD)", f"{total_usd:,.2f}")

    with col2:
        total_pln = valid["Value_PLN"].sum(skipna=True)
        if not np.isnan(total_pln):
            st.metric("Wartość portfela (PLN)", f"{total_pln:,.2f}")
        else:
            total_pln = 0.0
            st.metric("Wartość portfela (PLN)", "—")

    with col3:
        if usd_pln is not None:
            st.metric("FX USD → PLN", f"{usd_pln:,.4f}")
        else:
            st.metric("FX USD → PLN", "brak")
        st.caption(datetime.now().strftime("Aktualizacja: %Y-%m-%d %H:%M:%S"))

    with col4:
        net_pln = total_pln + bonds_value + ppk_value
        st.metric("Total net worth (PLN)", f"{net_pln:,.2f}")

    portfolio_now = net_pln

    st.markdown("---")

    # ---------------- TABS ----------------
    tab_overview, tab_portfolio, tab_savings, tab_plan, tab_progress = st.tabs(
        ["🌍 Overview", "📊 Pozycje rynkowe", "🏦 Inne oszczędności", "🧓 Retirement Planner", "📈 Pension Progress"]
    )

    # ---------------- TAB OVERVIEW ----------------
    with tab_overview:
        st.subheader("Struktura portfela – konta i kategorie")

        if not valid.empty and total_pln > 0:
            overview_df = valid.copy()

            def pie_cat(row):
                if row["Category"] == "CRYPTO":
                    return "Crypto"
                elif row["Category"] == "IKE":
                    return "Stock IKE"
                elif row["Category"] == "IKZE":
                    return "Stock IKZE"
                else:
                    return "Stock"

            overview_df["PieCategory"] = overview_df.apply(pie_cat, axis=1)
            pie_group = (
                overview_df
                .groupby("PieCategory")[["Value_PLN"]]
                .sum()
                .reset_index()
                .sort_values("Value_PLN", ascending=False)
            )

            st.table(
                pie_group.style.format(
                    {"Value_PLN": "{:,.2f}"},
                    na_rep="—",
                )
            )

            fig_pie = px.pie(
                pie_group,
                names="PieCategory",
                values="Value_PLN",
                title="Skład portfela (PLN) – Crypto / Stock / Stock IKE / Stock IKZE",
            )
            fig_pie.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white",
                font_color="#111827",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("---")
            st.subheader("Profil ryzyka portfela")

            stocks_pln = valid.loc[
                valid["Category"].isin(["STOCK/OTHER", "IKE", "IKZE"]),
                "Value_PLN",
            ].sum(skipna=True)

            crypto_pln = valid.loc[
                valid["Category"] == "CRYPTO",
                "Value_PLN",
            ].sum(skipna=True)

            safe_pln = bonds_value + ppk_value

            risk_rows = [
                {"Segment": "Bezpieczne / stabilne (obligacje + PPK)", "Value_PLN": safe_pln},
                {"Segment": "Akcje & ETF-y", "Value_PLN": stocks_pln},
                {"Segment": "Krypto / bardzo ryzykowne", "Value_PLN": crypto_pln},
            ]
            risk_df = pd.DataFrame(risk_rows)

            st.table(
                risk_df.style.format(
                    {"Value_PLN": "{:,.2f}"},
                    na_rep="—",
                )
            )

            fig_risk = px.bar(
                risk_df,
                x="Segment",
                y="Value_PLN",
                title="Podział według poziomu ryzyka (PLN)",
            )
            fig_risk.update_layout(
                xaxis_title="",
                yaxis_title="Wartość (PLN)",
                paper_bgcolor="white",
                plot_bgcolor="white",
                font_color="#111827",
            )
            st.plotly_chart(fig_risk, use_container_width=True)

            total_risk_base = safe_pln + stocks_pln + crypto_pln
            if total_risk_base > 0:
                risky_part = stocks_pln + crypto_pln
                risky_share = risky_part / total_risk_base

                if risky_share >= 0.8:
                    label = "Twój portfel jest **bardzo ryzykowny** – dominują aktywa agresywne."
                elif risky_share >= 0.6:
                    label = "Twój portfel jest **raczej ryzykowny** – przewaga akcji i/lub krypto."
                elif risky_share >= 0.4:
                    label = "Twój portfel jest **dość zbalansowany** między ryzykiem a bezpieczeństwem."
                else:
                    label = "Twój portfel jest **konserwatywny / defensywny** – dużo bezpiecznych aktywów."

                st.markdown(
                    f"{label} (ok. {risky_share*100:,.1f}% wartości w akcjach i krypto)."
                )
            else:
                st.info("Brak danych, aby policzyć profil ryzyka.")

            st.markdown("---")
            st.subheader("Ekspozycja walutowa portfela")

            curr_group = (
                valid.groupby("Currency")[["Value_PLN"]]
                .sum()
                .reset_index()
                .sort_values("Value_PLN", ascending=False)
            )

            st.table(
                curr_group.style.format(
                    {"Value_PLN": "{:,.2f}"},
                    na_rep="—",
                )
            )

            if len(curr_group) > 1:
                fig_curr = px.bar(
                    curr_group,
                    x="Currency",
                    y="Value_PLN",
                    title="Podział portfela według waluty ekspozycji (PLN)",
                )
                fig_curr.update_layout(
                    xaxis_title="Waluta",
                    yaxis_title="Wartość (PLN)",
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    font_color="#111827",
                )
                st.plotly_chart(fig_curr, use_container_width=True)
        else:
            st.info("Brak danych do wyświetlenia struktury portfela.")

    # ---------------- TAB PORTFOLIO ----------------
    with tab_portfolio:
        st.subheader("Pozycje rynkowe")

        def trend_html(val):
            if val == "up":
                return '<span class="trend-up">⬆</span>'
            elif val == "down":
                return '<span class="trend-down">⬇</span>'
            elif val == "flat":
                return '<span class="trend-flat">→</span>'
            else:
                return '<span class="trend-flat">–</span>'

        df_disp = df.copy()
        df_disp["Trend1mHTML"] = df_disp["Trend1m"].apply(trend_html)
        df_disp["Trend1wHTML"] = df_disp["Trend1w"].apply(trend_html)

        def vsp_html(v):
            if pd.isna(v):
                return "—"
            if v >= 0:
                return f'<span class="pl-positive">+{v:,.2f} PLN</span>'
            else:
                return f'<span class="pl-negative">{v:,.2f} PLN</span>'

        df_disp["VSP"] = df_disp["PL_Value"].apply(vsp_html)

        def fmt_qty(x):
            return f"{x:,.4f}" if pd.notna(x) else "—"

        def fmt_money(x):
            return f"{x:,.2f}" if pd.notna(x) else "—"

        table_df = pd.DataFrame({
            "Name": df_disp["Name"],
            "Ticker": df_disp["Ticker"],
            "Quantity": df_disp["Quantity"].apply(fmt_qty),
            "Purchase Price": df_disp["PurchasePrice"].apply(fmt_money),
            "Current Price": df_disp["Price"].apply(fmt_money),
            "Value USD": df_disp["Value_USD"].apply(fmt_money),
            "Value PLN": df_disp["Value_PLN"].apply(fmt_money),
            "Trend 1 Month": df_disp["Trend1mHTML"],
            "Trend 1 Week": df_disp["Trend1wHTML"],
            "VSP": df_disp["VSP"],
        })

        html_table = table_df.to_html(index=False, escape=False)
        st.markdown(f'<div class="portfolio-table">{html_table}</div>', unsafe_allow_html=True)

        if missing:
            st.warning("Brak danych cenowych dla: " + ", ".join(sorted(set(missing))))

    # ---------------- TAB SAVINGS ----------------
    with tab_savings:
        st.subheader("Inne oszczędności (PLN)")

        manual_rows = [
            {"Aktywo": "Obligacje skarbowe", "Value_PLN": bonds_value},
            {"Aktywo": "PPK – obecna wartość", "Value_PLN": ppk_value},
        ]
        df_manual = pd.DataFrame(manual_rows)

        st.table(
            df_manual.style.format(
                {"Value_PLN": "{:,.2f}"},
                na_rep="—",
            )
        )

        st.caption(f"Łączna wartość: {(bonds_value + ppk_value):,.2f} PLN")

        st.markdown("---")
        st.subheader("Prognoza obligacji skarbowych (konserwatywnie)")

        horizons = [5, 10, 15, 20, 25]
        bonds_rows = []
        for h in horizons:
            fv = project_bonds(bonds_value, h)
            bonds_rows.append({"Horyzont (lata)": h, "Prognozowana wartość (PLN)": fv})
        bonds_df = pd.DataFrame(bonds_rows)
        st.table(
            bonds_df.style.format(
                {"Prognozowana wartość (PLN)": "{:,.2f}"},
                na_rep="—",
            )
        )
        st.caption(
            f"Założona roczna stopa zwrotu obligacji: {BONDS_RATE_ANNUAL*100:.1f}% (konserwatywnie, przed podatkiem)."
        )

        st.markdown("---")
        st.subheader("Prognoza PPK")

        salary_brutto = st.number_input(
            "Twoje wynagrodzenie brutto (PLN/miesiąc) – dla prognozy PPK:",
            min_value=0.0,
            value=0.0,
            step=500.0,
            key="savings_salary_brutto",
        )

        ppk_rows = []
        for h in horizons:
            fv_ppk = project_ppk_custom(ppk_value, salary_brutto, h)
            ppk_rows.append({"Horyzont (lata)": h, "Prognozowana wartość PPK (PLN)": fv_ppk})
        ppk_df = pd.DataFrame(ppk_rows)
        st.table(
            ppk_df.style.format(
                {"Prognozowana wartość PPK (PLN)": "{:,.2f}"},
                na_rep="—",
            )
        )
        st.caption(
            "Przyjęto: Twój wkład + pracodawcy = 3% wynagrodzenia brutto miesięcznie, "
            f"oraz dopłatę państwa {PPK_STATE_ANNUAL:.0f} PLN/rok, roczna stopa zwrotu {PPK_RATE_ANNUAL*100:.1f}%."
        )

    # ---------------- TAB RETIREMENT PLANNER ----------------
    with tab_plan:
        st.subheader("Planowanie emerytury – model do 90. roku życia")

        st.markdown(
            """
Tutaj obliczamy, ile kapitału potrzebujesz, aby przejść na **spokojną emeryturę**,
z założeniem, że środki mają wystarczyć mniej więcej do 90. roku życia.
"""
        )

        spend_option = st.radio(
            "Jak zmienią się Twoje wydatki na emeryturze?",
            [
                "Będę wydawać mniej (–30%)",
                "Będę wydawać tyle samo",
                "Będę wydawać więcej (+30%)",
            ],
            key="rp_spend_option",
        )

        base_monthly = st.number_input(
            "Twoje miesięczne wydatki dzisiaj (PLN):",
            min_value=0.0,
            value=8000.0,
            step=500.0,
            key="rp_base_monthly",
        )

        if spend_option == "Będę wydawać mniej (–30%)":
            monthly_needs_today = base_monthly * 0.7
        elif spend_option == "Będę wydawać więcej (+30%)":
            monthly_needs_today = base_monthly * 1.3
        else:
            monthly_needs_today = base_monthly

        st.write(f"**Szacowane potrzebne miesięczne wydatki (dzisiaj): {monthly_needs_today:,.2f} PLN**")

        age_now = st.number_input(
            "Twój obecny wiek:",
            min_value=18,
            max_value=80,
            value=40,
            key="rp_age_now",
        )
        age_retire = st.number_input(
            "Wiek przejścia na emeryturę:",
            min_value=50,
            max_value=80,
            value=65,
            key="rp_age_retire",
        )
        age_end = 90
        years_to_retirement = max(int(age_retire) - int(age_now), 0)
        years_of_retirement = max(age_end - int(age_retire), 0)

        inflation_pct = st.slider(
            "Przewidywana średnia inflacja roczna (%):",
            0.0,
            10.0,
            4.0,
            step=0.5,
            key="rp_inflation_pct",
        )
        inflation = inflation_pct / 100.0
        st.caption(
            "Inflacja to średni wzrost cen rocznie. Jeśli nie wiesz, co wybrać, 4% to ostrożne, realistyczne założenie "
            "dla długiego okresu w Polsce."
        )

        real_return_pct = st.slider(
            "Realna stopa zwrotu w czasie emerytury (% ponad inflację):",
            0.0,
            5.0,
            2.0,
            step=0.5,
            key="rp_real_return_pct",
        )
        real_return = real_return_pct / 100.0
        st.caption(
            "Realna stopa zwrotu to zysk z inwestycji **po uwzględnieniu inflacji**. "
            "Konserwatywnie przyjmuje się 1–3% dla spokojnego portfela z obligacjami i ETF-ami."
        )

        st.markdown("---")
        st.subheader("Założenia dotyczące emerytury z ZUS")

        zus_mode = st.radio(
            "Jak chcesz uwzględnić ZUS w tym modelu?",
            [
                "Pesymistycznie: ZUS ≈ 25% mojego obecnego wynagrodzenia netto",
                "Nie uwzględniaj ZUS (załóż 0 PLN)",
            ],
            key="rp_zus_mode",
        )

        salary_net = st.number_input(
            "Twoje obecne wynagrodzenie netto (PLN/miesiąc):",
            min_value=0.0,
            value=0.0,
            step=500.0,
            key="rp_salary_net",
        )

        if zus_mode.startswith("Pesymistycznie") and salary_net > 0:
            zus_monthly_today = salary_net * 0.25
            st.caption(
                f"Na potrzeby obliczeń przyjmujemy, że Twoja przyszła emerytura z ZUS (w dzisiejszych pieniądzach) "
                f"wyniesie ok. 25% wynagrodzenia netto, czyli **{zus_monthly_today:,.2f} PLN/miesiąc**."
            )
        else:
            zus_monthly_today = 0.0
            st.caption(
                "W tym modelu przyjmujemy, że nie będziesz otrzymywać realnej emerytury z ZUS (0 PLN). "
                "To bardzo konserwatywne założenie."
            )

        (
            required_capital,
            future_monthly,
            future_yearly,
            yearly_gap_after_zus,
        ) = required_capital_finite_horizon(
            monthly_needs_today,
            years_to_retirement,
            years_of_retirement,
            inflation,
            zus_monthly_today,
            real_return,
        )

        st.session_state["rp_required_capital"] = float(required_capital)
        st.session_state["rp_years_to_retirement"] = int(years_to_retirement)
        st.session_state["rp_years_of_retirement"] = int(years_of_retirement)
        st.session_state["rp_age_now_val"] = int(age_now)
        st.session_state["rp_age_retire_val"] = int(age_retire)

        st.markdown("### Wyniki – model do 90. roku życia")

        st.write(f"Przyszłe miesięczne koszty (po inflacji): **{future_monthly:,.2f} PLN**")
        st.write(f"Przyszłe roczne koszty (po inflacji): **{future_yearly:,.2f} PLN**")
        st.write(f"Roczne koszty po uwzględnieniu ZUS: **{yearly_gap_after_zus:,.2f} PLN**")

        if yearly_gap_after_zus == 0:
            st.info(
                "Przy tych założeniach prognozowana emerytura z ZUS w pełni pokrywa Twoje koszty życia. "
                "W tym modelu nie potrzebujesz dodatkowego kapitału, dlatego wymagany kapitał wynosi 0 PLN."
            )

        st.write(
            f"**Wymagany kapitał emerytalny na starcie emerytury:** **{required_capital:,.2f} PLN** "
            f"(okres emerytury: {years_of_retirement} lat)."
        )

        portfolio_market_pln = total_pln
        st.write(
            f"**Twój obecny majątek inwestycyjny (portfel + obligacje + PPK): {portfolio_now:,.2f} PLN**"
        )
        st.caption(
            f"- Portfel rynkowy (akcje/ETF/krypto): {portfolio_market_pln:,.2f} PLN  \n"
            f"- Obligacje skarbowe: {bonds_value:,.2f} PLN  \n"
            f"- PPK: {ppk_value:,.2f} PLN"
        )

        gap = required_capital - portfolio_now
        if required_capital == 0 and yearly_gap_after_zus == 0:
            st.success(
                "Według tych założeń Twoja emerytura z ZUS sama pokrywa koszty życia. "
                "Twoje inwestycje są nadwyżką / dodatkową poduszką bezpieczeństwa. 💚"
            )
        else:
            if gap > 0:
                st.warning(f"Brakuje Ci ok. **{gap:,.2f} PLN** do założonego celu (w tym modelu).")
            else:
                st.success(
                    "Na podstawie tych założeń masz już wystarczający kapitał (lub nadwyżkę) "
                    "względem wymaganego poziomu. 💚"
                )

    # ---------------- TAB PENSION PROGRESS ----------------
    with tab_progress:
        st.subheader("📈 Pension Progress – gdzie jesteś na drodze do celu?")

        required_capital = float(st.session_state.get("rp_required_capital", 0.0))
        years_to_retirement = int(st.session_state.get("rp_years_to_retirement", 0))
        years_of_retirement = int(st.session_state.get("rp_years_of_retirement", 0))
        age_now_state = int(st.session_state.get("rp_age_now_val", 40))
        age_retire_state = int(st.session_state.get("rp_age_retire_val", age_now_state + years_to_retirement))

        if years_to_retirement <= 0:
            st.info(
                "Najpierw ustaw swoje założenia w zakładce **🧓 Retirement Planner** – "
                "wydatki, wiek emerytury, inflację i ZUS."
            )
        else:
            if required_capital > 0:
                progress_ratio = portfolio_now / required_capital
            else:
                progress_ratio = 1.0

            if required_capital == 0:
                health_label = "💚 Według tego modelu nie potrzebujesz dodatkowego kapitału."
                health_text = (
                    "Prognozowana emerytura z ZUS pokrywa w całości założone koszty życia. "
                    "Twoje inwestycje są nadwyżką i zwiększają komfort oraz bezpieczeństwo."
                )
            else:
                if progress_ratio >= 0.8:
                    health_label = "💚 Jesteś bardzo blisko swojego celu emerytalnego."
                    health_text = (
                        f"Masz już około **{progress_ratio*100:,.1f}%** wymaganego kapitału. "
                        "Jesteś w strefie zielonej – teraz chodzi raczej o dopracowanie strategii niż o pogoń za wynikiem."
                    )
                elif progress_ratio >= 0.4:
                    health_label = "💛 Jesteś w połowie drogi."
                    health_text = (
                        f"Masz około **{progress_ratio*100:,.1f}%** wymaganego kapitału. "
                        "Przy konsekwentnym oszczędzaniu możesz spokojnie domknąć cel."
                    )
                else:
                    health_label = "❤️ Jesteś na początku drogi."
                    health_text = (
                        f"Masz około **{progress_ratio*100:,.1f}%** wymaganego kapitału. "
                        "To dobry moment, żeby zbudować stałą, automatyczną ścieżkę oszczędzania."
                    )

            st.markdown(f"### {health_label}")
            st.write(health_text)

            st.markdown("#### Twój postęp względem celu")

            progress_value = min(max(progress_ratio, 0.0), 1.0)
            st.progress(progress_value)

            st.write(
                f"Aktualny majątek (portfel + obligacje + PPK): **{portfolio_now:,.2f} PLN**"
            )
            if required_capital > 0:
                st.write(
                    f"Wymagany kapitał emerytalny (z zakładki Retirement Planner): **{required_capital:,.2f} PLN**"
                )
            else:
                st.write(
                    "Wymagany kapitał emerytalny w tym modelu wynosi **0 PLN**, "
                    "ponieważ ZUS pokrywa w całości założone koszty życia."
                )

            st.markdown("---")
            st.markdown("#### Prognoza kapitału do emerytury")

            base_return = 0.025
            recommended_monthly = required_monthly_saving(
                required_capital,
                portfolio_now,
                years_to_retirement,
                base_return,
            )

            if required_capital > 0:
                if recommended_monthly > 0:
                    st.write(
                        f"Aby osiągnąć cel **{required_capital:,.0f} PLN** w scenariuszu bazowym "
                        f"(2.5% realnej stopy zwrotu) w ciągu {years_to_retirement} lat, "
                        f"powinnaś odkładać około **{recommended_monthly:,.0f} PLN/miesiąc**."
                    )
                else:
                    st.write(
                        "Przy obecnym poziomie majątku i czasie do emerytury "
                        "nie potrzebujesz dodatkowych regularnych wpłat, aby osiągnąć cel w scenariuszu bazowym."
                    )
            else:
                st.write(
                    "Ponieważ w tym modelu ZUS pokrywa Twoje koszty życia, "
                    "każda dodatkowa wpłata buduje nadwyżkę i komfort emerytalny."
                )

            default_monthly = recommended_monthly if recommended_monthly > 0 else 0.0

            monthly_saving = st.number_input(
                "Planowana miesięczna kwota oszczędzania do emerytury (PLN):",
                min_value=0.0,
                value=float(round(default_monthly)) if default_monthly > 0 else 0.0,
                step=200.0,
                key="pp_monthly_saving",
            )

            st.caption(
                "Możesz tu wpisać kwotę, którą realnie jesteś w stanie odkładać co miesiąc, "
                "a poniższy wykres pokaże, dokąd może Cię to doprowadzić w różnych scenariuszach rynkowych."
            )

            ages = [age_now_state + i for i in range(1, years_to_retirement + 1)]

            scenarios = [
                ("Pesymistyczny (1% realnie)", 0.01),
                ("Bazowy (2.5% realnie)", 0.025),
                ("Optymistyczny (4% realnie)", 0.04),
            ]

            rows = []
            final_base = None

            for name, r in scenarios:
                values = simulate_future_wealth(portfolio_now, monthly_saving, years_to_retirement, r)
                for age, val in zip(ages, values):
                    rows.append({"Age": age, "Scenario": name, "Value_PLN": val})
                if "Bazowy" in name and values:
                    final_base = values[-1]

            if rows:
                proj_df = pd.DataFrame(rows)

                st.markdown(
                    """
**Scenariusze na wykresie:**
- *Pesymistyczny (1% realnie)* – rynki zachowują się słabo, zyski z inwestycji są niewielkie.  
- *Bazowy (2.5% realnie)* – realistyczny, długoterminowy wynik spokojnego portfela (obligacje + ETF-y).  
- *Optymistyczny (4% realnie)* – dobre warunki rynkowe, wyższe realne zyski z inwestycji.

Realna stopa zwrotu oznacza wynik **po uwzględnieniu inflacji**.
"""
                )

                fig_proj = px.line(
                    proj_df,
                    x="Age",
                    y="Value_PLN",
                    color="Scenario",
                    title="Prognozowany kapitał do wieku emerytalnego (realnie, w dzisiejszych PLN)",
                )
                if required_capital > 0:
                    fig_proj.add_hline(
                        y=required_capital,
                        line_dash="dash",
                        annotation_text="Wymagany kapitał",
                        annotation_position="top left",
                    )
                fig_proj.update_layout(
                    xaxis_title="Wiek",
                    yaxis_title="Kapitał (PLN)",
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    font_color="#111827",
                )
                st.plotly_chart(fig_proj, use_container_width=True)

                if final_base is not None and required_capital > 0:
                    share = final_base / required_capital
                    if share >= 1:
                        st.success(
                            f"Przy wpłacie **{monthly_saving:,.0f} PLN/miesiąc** w scenariuszu bazowym "
                            f"osiągniesz około **{final_base:,.0f} PLN**, czyli **{share*100:,.1f}%** wymaganego kapitału."
                        )
                    else:
                        st.warning(
                            f"Przy wpłacie **{monthly_saving:,.0f} PLN/miesiąc** w scenariuszu bazowym "
                            f"osiągniesz około **{final_base:,.0f} PLN**, czyli **{share*100:,.1f}%** wymaganego kapitału."
                        )
                elif final_base is not None and required_capital == 0:
                    st.info(
                        f"Przy wpłacie **{monthly_saving:,.0f} PLN/miesiąc** w scenariuszu bazowym "
                        f"zbudujesz do emerytury kapitał około **{final_base:,.0f} PLN** "
                        "– będzie to nadwyżka ponad koszty pokrywane przez ZUS."
                    )
            else:
                st.info("Brak danych do narysowania prognozy kapitału.")


if __name__ == "__main__":
    main()
# coding: utf-8
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

# ------------------------------------------------------
# KONFIGURACJA HASŁA
# ------------------------------------------------------
PASSWORD = "mojehaslo"   # ZMIEŃ NA SWOJE HASŁO


# ------------------------------------------------------
# ZAŁOŻENIA DO PROGNOZ
# ------------------------------------------------------
BONDS_RATE_ANNUAL = 0.03
PPK_RATE_ANNUAL = 0.04

PPK_EMP_RATE = 0.015
PPK_ER_RATE = 0.015
PPK_STATE_ANNUAL = 240.0


# ------------------------------------------------------
# STYLIZACJA (CSS)
# ------------------------------------------------------
def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --primary-color: #2563eb;      /* niebieski */
            --accent-color:  #f97316;      /* lekko pomaranczowy */
            --bg-main:       #f3f4f6;      /* jasnoszary */
            --bg-card:       #ffffff;
            --border-soft:   #e5e7eb;
            --text-main:     #111827;
            --text-muted:    #6b7280;
        }

        html, body {
            background: var(--bg-main);
        }

        /* Globalne wymuszenie jasnego tekstu */
        body, body * {
            color: var(--text-main) !important;
            box-shadow: none;
        }

        /* Glowna kolumna - centrowanie i max szerokosc */
        [data-testid="stAppViewContainer"] > .main .block-container {
            max-width: 1000px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            margin: 0 auto;
        }

        [data-testid="stAppViewContainer"] {
            background: var(--bg-main);
        }

        /* Sidebar - jasny, bez czerni */
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--border-soft);
        }

        [data-testid="stSidebar"] * {
            color: var(--text-main) !important;
        }

        /* Pola input / textarea / select - jasne tlo, ciemny tekst */
        input, textarea, select {
            background: #f9fafb !important;
            color: var(--text-main) !important;
            border: 1px solid var(--border-soft) !important;
        }

        /* Przyciski (w tym "Odswiez") */
        button, [data-testid="stSidebar"] button {
            background: var(--primary-color) !important;
            color: #ffffff !important;
            border-radius: 999px !important;
            border: none !important;
        }
        button:hover, [data-testid="stSidebar"] button:hover {
            filter: brightness(0.95);
        }

        /* Naglowek aplikacji */
        .app-title {
            font-weight: 700;
            letter-spacing: 0.02em;
            margin-bottom: 0.3rem;
        }

        .app-subtitle {
            text-align: center;
            color: var(--text-muted) !important;
            max-width: 620px;
            margin: 0 auto 1.5rem auto;
            font-size: 0.95rem;
        }

        /* Karty metric - hero sekcja */
        div[data-testid="metric-container"] {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border-soft) !important;
            padding: 20px 18px !important;
            border-radius: 16px !important;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06) !important;
        }

        div[data-testid="stMetricLabel"] {
            color: #4b5563 !important;
            font-size: 0.95rem !important;
            font-weight: 500 !important;
        }

        div[data-testid="stMetricValue"] {
            font-size: 2.0rem !important;
            font-weight: 700 !important;
            color: #111827 !important;
        }

        /* 3. metric (FX) - mniejsza liczba */
        div[data-testid="metric-container"]:nth-of-type(3) div[data-testid="stMetricValue"] {
            font-size: 1.4rem !important;
        }

        /* Tabele - pandas HTML (overview & savings) */
        table.dataframe {
            border-collapse: collapse;
            width: 100%;
            background: var(--bg-card);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 10px rgba(15, 23, 42, 0.03);
        }
        table.dataframe th, table.dataframe td {
            border: 1px solid #e5e7eb;
            padding: 0.45rem 0.65rem;
            font-size: 0.9rem;
            color: var(--text-main) !important;
        }
        table.dataframe th {
            background-color: #f9fafb;
            font-weight: 600;
        }

        /* Tabela w zakladce Pozycje rynkowe */
        .portfolio-table {
            max-width: 1000px;
            margin: 0 auto;
        }
        .portfolio-table table {
            border-collapse: collapse;
            width: 100%;
            background: var(--bg-card);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 10px rgba(15, 23, 42, 0.03);
        }
        .portfolio-table th, .portfolio-table td {
            border: 1px solid #e5e7eb;
            padding: 0.45rem 0.65rem;
            font-size: 0.9rem;
            text-align: right;
            color: var(--text-main) !important;
        }
        .portfolio-table th:nth-child(1),
        .portfolio-table td:nth-child(1),
        .portfolio-table th:nth-child(2),
        .portfolio-table td:nth-child(2) {
            text-align: left;
        }
        .portfolio-table th {
            background-color: #f9fafb;
            font-weight: 600;
        }

        /* Ikony trendu i P/L */
        .trend-up { color: #16a34a !important; font-weight: 600; }
        .trend-down { color: #dc2626 !important; font-weight: 600; }
        .trend-flat { color: #6b7280 !important; }

        .pl-positive { color: #16a34a !important; font-weight: 600; }
        .pl-negative { color: #dc2626 !important; font-weight: 600; }

        /* Zakladki - zawsze widoczne */
        button[role="tab"] {
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            padding-top: 0.4rem !important;
            padding-bottom: 0.4rem !important;
            color: var(--text-muted) !important;
            border-bottom: 2px solid transparent !important;
            background: transparent !important;
        }
        button[role="tab"][aria-selected="true"] {
            color: var(--text-main) !important;
            border-bottom: 2px solid var(--accent-color) !important;
        }

        /* Plotly - jasne tlo, zadnej czerni */
        .stPlotlyChart {
            background-color: var(--bg-card) !important;
            padding: 1rem !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06) !important;
        }

        /* Alerty (info, warning, success) - jasne tlo, ciemny tekst */
        .stAlert {
            background-color: #fefce8 !important;  /* pastelowy zolty */
            color: #92400e !important;
            border-radius: 12px !important;
            border: 1px solid #facc15 !important;
        }

        /* Usuniecie defaultowego menu/footera Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: visible;}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------
# FUNKCJE POBIERANIA DANYCH
# ------------------------------------------------------
def parse_positions(text: str) -> pd.DataFrame:
    """
    Format linii:
    TICKER,ILOŚĆ[,CENA_ZAKUPU][,KONTO]
    """
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            st.warning(f"Niepoprawna linia: {line}")
            continue

        ticker = parts[0].upper()

        qty_str = parts[1].replace(",", ".")
        try:
            qty = float(qty_str)
        except ValueError:
            st.warning(f"Nie mogę odczytać ilości z: {line}")
            continue

        purchase_price = None
        if len(parts) >= 3 and parts[2] != "":
            purchase_str = parts[2].replace(",", ".")
            try:
                purchase_price = float(purchase_str)
            except ValueError:
                purchase_price = None

        if len(parts) >= 4:
            acc_raw = parts[3].upper()
            if acc_raw.startswith("IKE"):
                account = "IKE"
            elif acc_raw.startswith("IKZE"):
                account = "IKZE"
            else:
                account = "STANDARD"
        else:
            account = "STANDARD"

        rows.append(
            {
                "Ticker": ticker,
                "Quantity": qty,
                "PurchasePrice": purchase_price,
                "Account": account,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["Ticker", "Quantity", "PurchasePrice", "Account"])

    df = pd.DataFrame(rows)

    def categorize(row):
        if row["Account"] in ("IKE", "IKZE"):
            return row["Account"]
        if row["Ticker"].endswith("-USD"):
            return "CRYPTO"
        return "STOCK/OTHER"

    df["Category"] = df.apply(categorize, axis=1)
    return df


@st.cache_data(ttl=300)
def get_ticker_data(ticker: str):
    """
    Zwraca:
    - price
    - name
    - trend_m (up/down/flat/None)
    - trend_w (up/down/flat/None)
    - currency (USD/PLN/EUR/...)
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

        if not hist_w.empty:
            first_w = float(hist_w["Close"].iloc[0])
            if price > first_w:
                trend_w = "up"
            elif price < first_w:
                trend_w = "down"
            else:
                trend_w = "flat"
        else:
            trend_w = None

        info = getattr(t, "info", {}) or {}
        name = info.get("longName") or info.get("shortName") or ticker
        currency = info.get("currency") or "USD"

        return price, name, trend_m, trend_w, currency

    except Exception:
        return None, None, None, None, None


@st.cache_data(ttl=300)
def get_fx_rate_usd_pln():
    try:
        fx = yf.Ticker("USDPLN=X")
        hist = fx.history(period="1d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_fx_rate_eur_pln():
    try:
        fx = yf.Ticker("EURPLN=X")
        hist = fx.history(period="1d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None


# ------------------------------------------------------
# FUNKCJE – PROJEKCJE
# ------------------------------------------------------
def project_bonds(value, years):
    return value * ((1 + BONDS_RATE_ANNUAL) ** years)


def project_ppk_custom(current_value_pln, salary_brutto, years):
    """
    Projekcja PPK:
    - value = obecna wartość
    - salary_brutto = Twoje wynagrodzenie brutto miesięcznie
    """
    months = years * 12
    monthly_rate = (1 + PPK_RATE_ANNUAL) ** (1 / 12) - 1
    monthly_contrib = salary_brutto * (PPK_EMP_RATE + PPK_ER_RATE) + PPK_STATE_ANNUAL / 12.0

    total = current_value_pln
    for _ in range(months):
        total = total * (1 + monthly_rate) + monthly_contrib
    return total


# ------------------------------------------------------
# FUNKCJA – RETIREMENT (MODEL „DO 90 LAT”)
# ------------------------------------------------------
def required_capital_finite_horizon(
    monthly_needs_today: float,
    years_to_retirement: int,
    years_of_retirement: int,
    inflation: float,
    zus_monthly_today: float,
    real_return: float,
):
    """
    Zwraca:
    - required_capital: wymagany kapitał na starcie emerytury
    - future_monthly_needs: przyszłe miesięczne koszty (po inflacji)
    - future_yearly_needs: roczne koszty (po inflacji, przed ZUS)
    - yearly_gap_after_zus: roczne koszty do pokrycia z oszczędności
    """
    growth_factor = (1 + inflation) ** years_to_retirement

    future_monthly_needs = monthly_needs_today * growth_factor
    future_yearly_needs = future_monthly_needs * 12

    zus_annual_today = zus_monthly_today * 12.0
    zus_annual_future = zus_annual_today * growth_factor

    yearly_gap_after_zus = max(future_yearly_needs - zus_annual_future, 0.0)

    if years_of_retirement <= 0 or yearly_gap_after_zus == 0:
        return 0.0, future_monthly_needs, future_yearly_needs, yearly_gap_after_zus

    if real_return > 0:
        factor = (1 - (1 + real_return) ** (-years_of_retirement)) / real_return
        required_capital = yearly_gap_after_zus * factor
    else:
        required_capital = yearly_gap_after_zus * years_of_retirement

    return required_capital, future_monthly_needs, future_yearly_needs, yearly_gap_after_zus


# ------------------------------------------------------
# FUNKCJA – PROGNOZA KAPITAŁU (PENSION PROGRESS)
# ------------------------------------------------------
def simulate_future_wealth(initial, monthly_saving, years_to_retirement, annual_return):
    """
    Symuluje wzrost kapitału z miesięcznymi wpłatami.
    Zwraca listę wartości kapitału na koniec każdego roku.
    """
    value = initial
    if years_to_retirement <= 0:
        return []

    monthly_rate = (1 + annual_return) ** (1 / 12) - 1
    values = []
    for _ in range(years_to_retirement):
        for _m in range(12):
            value = (value + monthly_saving) * (1 + monthly_rate)
        values.append(value)
    return values


def required_monthly_saving(target, current, years_to_retirement, annual_return):
    """
    Liczy, ile trzeba odkładać miesięcznie, aby osiągnąć target
    przy danej stopie zwrotu (annual_return) i current kapitale startowym.
    """
    if years_to_retirement <= 0:
        return 0.0

    if target <= current:
        return 0.0

    months = years_to_retirement * 12
    monthly_rate = (1 + annual_return) ** (1 / 12) - 1

    if monthly_rate == 0:
        return (target - current) / months

    future_current = current * ((1 + monthly_rate) ** months)
    numerator = (target - future_current) * monthly_rate
    denominator = ((1 + monthly_rate) ** months - 1)

    if denominator <= 0:
        return 0.0

    pmt = numerator / denominator
    return max(pmt, 0.0)


# ------------------------------------------------------
# GŁÓWNA FUNKCJA APLIKACJI
# ------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Local Portfolio Tracker & Pension Plan",
        page_icon="💰",
        layout="wide",
    )
    inject_css()

    # GŁÓWNY NAGŁÓWEK
    st.markdown('<h1 class="app-title">💰 Local Portfolio Tracker & Pension Plan</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="app-subtitle">Twoje portfolio, Twoje bezpieczeństwo. Dane rynkowe + planowanie finansowe.</p>',
        unsafe_allow_html=True,
    )

    # ---------------- SIDEBAR – dostęp ----------------
    st.sidebar.header("🔒 Dostęp")
    pw = st.sidebar.text_input("Hasło dostępu", type="password", key="password_input")

    if pw != PASSWORD:
        st.warning("Podaj poprawne hasło, aby zobaczyć swój portfel.")
        st.stop()

    st.sidebar.markdown("---")

    st.sidebar.header("🧾 Twoje pozycje")

    st.sidebar.markdown(
        """
Format wprowadzania pozycji:

`TICKER,ILOŚĆ[,CENA_ZAKUPU][,KONTO]`

Przykłady:
- `BTC-USD,0.02,35000`
- `TSLA,3,250`
- `ETFSP500.WA,10,125,IKZE`
- `ETFABC.DE,7,90,IKE`
"""
    )

    default_positions = (
        "BTC-USD,0.02,35000\n"
        "ETH-USD,0.5,2000\n"
        "TSLA,3,250\n"
        "ETFSP500.WA,10,125,IKZE"
    )

    positions_text = st.sidebar.text_area(
        "Positions (jedna linia = jedna pozycja)",
        value=default_positions,
        height=220,
    )

    st.sidebar.subheader("🏦 Inne oszczędności (PLN)")
    bonds_value = st.sidebar.number_input("Obligacje skarbowe", min_value=0.0, value=0.0, step=1000.0)
    ppk_value = st.sidebar.number_input("PPK – obecna wartość", min_value=0.0, value=0.0, step=1000.0)

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Odswież dane rynkowe"):
        st.cache_data.clear()
        st.rerun()

    # ---------------- PARSOWANIE ----------------
    df = parse_positions(positions_text)
    if df.empty:
        st.info("Dodaj swoje aktywa w panelu po lewej, żeby zobaczyć portfel.")
        return

    # ---------------- POBIERANIE CEN ----------------
    prices, names, trend_m, trend_w, currencies = [], [], [], [], []
    missing = []

    with st.spinner("Pobieram najnowsze ceny rynkowe..."):
        for _, row in df.iterrows():
            price, name, t_m, t_w, curr = get_ticker_data(row["Ticker"])
            if price is None:
                prices.append(None)
                names.append(None)
                trend_m.append(None)
                trend_w.append(None)
                currencies.append(None)
                missing.append(row["Ticker"])
            else:
                prices.append(price)
                names.append(name)
                trend_m.append(t_m)
                trend_w.append(t_w)
                currencies.append(curr)

    df["Price"] = prices
    df["Name"] = names
    df["Trend1m"] = trend_m
    df["Trend1w"] = trend_w
    df["Currency"] = currencies

    usd_pln = get_fx_rate_usd_pln()
    eur_pln = get_fx_rate_eur_pln()

    # ---------------- WARTOŚĆ W PLN / USD ----------------
    def compute_value_pln(row):
        if pd.isna(row["Price"]) or pd.isna(row["Quantity"]):
            return np.nan
        curr = row["Currency"]
        if curr == "PLN":
            return row["Price"] * row["Quantity"]
        elif curr == "USD":
            if usd_pln is None:
                return np.nan
            return row["Price"] * row["Quantity"] * usd_pln
        elif curr == "EUR":
            if eur_pln is None:
                return np.nan
            return row["Price"] * row["Quantity"] * eur_pln
        else:
            return np.nan

    df["Value_PLN"] = df.apply(compute_value_pln, axis=1)

    if usd_pln is not None:
        df["Value_USD"] = df["Value_PLN"] / usd_pln
    else:
        df["Value_USD"] = np.nan

    def compute_purchase_pln(row):
        if pd.isna(row["PurchasePrice"]) or pd.isna(row["Quantity"]):
            return np.nan
        curr = row["Currency"]
        if curr == "PLN":
            return row["PurchasePrice"] * row["Quantity"]
        elif curr == "USD":
            if usd_pln is None:
                return np.nan
            return row["PurchasePrice"] * row["Quantity"] * usd_pln
        elif curr == "EUR":
            if eur_pln is None:
                return np.nan
            return row["PurchasePrice"] * row["Quantity"] * eur_pln
        else:
            return np.nan

    df["PurchaseValue"] = df.apply(compute_purchase_pln, axis=1)
    df["PL_Value"] = df["Value_PLN"] - df["PurchaseValue"]
    df["PL_Percent"] = np.where(
        df["PurchaseValue"] > 0,
        df["PL_Value"] / df["PurchaseValue"] * 100,
        np.nan,
    )

    valid = df.dropna(subset=["Price"])

    # ---------------- KAFELKI GŁÓWNE ----------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_usd = valid["Value_USD"].sum(skipna=True)
        st.metric("Wartość portfela (USD)", f"{total_usd:,.2f}")

    with col2:
        total_pln = valid["Value_PLN"].sum(skipna=True)
        if not np.isnan(total_pln):
            st.metric("Wartość portfela (PLN)", f"{total_pln:,.2f}")
        else:
            total_pln = 0.0
            st.metric("Wartość portfela (PLN)", "—")

    with col3:
        if usd_pln is not None:
            st.metric("FX USD → PLN", f"{usd_pln:,.4f}")
        else:
            st.metric("FX USD → PLN", "brak")
        st.caption(datetime.now().strftime("Aktualizacja: %Y-%m-%d %H:%M:%S"))

    with col4:
        net_pln = total_pln + bonds_value + ppk_value
        st.metric("Total net worth (PLN)", f"{net_pln:,.2f}")

    portfolio_now = net_pln

    st.markdown("---")

    # ---------------- TABS ----------------
    tab_overview, tab_portfolio, tab_savings, tab_plan, tab_progress = st.tabs(
        ["🌍 Overview", "📊 Pozycje rynkowe", "🏦 Inne oszczędności", "🧓 Retirement Planner", "📈 Pension Progress"]
    )

    # ---------------- TAB OVERVIEW ----------------
    with tab_overview:
        st.subheader("Struktura portfela – konta i kategorie")

        if not valid.empty and total_pln > 0:
            overview_df = valid.copy()

            def pie_cat(row):
                if row["Category"] == "CRYPTO":
                    return "Crypto"
                elif row["Category"] == "IKE":
                    return "Stock IKE"
                elif row["Category"] == "IKZE":
                    return "Stock IKZE"
                else:
                    return "Stock"

            overview_df["PieCategory"] = overview_df.apply(pie_cat, axis=1)
            pie_group = (
                overview_df
                .groupby("PieCategory")[["Value_PLN"]]
                .sum()
                .reset_index()
                .sort_values("Value_PLN", ascending=False)
            )

            st.table(
                pie_group.style.format(
                    {"Value_PLN": "{:,.2f}"},
                    na_rep="—",
                )
            )

            fig_pie = px.pie(
                pie_group,
                names="PieCategory",
                values="Value_PLN",
                title="Skład portfela (PLN) – Crypto / Stock / Stock IKE / Stock IKZE",
            )
            fig_pie.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white",
                font_color="#111827",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("---")
            st.subheader("Profil ryzyka portfela")

            stocks_pln = valid.loc[
                valid["Category"].isin(["STOCK/OTHER", "IKE", "IKZE"]),
                "Value_PLN",
            ].sum(skipna=True)

            crypto_pln = valid.loc[
                valid["Category"] == "CRYPTO",
                "Value_PLN",
            ].sum(skipna=True)

            safe_pln = bonds_value + ppk_value

            risk_rows = [
                {"Segment": "Bezpieczne / stabilne (obligacje + PPK)", "Value_PLN": safe_pln},
                {"Segment": "Akcje & ETF-y", "Value_PLN": stocks_pln},
                {"Segment": "Krypto / bardzo ryzykowne", "Value_PLN": crypto_pln},
            ]
            risk_df = pd.DataFrame(risk_rows)

            st.table(
                risk_df.style.format(
                    {"Value_PLN": "{:,.2f}"},
                    na_rep="—",
                )
            )

            fig_risk = px.bar(
                risk_df,
                x="Segment",
                y="Value_PLN",
                title="Podział według poziomu ryzyka (PLN)",
            )
            fig_risk.update_layout(
                xaxis_title="",
                yaxis_title="Wartość (PLN)",
                paper_bgcolor="white",
                plot_bgcolor="white",
                font_color="#111827",
            )
            st.plotly_chart(fig_risk, use_container_width=True)

            total_risk_base = safe_pln + stocks_pln + crypto_pln
            if total_risk_base > 0:
                risky_part = stocks_pln + crypto_pln
                risky_share = risky_part / total_risk_base

                if risky_share >= 0.8:
                    label = "Twój portfel jest **bardzo ryzykowny** – dominują aktywa agresywne."
                elif risky_share >= 0.6:
                    label = "Twój portfel jest **raczej ryzykowny** – przewaga akcji i/lub krypto."
                elif risky_share >= 0.4:
                    label = "Twój portfel jest **dość zbalansowany** między ryzykiem a bezpieczeństwem."
                else:
                    label = "Twój portfel jest **konserwatywny / defensywny** – dużo bezpiecznych aktywów."

                st.markdown(
                    f"{label} (ok. {risky_share*100:,.1f}% wartości w akcjach i krypto)."
                )
            else:
                st.info("Brak danych, aby policzyć profil ryzyka.")

            st.markdown("---")
            st.subheader("Ekspozycja walutowa portfela")

            curr_group = (
                valid.groupby("Currency")[["Value_PLN"]]
                .sum()
                .reset_index()
                .sort_values("Value_PLN", ascending=False)
            )

            st.table(
                curr_group.style.format(
                    {"Value_PLN": "{:,.2f}"},
                    na_rep="—",
                )
            )

            if len(curr_group) > 1:
                fig_curr = px.bar(
                    curr_group,
                    x="Currency",
                    y="Value_PLN",
                    title="Podział portfela według waluty ekspozycji (PLN)",
                )
                fig_curr.update_layout(
                    xaxis_title="Waluta",
                    yaxis_title="Wartość (PLN)",
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    font_color="#111827",
                )
                st.plotly_chart(fig_curr, use_container_width=True)
        else:
            st.info("Brak danych do wyświetlenia struktury portfela.")

    # ---------------- TAB PORTFOLIO ----------------
    with tab_portfolio:
        st.subheader("Pozycje rynkowe")

        def trend_html(val):
            if val == "up":
                return '<span class="trend-up">⬆</span>'
            elif val == "down":
                return '<span class="trend-down">⬇</span>'
            elif val == "flat":
                return '<span class="trend-flat">→</span>'
            else:
                return '<span class="trend-flat">–</span>'

        df_disp = df.copy()
        df_disp["Trend1mHTML"] = df_disp["Trend1m"].apply(trend_html)
        df_disp["Trend1wHTML"] = df_disp["Trend1w"].apply(trend_html)

        def vsp_html(v):
            if pd.isna(v):
                return "—"
            if v >= 0:
                return f'<span class="pl-positive">+{v:,.2f} PLN</span>'
            else:
                return f'<span class="pl-negative">{v:,.2f} PLN</span>'

        df_disp["VSP"] = df_disp["PL_Value"].apply(vsp_html)

        def fmt_qty(x):
            return f"{x:,.4f}" if pd.notna(x) else "—"

        def fmt_money(x):
            return f"{x:,.2f}" if pd.notna(x) else "—"

        table_df = pd.DataFrame({
            "Name": df_disp["Name"],
            "Ticker": df_disp["Ticker"],
            "Quantity": df_disp["Quantity"].apply(fmt_qty),
            "Purchase Price": df_disp["PurchasePrice"].apply(fmt_money),
            "Current Price": df_disp["Price"].apply(fmt_money),
            "Value USD": df_disp["Value_USD"].apply(fmt_money),
            "Value PLN": df_disp["Value_PLN"].apply(fmt_money),
            "Trend 1 Month": df_disp["Trend1mHTML"],
            "Trend 1 Week": df_disp["Trend1wHTML"],
            "VSP": df_disp["VSP"],
        })

        html_table = table_df.to_html(index=False, escape=False)
        st.markdown(f'<div class="portfolio-table">{html_table}</div>', unsafe_allow_html=True)

        if missing:
            st.warning("Brak danych cenowych dla: " + ", ".join(sorted(set(missing))))

    # ---------------- TAB SAVINGS ----------------
    with tab_savings:
        st.subheader("Inne oszczędności (PLN)")

        manual_rows = [
            {"Aktywo": "Obligacje skarbowe", "Value_PLN": bonds_value},
            {"Aktywo": "PPK – obecna wartość", "Value_PLN": ppk_value},
        ]
        df_manual = pd.DataFrame(manual_rows)

        st.table(
            df_manual.style.format(
                {"Value_PLN": "{:,.2f}"},
                na_rep="—",
            )
        )

        st.caption(f"Łączna wartość: {(bonds_value + ppk_value):,.2f} PLN")

        st.markdown("---")
        st.subheader("Prognoza obligacji skarbowych (konserwatywnie)")

        horizons = [5, 10, 15, 20, 25]
        bonds_rows = []
        for h in horizons:
            fv = project_bonds(bonds_value, h)
            bonds_rows.append({"Horyzont (lata)": h, "Prognozowana wartość (PLN)": fv})
        bonds_df = pd.DataFrame(bonds_rows)
        st.table(
            bonds_df.style.format(
                {"Prognozowana wartość (PLN)": "{:,.2f}"},
                na_rep="—",
            )
        )
        st.caption(
            f"Założona roczna stopa zwrotu obligacji: {BONDS_RATE_ANNUAL*100:.1f}% (konserwatywnie, przed podatkiem)."
        )

        st.markdown("---")
        st.subheader("Prognoza PPK")

        salary_brutto = st.number_input(
            "Twoje wynagrodzenie brutto (PLN/miesiąc) – dla prognozy PPK:",
            min_value=0.0,
            value=0.0,
            step=500.0,
            key="savings_salary_brutto",
        )

        ppk_rows = []
        for h in horizons:
            fv_ppk = project_ppk_custom(ppk_value, salary_brutto, h)
            ppk_rows.append({"Horyzont (lata)": h, "Prognozowana wartość PPK (PLN)": fv_ppk})
        ppk_df = pd.DataFrame(ppk_rows)
        st.table(
            ppk_df.style.format(
                {"Prognozowana wartość PPK (PLN)": "{:,.2f}"},
                na_rep="—",
            )
        )
        st.caption(
            "Przyjęto: Twój wkład + pracodawcy = 3% wynagrodzenia brutto miesięcznie, "
            f"oraz dopłatę państwa {PPK_STATE_ANNUAL:.0f} PLN/rok, roczna stopa zwrotu {PPK_RATE_ANNUAL*100:.1f}%."
        )

    # ---------------- TAB RETIREMENT PLANNER ----------------
    with tab_plan:
        st.subheader("Planowanie emerytury – model do 90. roku życia")

        st.markdown(
            """
Tutaj obliczamy, ile kapitału potrzebujesz, aby przejść na **spokojną emeryturę**,
z założeniem, że środki mają wystarczyć mniej więcej do 90. roku życia.
"""
        )

        spend_option = st.radio(
            "Jak zmienią się Twoje wydatki na emeryturze?",
            [
                "Będę wydawać mniej (–30%)",
                "Będę wydawać tyle samo",
                "Będę wydawać więcej (+30%)",
            ],
            key="rp_spend_option",
        )

        base_monthly = st.number_input(
            "Twoje miesięczne wydatki dzisiaj (PLN):",
            min_value=0.0,
            value=8000.0,
            step=500.0,
            key="rp_base_monthly",
        )

        if spend_option == "Będę wydawać mniej (–30%)":
            monthly_needs_today = base_monthly * 0.7
        elif spend_option == "Będę wydawać więcej (+30%)":
            monthly_needs_today = base_monthly * 1.3
        else:
            monthly_needs_today = base_monthly

        st.write(f"**Szacowane potrzebne miesięczne wydatki (dzisiaj): {monthly_needs_today:,.2f} PLN**")

        age_now = st.number_input(
            "Twój obecny wiek:",
            min_value=18,
            max_value=80,
            value=40,
            key="rp_age_now",
        )
        age_retire = st.number_input(
            "Wiek przejścia na emeryturę:",
            min_value=50,
            max_value=80,
            value=65,
            key="rp_age_retire",
        )
        age_end = 90
        years_to_retirement = max(int(age_retire) - int(age_now), 0)
        years_of_retirement = max(age_end - int(age_retire), 0)

        inflation_pct = st.slider(
            "Przewidywana średnia inflacja roczna (%):",
            0.0,
            10.0,
            4.0,
            step=0.5,
            key="rp_inflation_pct",
        )
        inflation = inflation_pct / 100.0
        st.caption(
            "Inflacja to średni wzrost cen rocznie. Jeśli nie wiesz, co wybrać, 4% to ostrożne, realistyczne założenie "
            "dla długiego okresu w Polsce."
        )

        real_return_pct = st.slider(
            "Realna stopa zwrotu w czasie emerytury (% ponad inflację):",
            0.0,
            5.0,
            2.0,
            step=0.5,
            key="rp_real_return_pct",
        )
        real_return = real_return_pct / 100.0
        st.caption(
            "Realna stopa zwrotu to zysk z inwestycji **po uwzględnieniu inflacji**. "
            "Konserwatywnie przyjmuje się 1–3% dla spokojnego portfela z obligacjami i ETF-ami."
        )

        st.markdown("---")
        st.subheader("Założenia dotyczące emerytury z ZUS")

        zus_mode = st.radio(
            "Jak chcesz uwzględnić ZUS w tym modelu?",
            [
                "Pesymistycznie: ZUS ≈ 25% mojego obecnego wynagrodzenia netto",
                "Nie uwzględniaj ZUS (załóż 0 PLN)",
            ],
            key="rp_zus_mode",
        )

        salary_net = st.number_input(
            "Twoje obecne wynagrodzenie netto (PLN/miesiąc):",
            min_value=0.0,
            value=0.0,
            step=500.0,
            key="rp_salary_net",
        )

        if zus_mode.startswith("Pesymistycznie") and salary_net > 0:
            zus_monthly_today = salary_net * 0.25
            st.caption(
                f"Na potrzeby obliczeń przyjmujemy, że Twoja przyszła emerytura z ZUS (w dzisiejszych pieniądzach) "
                f"wyniesie ok. 25% wynagrodzenia netto, czyli **{zus_monthly_today:,.2f} PLN/miesiąc**."
            )
        else:
            zus_monthly_today = 0.0
            st.caption(
                "W tym modelu przyjmujemy, że nie będziesz otrzymywać realnej emerytury z ZUS (0 PLN). "
                "To bardzo konserwatywne założenie."
            )

        (
            required_capital,
            future_monthly,
            future_yearly,
            yearly_gap_after_zus,
        ) = required_capital_finite_horizon(
            monthly_needs_today,
            years_to_retirement,
            years_of_retirement,
            inflation,
            zus_monthly_today,
            real_return,
        )

        st.session_state["rp_required_capital"] = float(required_capital)
        st.session_state["rp_years_to_retirement"] = int(years_to_retirement)
        st.session_state["rp_years_of_retirement"] = int(years_of_retirement)
        st.session_state["rp_age_now_val"] = int(age_now)
        st.session_state["rp_age_retire_val"] = int(age_retire)

        st.markdown("### Wyniki – model do 90. roku życia")

        st.write(f"Przyszłe miesięczne koszty (po inflacji): **{future_monthly:,.2f} PLN**")
        st.write(f"Przyszłe roczne koszty (po inflacji): **{future_yearly:,.2f} PLN**")
        st.write(f"Roczne koszty po uwzględnieniu ZUS: **{yearly_gap_after_zus:,.2f} PLN**")

        if yearly_gap_after_zus == 0:
            st.info(
                "Przy tych założeniach prognozowana emerytura z ZUS w pełni pokrywa Twoje koszty życia. "
                "W tym modelu nie potrzebujesz dodatkowego kapitału, dlatego wymagany kapitał wynosi 0 PLN."
            )

        st.write(
            f"**Wymagany kapitał emerytalny na starcie emerytury:** **{required_capital:,.2f} PLN** "
            f"(okres emerytury: {years_of_retirement} lat)."
        )

        portfolio_market_pln = total_pln
        st.write(
            f"**Twój obecny majątek inwestycyjny (portfel + obligacje + PPK): {portfolio_now:,.2f} PLN**"
        )
        st.caption(
            f"- Portfel rynkowy (akcje/ETF/krypto): {portfolio_market_pln:,.2f} PLN  \n"
            f"- Obligacje skarbowe: {bonds_value:,.2f} PLN  \n"
            f"- PPK: {ppk_value:,.2f} PLN"
        )

        gap = required_capital - portfolio_now
        if required_capital == 0 and yearly_gap_after_zus == 0:
            st.success(
                "Według tych założeń Twoja emerytura z ZUS sama pokrywa koszty życia. "
                "Twoje inwestycje są nadwyżką / dodatkową poduszką bezpieczeństwa. 💚"
            )
        else:
            if gap > 0:
                st.warning(f"Brakuje Ci ok. **{gap:,.2f} PLN** do założonego celu (w tym modelu).")
            else:
                st.success(
                    "Na podstawie tych założeń masz już wystarczający kapitał (lub nadwyżkę) "
                    "względem wymaganego poziomu. 💚"
                )

    # ---------------- TAB PENSION PROGRESS ----------------
    with tab_progress:
        st.subheader("📈 Pension Progress – gdzie jesteś na drodze do celu?")

        required_capital = float(st.session_state.get("rp_required_capital", 0.0))
        years_to_retirement = int(st.session_state.get("rp_years_to_retirement", 0))
        years_of_retirement = int(st.session_state.get("rp_years_of_retirement", 0))
        age_now_state = int(st.session_state.get("rp_age_now_val", 40))
        age_retire_state = int(st.session_state.get("rp_age_retire_val", age_now_state + years_to_retirement))

        if years_to_retirement <= 0:
            st.info(
                "Najpierw ustaw swoje założenia w zakładce **🧓 Retirement Planner** – "
                "wydatki, wiek emerytury, inflację i ZUS."
            )
        else:
            if required_capital > 0:
                progress_ratio = portfolio_now / required_capital
            else:
                progress_ratio = 1.0

            if required_capital == 0:
                health_label = "💚 Według tego modelu nie potrzebujesz dodatkowego kapitału."
                health_text = (
                    "Prognozowana emerytura z ZUS pokrywa w całości założone koszty życia. "
                    "Twoje inwestycje są nadwyżką i zwiększają komfort oraz bezpieczeństwo."
                )
            else:
                if progress_ratio >= 0.8:
                    health_label = "💚 Jesteś bardzo blisko swojego celu emerytalnego."
                    health_text = (
                        f"Masz już około **{progress_ratio*100:,.1f}%** wymaganego kapitału. "
                        "Jesteś w strefie zielonej – teraz chodzi raczej o dopracowanie strategii niż o pogoń za wynikiem."
                    )
                elif progress_ratio >= 0.4:
                    health_label = "💛 Jesteś w połowie drogi."
                    health_text = (
                        f"Masz około **{progress_ratio*100:,.1f}%** wymaganego kapitału. "
                        "Przy konsekwentnym oszczędzaniu możesz spokojnie domknąć cel."
                    )
                else:
                    health_label = "❤️ Jesteś na początku drogi."
                    health_text = (
                        f"Masz około **{progress_ratio*100:,.1f}%** wymaganego kapitału. "
                        "To dobry moment, żeby zbudować stałą, automatyczną ścieżkę oszczędzania."
                    )

            st.markdown(f"### {health_label}")
            st.write(health_text)

            st.markdown("#### Twój postęp względem celu")

            progress_value = min(max(progress_ratio, 0.0), 1.0)
            st.progress(progress_value)

            st.write(
                f"Aktualny majątek (portfel + obligacje + PPK): **{portfolio_now:,.2f} PLN**"
            )
            if required_capital > 0:
                st.write(
                    f"Wymagany kapitał emerytalny (z zakładki Retirement Planner): **{required_capital:,.2f} PLN**"
                )
            else:
                st.write(
                    "Wymagany kapitał emerytalny w tym modelu wynosi **0 PLN**, "
                    "ponieważ ZUS pokrywa w całości założone koszty życia."
                )

            st.markdown("---")
            st.markdown("#### Prognoza kapitału do emerytury")

            base_return = 0.025
            recommended_monthly = required_monthly_saving(
                required_capital,
                portfolio_now,
                years_to_retirement,
                base_return,
            )

            if required_capital > 0:
                if recommended_monthly > 0:
                    st.write(
                        f"Aby osiągnąć cel **{required_capital:,.0f} PLN** w scenariuszu bazowym "
                        f"(2.5% realnej stopy zwrotu) w ciągu {years_to_retirement} lat, "
                        f"powinnaś odkładać około **{recommended_monthly:,.0f} PLN/miesiąc**."
                    )
                else:
                    st.write(
                        "Przy obecnym poziomie majątku i czasie do emerytury "
                        "nie potrzebujesz dodatkowych regularnych wpłat, aby osiągnąć cel w scenariuszu bazowym."
                    )
            else:
                st.write(
                    "Ponieważ w tym modelu ZUS pokrywa Twoje koszty życia, "
                    "każda dodatkowa wpłata buduje nadwyżkę i komfort emerytalny."
                )

            default_monthly = recommended_monthly if recommended_monthly > 0 else 0.0

            monthly_saving = st.number_input(
                "Planowana miesięczna kwota oszczędzania do emerytury (PLN):",
                min_value=0.0,
                value=float(round(default_monthly)) if default_monthly > 0 else 0.0,
                step=200.0,
                key="pp_monthly_saving",
            )

            st.caption(
                "Możesz tu wpisać kwotę, którą realnie jesteś w stanie odkładać co miesiąc, "
                "a poniższy wykres pokaże, dokąd może Cię to doprowadzić w różnych scenariuszach rynkowych."
            )

            ages = [age_now_state + i for i in range(1, years_to_retirement + 1)]

            scenarios = [
                ("Pesymistyczny (1% realnie)", 0.01),
                ("Bazowy (2.5% realnie)", 0.025),
                ("Optymistyczny (4% realnie)", 0.04),
            ]

            rows = []
            final_base = None

            for name, r in scenarios:
                values = simulate_future_wealth(portfolio_now, monthly_saving, years_to_retirement, r)
                for age, val in zip(ages, values):
                    rows.append({"Age": age, "Scenario": name, "Value_PLN": val})
                if "Bazowy" in name and values:
                    final_base = values[-1]

            if rows:
                proj_df = pd.DataFrame(rows)

                st.markdown(
                    """
**Scenariusze na wykresie:**
- *Pesymistyczny (1% realnie)* – rynki zachowują się słabo, zyski z inwestycji są niewielkie.  
- *Bazowy (2.5% realnie)* – realistyczny, długoterminowy wynik spokojnego portfela (obligacje + ETF-y).  
- *Optymistyczny (4% realnie)* – dobre warunki rynkowe, wyższe realne zyski z inwestycji.

Realna stopa zwrotu oznacza wynik **po uwzględnieniu inflacji**.
"""
                )

                fig_proj = px.line(
                    proj_df,
                    x="Age",
                    y="Value_PLN",
                    color="Scenario",
                    title="Prognozowany kapitał do wieku emerytalnego (realnie, w dzisiejszych PLN)",
                )
                if required_capital > 0:
                    fig_proj.add_hline(
                        y=required_capital,
                        line_dash="dash",
                        annotation_text="Wymagany kapitał",
                        annotation_position="top left",
                    )
                fig_proj.update_layout(
                    xaxis_title="Wiek",
                    yaxis_title="Kapitał (PLN)",
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    font_color="#111827",
                )
                st.plotly_chart(fig_proj, use_container_width=True)

                if final_base is not None and required_capital > 0:
                    share = final_base / required_capital
                    if share >= 1:
                        st.success(
                            f"Przy wpłacie **{monthly_saving:,.0f} PLN/miesiąc** w scenariuszu bazowym "
                            f"osiągniesz około **{final_base:,.0f} PLN**, czyli **{share*100:,.1f}%** wymaganego kapitału."
                        )
                    else:
                        st.warning(
                            f"Przy wpłacie **{monthly_saving:,.0f} PLN/miesiąc** w scenariuszu bazowym "
                            f"osiągniesz około **{final_base:,.0f} PLN**, czyli **{share*100:,.1f}%** wymaganego kapitału."
                        )
                elif final_base is not None and required_capital == 0:
                    st.info(
                        f"Przy wpłacie **{monthly_saving:,.0f} PLN/miesiąc** w scenariuszu bazowym "
                        f"zbudujesz do emerytury kapitał około **{final_base:,.0f} PLN** "
                        "– będzie to nadwyżka ponad koszty pokrywane przez ZUS."
                    )
            else:
                st.info("Brak danych do narysowania prognozy kapitału.")


if __name__ == "__main__":
    main()
