import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import locale

# ตั้งค่าหน้า Dashboard
st.set_page_config(page_title="BKK AIR FORCE ONE", layout="wide")

# ปรับแต่ง CSS ให้เป็นสไตล์ Tactical Dark
st.markdown("""
    <style>
    .main { background-color: #000000; }
    h1, h2, h3 { color: #f97316; }
    </style>
""", unsafe_allow_html=True)

# 1. แสดงวันที่ภาษาไทย
def get_thai_date():
    days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
    months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
              "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    now = datetime.now()
    return f"วัน{days[now.weekday()]}ที่ {now.day} {months[now.month-1]} {now.year + 543}"

st.title("BKK AIR FORCE ONE")
st.subheader(f"Tactical Weather Dashboard | {get_thai_date()}")

# ดึงข้อมูล
@st.cache_data(ttl=3600)
def get_data():
    url = 'https://api.open-meteo.com/v1/forecast?latitude=13.75&longitude=100.50&current=precipitation,wind_speed_10m&hourly=precipitation_probability&forecast_hours=24&timezone=Asia%2FBangkok'
    return requests.get(url).json()

data = get_data()
probs = data['hourly']['precipitation_probability']
current = data['current']

# 2. กล่องสรุปค่าปัจจุบัน (Custom Dashboard UI)
st.write("### CURRENT STATUS (ปัจจุบัน)")
col1, col2 = st.columns(2)
with col1:
    st.metric("ฝน (mm/h) / โอกาส", f"{current['precipitation']} | {probs[0]}%")
with col2:
    st.metric("ความเร็วลม", f"{current['wind_speed_10m']} km/h")

# 3. กราฟพยากรณ์ 24 ชั่วโมง
st.write("### 24-Hour Probability Trend")
time_labels = [datetime.now() + timedelta(hours=i) for i in range(24)]

fig, ax = plt.subplots(figsize=(10, 3), facecolor='#000000')
ax.plot(time_labels, probs, color='#f97316', linewidth=3, marker='o')
ax.fill_between(time_labels, probs, color='#f97316', alpha=0.2)

ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
ax.set_ylim(0, 100)
ax.set_facecolor('#000000')
ax.tick_params(colors='white')
st.pyplot(fig)
