import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from github import Github
import os
import re

st.set_page_config(
    page_title="AI Gold & Currency Tracker", page_icon="💰", layout="wide"
)

st.title("💰 AI Gold & Currency Tracker")
st.write("Gold and currency price tracker with Machine Learning prediction")

CSV_FILE = "market_history.csv"

ASSETS = {
    "Gold 24K": "https://www.tgju.org/profile/geram24",
    "Gold 18K": "https://www.tgju.org/profile/geram18",
    "Dollar": "https://www.tgju.org/profile/price_dollar_rl",
    "Euro": "https://www.tgju.org/profile/price_eur",
}


def extract_price(text):
    patterns = [
        r"نرخ فعلی\s*([\d,]+)",
        r"قیمت فعلی\s*([\d,]+)",
        r"آخرین نرخ\s*([\d,]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(",", ""))

    return None


def fetch_price(name, url):
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    price = extract_price(text)

    return {
        "Name": name,
        "Price": price,
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def load_history():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)

    return pd.DataFrame(columns=["Name", "Price", "Time"])


def save_history(df):
    df.to_csv(CSV_FILE, index=False)


def predict_next_price(df, asset_name):
    asset_df = df[df["Name"] == asset_name].copy()

    if len(asset_df) < 5:
        return None

    asset_df = asset_df.reset_index(drop=True)

    X = [[i] for i in range(len(asset_df))]
    y = asset_df["Price"]

    model = RandomForestRegressor(n_estimators=50, random_state=42)

    model.fit(X, y)

    next_index = [[len(asset_df)]]

    return model.predict(next_index)[0]


def upload_to_github():
    try:
        github_token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["REPO_NAME"]

        github = Github(github_token)
        repo = github.get_repo(repo_name)

        with open(CSV_FILE, "r", encoding="utf-8") as file:
            content = file.read()

        try:
            old_file = repo.get_contents(CSV_FILE)
            repo.update_file(
                path=CSV_FILE,
                message="Update market history",
                content=content,
                sha=old_file.sha,
            )
        except:
            repo.create_file(
                path=CSV_FILE, message="Create market history", content=content
            )

        return True

    except Exception as error:
        st.warning(f"GitHub upload failed: {error}")
        return False


if st.button("📡 Fetch Prices And Predict", use_container_width=True):

    history = load_history()

    new_rows = []

    with st.spinner("Fetching market prices..."):
        for name, url in ASSETS.items():
            try:
                row = fetch_price(name, url)

                if row["Price"] is not None:
                    new_rows.append(row)

            except Exception as error:
                st.error(f"Error fetching {name}: {error}")

    if new_rows:
        new_df = pd.DataFrame(new_rows)

        history = pd.concat([history, new_df], ignore_index=True)

        save_history(history)

        st.success("Prices saved successfully!")

        upload_to_github()

        st.subheader("📊 Latest Prices")

        cols = st.columns(4)

        for i, row in new_df.iterrows():
            prediction = predict_next_price(history, row["Name"])

            with cols[i]:
                st.metric(
                    label=row["Name"],
                    value=f"{row['Price']:,.0f}",
                    delta=(
                        f"Prediction: {prediction:,.0f}"
                        if prediction
                        else "Need more data"
                    ),
                )

        st.subheader("📁 Saved History")
        st.dataframe(history.tail(20), use_container_width=True)

        selected_asset = st.selectbox("Select asset for chart:", list(ASSETS.keys()))

        chart_df = history[history["Name"] == selected_asset]

        st.line_chart(chart_df, x="Time", y="Price")

    else:
        st.error("No data received.")
