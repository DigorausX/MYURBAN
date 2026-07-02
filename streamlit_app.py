import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

st.set_page_config(page_title="BKK AIR FORCE ONE", layout="wide")

# ⚡ พลัง CSS สไตล์ Tactical (ใส่สีส้มไฟฟ้าและกรอบเรืองแสง)
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    h1 { color: #ff4500 !important; font-weight: 800 !important; text-transform: uppercase; letter-spacing: 2px; }
    .metric-card { 
        background: #1a1a1a; padding: 20px; border-left: 5px solid #ff4500; 
        border-radius: 5px; margin-bottom: 10px; color: white;
    }
    .big-font { font-size: 3rem !important; color: #ff4500 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 BKK AIR FORCE ONE")
st.write(f"### 🛡️ TACTICAL WEATHER DASHBOARD | {datetime.now().strftime('%d/%m/%Y')}")

# ดึงข้อมูล
@st.cache_data(ttl=3600)
def get_data():
    url = 'https://api.open-meteo.com/v1/forecast?latitude=13.75&longitude=100.50&current=precipitation,wind_speed_10m&hourly=precipitation_probability&forecast_hours=24&timezone=Asia%2FBangkok'
    return requests.get(url).json()

data = get_data()
probs = data['hourly']['precipitation_probability']
current = data['current']

# 📦 สร้าง Card สรุปสถานะแบบจี๊ดจ๊าด
st.write("---")
c1, c2 = st.columns(2)
with c1:
    st.markdown(f'<div class="metric-card">ฝน (mm/h) <div class="big-font">{current["precipitation"]}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card">โอกาสฝน <div class="big-font">{probs[0]}%</div></div>', unsafe_allow_html=True)

# 📉 กราฟ Tactical
st.write("### ☢️ 24-Hour Probability Trend")
fig, ax = plt.subplots(figsize=(10, 3), facecolor='#000000')
ax.plot(probs, color='#ff4500', linewidth=4, marker='o', markersize=8, markerfacecolor='white')
ax.fill_between(range(len(probs)), probs, color='#ff4500', alpha=0.15)
ax.set_ylim(0, 100)
ax.set_facecolor('#000000')
ax.tick_params(colors='#ff4500')
for spine in ax.spines.values(): spine.set_edgecolor('#ff4500')
st.pyplot(fig)
