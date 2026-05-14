import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

st.set_page_config(
    page_title="Aeromche Market Dashboard", page_icon="💰", layout="wide"
)

st.markdown(
    """
<style>
.big-title {
    font-size: 48px;
    font-weight: 900;
}
.subtitle {
    color: #94a3b8;
    font-size: 18px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="big-title">💰 Aeromche Market Dashboard</div>', unsafe_allow_html=True
)

st.markdown('<div class="subtitle">Live prices from TGJU</div>', unsafe_allow_html=True)

st.divider()


def fetch_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    for _ in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception:
            time.sleep(2)

    raise Exception(f"Could not fetch data from {url}")


def extract_value(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return "Not found"


@st.cache_data(ttl=300)
def get_market_data():
    targets = [
        {
            "Icon": "🥇",
            "Market": "Tala 24 Ayar",
            "URL": "https://www.tgju.org/profile/geram24",
        },
        {
            "Icon": "🟡",
            "Market": "Tala 18 Ayar",
            "URL": "https://www.tgju.org/profile/geram18",
        },
        {
            "Icon": "💵",
            "Market": "Dollar",
            "URL": "https://www.tgju.org/profile/price_dollar_rl",
        },
        {
            "Icon": "💶",
            "Market": "Euro",
            "URL": "https://www.tgju.org/profile/price_eur",
        },
    ]

    rows = []

    for item in targets:
        html = fetch_page(item["URL"])
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)

        current_price = extract_value(
            text,
            [r"نرخ فعلی\s*([\d,]+)", r"قیمت فعلی\s*([\d,]+)", r"آخرین نرخ\s*([\d,]+)"],
        )

        daily_high = extract_value(
            text, [r"بالاترین قیمت روز\s*([\d,]+)", r"بیشترین قیمت روز\s*([\d,]+)"]
        )

        daily_low = extract_value(
            text, [r"پایین ترین قیمت روز\s*([\d,]+)", r"کمترین قیمت روز\s*([\d,]+)"]
        )

        rows.append(
            {
                "Icon": item["Icon"],
                "Bazar": item["Market"],
                "Gheymat Feli": current_price,
                "Bishtarin Gheymat Rooz": daily_high,
                "Kamtarin Gheymat Rooz": daily_low,
            }
        )

    return pd.DataFrame(rows)


if st.button("📈 Fetch Market Data", use_container_width=True):
    try:
        with st.spinner("Loading market data..."):
            df = get_market_data()

        st.success("Data fetched successfully!")

        st.subheader("📊 Jadval Gheymat-ha")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("⚡ Kart-haye Sarie")

        cols = st.columns(4)

        for i, row in df.iterrows():
            with cols[i]:
                title = f'{row["Icon"]} {row["Bazar"]}'

                st.metric(
                    label=title,
                    value=row["Gheymat Feli"],
                    delta=f'Low: {row["Kamtarin Gheymat Rooz"]}',
                )

    except Exception as e:
        st.error(e)


st.sidebar.title("⚙️ Dashboard Settings")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.info("Powered by Aeromche 🚀")
