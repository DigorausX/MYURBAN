import streamlit as st
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

st.set_page_config(page_title="BKK AIR FORCE ONE", layout="wide")

# CSS สำหรับกล่อง Metric ให้ดูดุดัน
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 50px !important;
        color: #ff4500 !important;
        font-weight: 800;
    }
    [data-testid="stMetricLabel"] {
        color: #aaaaaa !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 BKK AIR FORCE ONE")
st.write(f"### 🛡️ TACTICAL WEATHER DASHBOARD | {datetime.now().strftime('%d/%m/%Y')}")

# ดึงข้อมูล
@st.cache_data(ttl=3600)
def get_data():
    url = 'https://api.open-meteo.com/v1/forecast?latitude=13.75&longitude=100.50&current=precipitation,wind_speed_10m&hourly=precipitation_probability&forecast_hours=24&timezone=Asia%2FBangkok'
    return requests.get(url).json()

try:
    data = get_data()
    current = data['current']
    
    # ใช้ฟังก์ชัน Metric ของ Streamlit แทนการเขียน HTML เอง (กัน Error)
    col1, col2 = st.columns(2)
    col1.metric("ฝนปัจจุบัน (mm/h)", current['precipitation'])
    col2.metric("ความเร็วลม (km/h)", current['wind_speed_10m'])

    st.write("---")
    st.write("### ☢️ 24-Hour Probability Trend")
    probs = data['hourly']['precipitation_probability']
    fig, ax = plt.subplots(figsize=(10, 3), facecolor='#000000')
    ax.plot(probs, color='#ff4500', linewidth=3)
    ax.fill_between(range(24), probs, color='#ff4500', alpha=0.15)
    ax.set_facecolor('#000000')
    ax.tick_params(colors='white')
    st.pyplot(fig)

except Exception as e:
    st.error("กรุณารอระบบโหลดข้อมูล...")
