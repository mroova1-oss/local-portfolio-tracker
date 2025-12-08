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
            --accent-color:  #f97316;      /* lekko pomarańczowy */
            --bg-main:       #f3f4f6;      /* jasnoszary */
            --bg-card:       #ffffff;
            --border-soft:   #e5e7eb;
            --text-main:     #111827;
            --text-muted:    #6b7280;
        }

        html, body {
            background: var(--bg-main);
            color: var(--text-main);
        }

        /* Główna kolumna – centrowanie i max szerokość (węższa, żeby hero był wyraźniejszy) */
        [data-testid="stAppViewContainer"] > .main .block-container {
            max-width: 1000px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            margin: 0 auto;
        }

        /* Tło aplikacji */
        [data-testid="stAppViewContainer"] {
            background: var(--bg-main);
            color: var(--text-main);
        }

        /* Sidebar – jasny, stonowany */
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--border-soft);
        }

        [data-testid="stSidebar"] * {
            color: var(--text-main);
        }

        /* Jasne pola input/textarea nawet przy dark theme na koncie */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stNumberInput"] input {
            background: #f9fafb !important;
            color: var(--text-main) !important;
            border: 1px solid var(--border-soft) !important;
        }

        /* Nagłówek aplikacji */
        .main > div:first-child h1 {
            font-weight: 700;
            letter-spacing: 0.02em;
        }

        /* Podtytuł */
        .main > div:first-child p {
            color: var(--text-muted);
        }

        /* Karty metric – hero sekcja */
        div[data-testid="metric-container"] {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border-soft) !important;
            padding: 20px 18px !important;
            border-radius: 16px !important;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06) !important;
        }

        div[data-testid="stMetricLabel"] {
            color: #4b5563 !important;        /* zawsze widoczne */
            font-size: 0.95rem !important;
            font-weight: 500 !important;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.8rem !important;      /* większe liczby */
            font-weight: 700 !important;
            color: #111827 !important;         /* ciemny, wyraźny */
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
        }
        table.dataframe th {
            background-color: #f9fafb;
            font-weight: 600;
        }

        /* Tabela w zakładce Pozycje rynkowe – max szerokość + centrowanie */
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
        .trend-up { color: #16a34a; font-weight: 600; }
        .trend-down { color: #dc2626; font-weight: 600; }
        .trend-flat { color: #6b7280; }

        .pl-positive { color: #16a34a; font-weight: 600; }
        .pl-negative { color: #dc2626; font-weight: 600; }

        /* Zakładki – zawsze widoczne, spójna tonacja */
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

        /* Usunięcie defaultowego menu/footera Streamlit */
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
        layout="wide"
    )
    inject_css()

    # GŁÓWNY NAGŁÓWEK
    st.title("💰 Local Portfolio Tracker & Pension Plan")
    st.caption("Twoje portfolio, Twoje bezpieczeństwo. Dane rynkowe + planowanie finansowe.")

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

`TICKER,ILOŚĆ[,CENA_ZAKUP_]()
