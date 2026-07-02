import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

st.set_page_config(page_title="BKK AIR FORCE ONE", layout="centered")

st.title("BKK AIR FORCE ONE")
st.subheader("Tactical Weather Dashboard")

# ดึงข้อมูลจาก API
@st.cache_data(ttl=3600)
def get_data():
    url = 'https://api.open-meteo.com/v1/forecast?latitude=13.75&longitude=100.50&hourly=precipitation_probability&forecast_hours=24&timezone=Asia%2FBangkok'
    return requests.get(url).json()

try:
    data = get_data()
    probs = data['hourly']['precipitation_probability']

    # แสดงกราฟ
    st.write("### แนวโน้มโอกาสฝน (24 ชม.)")
    fig, ax = plt.subplots(facecolor='#000000')
    ax.plot(probs, color='#f97316', linewidth=3)
    ax.fill_between(range(len(probs)), probs, color='#f97316', alpha=0.2)
    ax.set_facecolor('#000000')
    ax.tick_params(colors='white')
    st.pyplot(fig)

    # แสดงตัวเลขสรุป
    col1, col2 = st.columns(2)
    col1.metric("โอกาสฝนตอนนี้", f"{probs[0]}%")
    col2.metric("โอกาสฝนสูงสุด", f"{max(probs)}%")
    
except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
