import streamlit as st 
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Users\moala\Desktop\mood-of-the-queue-4a0e8e148eae.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Mood_of_the_Queue").sheet1

mood_score_map = {
    "🎉": 5,
    "😊": 4,
    "😐": 3,
    "😕": 2,
    "😠": 1
}

with st.form("mood_logger"):
    mood = st.radio("How does the queue feel?", ["😊", "😠", "😕", "🎉", "😐"])
    st.caption("🎉: joyful | 😊: happy | 😐: neutral | 😕: sad | 😠: frustrated" )
    note = st.text_input("Optional note").strip()
    submitted = st.form_submit_button("Log Mood")
    if submitted:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        score = mood_score_map[mood]
        sheet.append_row([now, mood, note, score])
        st.success(f"✅ Mood '{mood}' logged!")


data = sheet.get_all_records()
df = pd.DataFrame(data)

# Convert columns
df['score'] = pd.to_numeric(df['score'], errors='coerce')
df['now'] = pd.to_datetime(df['now'])
df = df.set_index('now')

# Compute today's average
today = pd.Timestamp.now().normalize()
today_avg = df.loc[df.index.normalize() == today, 'score'].mean()
today_avg = today_avg if not pd.isna(today_avg) else 0

# Compute 30-day rolling average
last_30_days = df.loc[df.index >= pd.Timestamp.now() - pd.Timedelta(days=30)]
rolling_30d_avg = last_30_days['score'].mean()

score = math.ceil(today_avg)
score_to_emoji = {v: k for k, v in mood_score_map.items()}
emoji = score_to_emoji.get(score, "❓")

# Display as Streamlit metric
a, b = st.columns(2)

with a:
    st.metric("Today's Vibe", f"{round(today_avg, 2)} {emoji}", f"{round(today_avg - rolling_30d_avg, 2)} vs 30d avg")

with b:
    selected_date = st.date_input("Filter by date", pd.Timestamp.now().date())
    filtered_df = df[df.index.date == selected_date]
    filtered_avg = filtered_df['score'].mean()
    st.write(f"**Average mood on {selected_date}:** {round(filtered_avg, 2) if not pd.isna(filtered_avg) else 'No data'}")



df_daily = df.resample("D").mean(numeric_only=True)[["score"]].dropna()

# Create figure
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_daily.index,
    y=df_daily['score'],
    fill='tozeroy',
    mode='lines',
    name='Average Mood',
    line=dict(color='royalblue'),
))

# Custom y-axis ticks with emojis
fig.update_layout(
    title="Mood Score Over Time",
    xaxis_title="Date",
    yaxis=dict(
        title="Mood",
        tickmode='array',
        tickvals=list(score_to_emoji.keys()),
        ticktext=[score_to_emoji[k] for k in score_to_emoji],
        range=[1, 5]
    ),
    template="simple_white",
    height=400,
)

# Show in Streamlit
st.plotly_chart(fig, use_container_width=True)
