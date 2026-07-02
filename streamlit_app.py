import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="BKK AIR FORCE ONE", layout="wide")

# ⚡ อัปเกรด CSS ให้กล่องเด่นแบบ Tactical Glowing
st.markdown("""
    <style>
    .metric-container {
        display: flex;
        gap: 15px;
    }
    .metric-box {
        flex: 1;
        background: linear-gradient(145deg, #1a1a1a, #000000);
        padding: 25px;
        border: 2px solid #ff4500;
        border-radius: 15px;
        box-shadow: 0 0 15px rgba(255, 69, 0, 0.4);
        text-align: center;
        transition: 0.3s;
    }
    .metric-box:hover { box-shadow: 0 0 25px rgba(255, 69, 0, 0.8); }
    .metric-label { color: #aaaaaa; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 10px; }
    .metric-value { color: #ffffff; font-size: 2.5rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# 📦 แสดงผลใน Python
st.write("### 🚨 CURRENT STATUS")
st.markdown(f'''
    <div class="metric-container">
        <div class="metric-box">
            <div class="metric-label">ฝนปัจจุบัน (mm/h)</div>
            <div class="metric-value">{data["current"]["precipitation"]}</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">ความเร็วลม (km/h)</div>
            <div class="metric-value">{data["current"]["wind_speed_10m"]}</div>
        </div>
    </div>
''', unsafe_allow_html=True)

# ดึงข้อมูล
@st.cache_data(ttl=3600)
def get_data():
    url = 'https://api.open-meteo.com/v1/forecast?latitude=13.75&longitude=100.50&current=precipitation,wind_speed_10m&hourly=precipitation_probability,wind_direction_10m&forecast_hours=24&timezone=Asia%2FBangkok'
    return requests.get(url).json()

data = get_data()
probs = data['hourly']['precipitation_probability']
wind_dir = data['hourly']['wind_direction_10m'] # ต้องไปคำนวณแปลงองศาเป็นตัวอักษรต่อ

# 1. กล่องสรุปปัจจุบัน
c1, c2 = st.columns(2)
with c1: st.markdown(f'<div class="forecast-card">ฝนปัจจุบัน: {data["current"]["precipitation"]} mm/h</div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="forecast-card">ลม: {data["current"]["wind_speed_10m"]} km/h</div>', unsafe_allow_html=True)

# 2. กราฟ
st.write("### ☢️ 24-Hour Probability Trend")
fig, ax = plt.subplots(figsize=(10, 2), facecolor='#000000')
ax.plot(probs[:24], color='#ff4500', linewidth=3)
ax.fill_between(range(24), probs[:24], color='#ff4500', alpha=0.1)
ax.set_facecolor('#000000')
ax.tick_params(colors='#ff4500')
st.pyplot(fig)

# 3. 8-HOUR TACTICAL FORECAST (ส่วนที่คุณต้องการ)
st.write("### ⏱️ 8-HOUR TACTICAL FORECAST")
for i in range(8):
    time_str = (datetime.now() + timedelta(hours=i)).strftime("%H:00")
    st.markdown(f'''
        <div class="forecast-card">
            <span style="color:#ff4500; font-weight:bold;">{time_str}</span>
            <span>โอกาสฝน: {probs[i]}%</span>
            <span>ลม: {wind_dir[i]}°</span>
        </div>
    ''', unsafe_allow_html=True)
