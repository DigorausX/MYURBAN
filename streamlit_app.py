import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# ตั้งค่าหน้า Dashboard
# ปรับตรงช่วงแสดงกราฟใน streamlit_app.py
st.write("### 24-Hour Probability Trend")
    fig, ax = plt.subplots(figsize=(10, 4), facecolor='#000000') # กำหนดขนาดคงที่
    ax.plot(probs, color='#38bdf8', linewidth=3, marker='o')
    ax.fill_between(range(len(probs)), probs, color='#38bdf8', alpha=0.2)
    
    # 🚨 จุดสำคัญ: ล็อกแกน Y ให้เริ่มที่ 0 และไปจบที่ 100 เสมอ
    ax.set_ylim(0, 100) 
    
    ax.set_facecolor('#000000')
    ax.tick_params(colors='white')
    st.pyplot(fig)
st.title("BKK AIR FORCE ONE - TACTICAL DASHBOARD")

# ดึงข้อมูล API
@st.cache_data(ttl=3600)
def get_data():
    url = 'https://api.open-meteo.com/v1/forecast?latitude=13.75&longitude=100.50&current=precipitation,wind_speed_10m&hourly=precipitation_probability&past_hours=12&forecast_hours=12&timezone=Asia%2FBangkok'
    return requests.get(url).json()

try:
    data = get_data()
    probs = data['hourly']['precipitation_probability']
    
    # 1. แสดง Radar (ใช้ iframe ของ Windy)
    st.components.v1.iframe("https://embed.windy.com/embed.html?type=map&location=coordinates&lat=13.75&lon=100.50&zoom=10&overlay=rain", height=300)

    # 2. แสดงสถานะปัจจุบัน
    col1, col2 = st.columns(2)
    col1.metric("ฝนปัจจุบัน", f"{data['current']['precipitation']} mm/h")
    col2.metric("โอกาสฝน", f"{probs[12]}%")

    # 3. กราฟพยากรณ์
    st.write("### 24-Hour Probability Trend")
    fig, ax = plt.subplots(facecolor='black')
    ax.plot(probs, color='#38bdf8', marker='o')
    ax.set_facecolor('black')
    ax.tick_params(colors='white')
    st.pyplot(fig)

except Exception as e:
    st.error("เชื่อมต่อข้อมูลล้มเหลว")
