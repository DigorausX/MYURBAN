import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="BKK AIR FORCE ONE", layout="wide")

st.title("BKK AIR FORCE ONE")
st.subheader("Tactical Weather Dashboard")

@st.cache_data(ttl=3600)
def get_data():
    url = 'https://api.open-meteo.com/v1/forecast?latitude=13.75&longitude=100.50&hourly=precipitation_probability&forecast_hours=24&timezone=Asia%2FBangkok'
    return requests.get(url).json()

try:
    data = get_data()
    probs = data['hourly']['precipitation_probability']
    
    # 1. สร้างรายการเวลาจริง (Time Axis)
    start_time = datetime.now()
    time_labels = [start_time + timedelta(hours=i) for i in range(len(probs))]
    
    st.write("### 24-Hour Probability Trend")
    fig, ax = plt.subplots(figsize=(10, 4), facecolor='#000000')
    
    # 2. พล็อตโดยใช้เวลาจริง
    ax.plot(time_labels, probs, color='#f97316', linewidth=3, marker='o')
    ax.fill_between(time_labels, probs, color='#f97316', alpha=0.2)
    
    # 3. จัดการสเกลเวลาบนแกน X ให้สวยงาม
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M')) # แสดงเป็น HH:MM
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3)) # แสดงทุก 3 ชั่วโมง
    
    ax.set_ylim(0, 100)
    ax.set_facecolor('#000000')
    ax.tick_params(colors='white')
    st.pyplot(fig)

    # ... (ส่วนแสดงผลอื่นๆ เหมือนเดิม)
except Exception as e:
    st.error(f"เกิดข้อผิดพลาด: {e}")
