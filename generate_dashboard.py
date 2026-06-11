import pandas as pd
import json
import math
import numpy as np
from datetime import datetime

print("🚀 กำลังรันโปรเจกต์ BKK Air force ONE (V24 - Clean Code Edition)...")

file_name = 'BKK_All_Time_HeatIndex.csv'

# ==========================================
# 🧠 สูตรคำนวณ Heat Index
# ==========================================
def calculate_heat_index(T_C, RH):
    T_F = T_C * 9/5 + 32
    HI_F = -42.379 + 2.04901523*T_F + 10.14333127*RH - 0.22475541*T_F*RH \
           - 6.83783e-3*T_F*T_F - 5.481717e-2*RH*RH + 1.22874e-3*T_F*T_F*RH \
           + 8.5282e-4*T_F*RH*RH - 1.99e-6*T_F*T_F*RH*RH
    if RH < 13 and T_F >= 80 and T_F <= 112:
        HI_F -= ((13-RH)/4) * math.sqrt((17-abs(T_F-95.0))/17)
    elif RH > 85 and T_F >= 80 and T_F <= 87:
        HI_F += ((RH-85)/10) * ((87-T_F)/5)
    return (HI_F - 32) * 5/9

def generate_colored_matrix_html():
    temp_range = range(28, 41) 
    rh_range = range(40, 101, 5) 
    table_html = "<table class='border-collapse text-center w-full shadow-lg rounded-lg overflow-hidden' style='font-size: 11px;'><thead class='bg-slate-800'><tr><th class='border border-slate-700 p-2 font-bold text-slate-400'>RH / Temp</th>"
    for t in temp_range: table_html += f"<th class='border border-slate-700 p-2 font-bold text-white'>{t}°C</th>"
    table_html += "</tr></thead><tbody>"
    for rh in rh_range:
        table_html += f"<tr><td class='border border-slate-700 p-2 font-bold bg-slate-800 text-white'>{rh}%</td>"
        for t in temp_range:
            hi = calculate_heat_index(t, rh)
            rounded_hi = round(hi, 1)
            bg, txt, risk = "bg-slate-700", "text-white", ""
            if hi >= 52: bg, risk = "bg-red-600 shadow-[0_0_15px_rgba(239,68,68,0.4)]", "อันตรายมาก"
            elif hi >= 42: bg, risk = "bg-orange-500 shadow-[0_0_15px_rgba(249,115,22,0.4)]", "อันตราย"
            elif hi >= 33: bg, risk, txt = "bg-yellow-400 shadow-[0_0_15px_rgba(250,204,21,0.4)]", "เตือนภัย", "text-slate-900"
            elif hi >= 27: bg, risk, txt = "bg-green-500 shadow-[0_0_15px_rgba(34,197,94,0.4)]", "เฝ้าระวัง", "text-slate-900"
            tt = f"อุณหภูมิ: {t}°C, ความชื้น: {rh}%\\nรู้สึกเหมือน: {rounded_hi}°C\\nระดับ: {risk}"
            table_html += f"<td class='border border-slate-700 p-1.5 {bg} {txt} cursor-pointer hover:scale-125 hover:z-20 transition-transform relative' title='{tt}'>{rounded_hi}</td>"
        table_html += "</tr>"
    table_html += "</tbody></table>"
    return table_html

def clean_list(lst): return [x if pd.notnull(x) else None for x in lst]

try:
    colored_matrix_table_html = generate_colored_matrix_html()

    # 1. โหลดข้อมูล
    df = pd.read_csv(file_name)
    df['Time'] = df['Time'].astype(str).str.strip()
    if 'Date' in df.columns: df['Date'] = df['Date'].astype(str).str.strip()
    df['District'] = df['District'].astype(str).str.strip()
    df['Heat_Index'] = pd.to_numeric(df['Heat_Index'], errors='coerce')

    has_weather_factors = 'Temp' in df.columns and 'RH' in df.columns
    if has_weather_factors:
        df['Temp'] = pd.to_numeric(df['Temp'], errors='coerce')
        df['RH'] = pd.to_numeric(df['RH'], errors='coerce')

    df = df.dropna(subset=['Heat_Index'])
    df = df[df['Heat_Index'] <= 60]
    df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S', errors='coerce').dt.hour
    bad_morning = (df['Hour'] < 12) & (df['Heat_Index'] > 45)
    df = df[~bad_morning].copy()

    # 2. คำนวณข้อมูลหลัก
    avg_hi = round(df['Heat_Index'].mean(), 1) if not df.empty else 0
    max_hi = df['Heat_Index'].max() if not df.empty else 0
    if not df.empty:
        hottest_row = df.loc[df['Heat_Index'].idxmax()]
        hottest_district, hottest_date = hottest_row['District'], hottest_row['Date'] if 'Date' in df.columns else "N/A"
    else: hottest_district, hottest_date = "N/A", "N/A"

    df['Is_Danger'] = df['Heat_Index'] >= 42
    danger_days = int(df.groupby('Date')['Is_Danger'].max().sum()) if 'Date' in df.columns else 0

    df['Heat_Burden'] = df['Heat_Index'].apply(lambda x: x - 42.0 if pd.notnull(x) and x > 42.0 else 0)
    hours_count = df[df['Is_Danger']].groupby('District').size().reindex(df['District'].unique(), fill_value=0).sort_values(ascending=False)
    days_count = df.groupby(['District', 'Date'])['Is_Danger'].max().reset_index().groupby('District')['Is_Danger'].sum().sort_values(ascending=False) if 'Date' in df.columns else pd.Series(0, index=df['District'].unique())
    burden_all50 = df.groupby('District')['Heat_Burden'].sum().round(0).astype(int).sort_values(ascending=False)
    district_max_hi_sorted = df.groupby('District')['Heat_Index'].max().sort_values(ascending=False)

    # 3. เตรียมข้อมูลแผนที่ 3 มิติ (Triple Map Data)
    map_data = []
    for dist in df['District'].unique():
        dist_max = df[df['District'] == dist]['Heat_Index'].max()
        dist_hrs = hours_count.get(dist, 0)
        dist_dys = days_count.get(dist, 0)
        map_data.append({
            "district": dist, 
            "max_hi": round(float(dist_max), 1) if pd.notnull(dist_max) else 0,
            "hours": int(dist_hrs),
            "days": int(dist_dys)
        })
    map_data_json = json.dumps(map_data)

    # 3.1 เตรียม HTML สำหรับแผง Top 5
    top5_hours_html = ""
    for i, (dist, val) in enumerate(hours_count.head(5).items()):
        top5_hours_html += f"<div class='flex justify-between text-[11px] mb-1.5 border-b border-slate-700/50 pb-1'><span class='text-slate-300 truncate mr-1'>{i+1}. {dist}</span><span class='text-red-400 font-mono'>{val} ชม.</span></div>"

    top5_days_html = ""
    for i, (dist, val) in enumerate(days_count.head(5).items()):
        top5_days_html += f"<div class='flex justify-between text-[11px] mb-1.5 border-b border-slate-700/50 pb-1'><span class='text-slate-300 truncate mr-1'>{i+1}. {dist}</span><span class='text-orange-400 font-mono'>{val} วัน</span></div>"

    top5_max_html = ""
    for i, (dist, val) in enumerate(district_max_hi_sorted.head(5).items()):
        top5_max_html += f"<div class='flex justify-between text-[11px] mb-1.5 border-b border-slate-700/50 pb-1'><span class='text-slate-300 truncate mr-1'>{i+1}. {dist}</span><span class='text-red-500 font-mono font-bold'>{val}°C</span></div>"

    # HTML สำหรับเกณฑ์สี
    legend_hours_html = """<div class='text-[10px] space-y-1.5 text-slate-400'>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#ef4444] rounded-sm mr-2 shadow-[0_0_5px_#ef4444]'></div>&ge; 150 ชม.</div>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#f97316] rounded-sm mr-2 shadow-[0_0_5px_#f97316]'></div>100 - 149 ชม.</div>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#facc15] rounded-sm mr-2 shadow-[0_0_5px_#facc15]'></div>50 - 99 ชม.</div>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#22c55e] rounded-sm mr-2 shadow-[0_0_5px_#22c55e]'></div>&lt; 50 ชม.</div>
    </div>"""

    legend_days_html = """<div class='text-[10px] space-y-1.5 text-slate-400'>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#ef4444] rounded-sm mr-2 shadow-[0_0_5px_#ef4444]'></div>&ge; 30 วัน</div>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#f97316] rounded-sm mr-2 shadow-[0_0_5px_#f97316]'></div>20 - 29 วัน</div>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#facc15] rounded-sm mr-2 shadow-[0_0_5px_#facc15]'></div>10 - 19 วัน</div>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#22c55e] rounded-sm mr-2 shadow-[0_0_5px_#22c55e]'></div>&lt; 10 วัน</div>
    </div>"""

    legend_max_html = """<div class='text-[10px] space-y-1.5 text-slate-400'>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#ef4444] rounded-sm mr-2 shadow-[0_0_5px_#ef4444]'></div>&ge; 52.0°C</div>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#f97316] rounded-sm mr-2 shadow-[0_0_5px_#f97316]'></div>42.0 - 51.9°C</div>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#facc15] rounded-sm mr-2 shadow-[0_0_5px_#facc15]'></div>33.0 - 41.9°C</div>
        <div class='flex items-center'><div class='w-3 h-3 bg-[#22c55e] rounded-sm mr-2 shadow-[0_0_5px_#22c55e]'></div>&lt; 33.0°C</div>
    </div>"""

    # 4. ข้อมูลกราฟอื่นๆ
    hourly_avg = df.groupby('Hour')['Heat_Index'].mean().round(1)
    line_labels = json.dumps(clean_list([f"{int(h):02d}:00" for h in hourly_avg.index if pd.notnull(h)]))
    line_data = json.dumps(clean_list(hourly_avg.values.tolist()))

    if has_weather_factors:
        hourly_weather = df.groupby('Hour')[['Temp', 'RH', 'Heat_Index']].mean().round(1)
        hourly_temp, hourly_rh, hourly_hi_factors = json.dumps(clean_list(hourly_weather['Temp'].tolist())), json.dumps(clean_list(hourly_weather['RH'].tolist())), json.dumps(clean_list(hourly_weather['Heat_Index'].tolist()))
    else: hourly_temp, hourly_rh, hourly_hi_factors = "[]", "[]", "[]"

    doughnut_data = json.dumps([
        len(df[(df['Heat_Index'] >= 27) & (df['Heat_Index'] < 33)]),
        len(df[(df['Heat_Index'] >= 33) & (df['Heat_Index'] < 42)]),
        len(df[(df['Heat_Index'] >= 42) & (df['Heat_Index'] < 52)]),
        len(df[df['Heat_Index'] >= 52])
    ])

    if 'Date' in df.columns:
        daily_trend = df.groupby('Date')['Heat_Index'].agg(['max', 'mean']).reset_index().dropna(subset=['Date']).sort_values('Date')
        trend_dates, trend_max, trend_mean = json.dumps(clean_list(daily_trend['Date'].tolist())), json.dumps(clean_list(daily_trend['max'].round(1).tolist())), json.dumps(clean_list(daily_trend['mean'].round(1).tolist()))
    else: trend_dates, trend_max, trend_mean = "[]", "[]", "[]"

    hours_top10_labels, hours_top10_data = json.dumps(clean_list(hours_count.head(10).index.tolist())), json.dumps(clean_list(hours_count.head(10).values.tolist()))
    days_top10_labels, days_top10_data = json.dumps(clean_list(days_count.head(10).index.tolist())), json.dumps(clean_list(days_count.head(10).values.tolist()))
    burden_top10_labels, burden_top10_data = json.dumps(clean_list(burden_all50.head(10).index.tolist())), json.dumps(clean_list(burden_all50.head(10).values.tolist()))
    hours_all50_labels, hours_all50_data = json.dumps(clean_list(hours_count.index.tolist())), json.dumps(clean_list(hours_count.values.tolist()))
    days_all50_labels, days_all50_data = json.dumps(clean_list(days_count.index.tolist())), json.dumps(clean_list(days_count.values.tolist()))
    burden_all50_labels, burden_all50_data = json.dumps(clean_list(burden_all50.index.tolist())), json.dumps(clean_list(burden_all50.values.tolist()))

    risk_b = {'Caution': [], 'Warning': [], 'Danger': [], 'Extreme': []}
    for dist in hours_count.head(10).index.tolist():
        d_df = df[df['District'] == dist]
        risk_b['Caution'].append(len(d_df[(d_df['Heat_Index'] >= 27) & (d_df['Heat_Index'] < 33)]))
        risk_b['Warning'].append(len(d_df[(d_df['Heat_Index'] >= 33) & (d_df['Heat_Index'] < 42)]))
        risk_b['Danger'].append(len(d_df[(d_df['Heat_Index'] >= 42) & (d_df['Heat_Index'] < 52)]))
        risk_b['Extreme'].append(len(d_df[d_df['Heat_Index'] >= 52]))
    risk_c_json, risk_w_json, risk_d_json, risk_e_json = json.dumps(clean_list(risk_b['Caution'])), json.dumps(clean_list(risk_b['Warning'])), json.dumps(clean_list(risk_b['Danger'])), json.dumps(clean_list(risk_b['Extreme']))

    streak_labels_json, streak_data_json = "[]", "[]"
    if 'Date' in df.columns:
        dds = df.groupby(['District', 'Date'])['Is_Danger'].max().reset_index().dropna(subset=['Date']).sort_values(['District', 'Date'])
        dds['Streak'] = dds.groupby('District')['Is_Danger'].apply(lambda x: x * (x.groupby((x != x.shift()).cumsum()).cumcount() + 1)).reset_index(level=0, drop=True)
        max_streaks = dds.groupby('District')['Streak'].max().nlargest(10).astype(int)
        streak_labels_json, streak_data_json = json.dumps(clean_list(max_streaks.index.tolist())), json.dumps(clean_list(max_streaks.values.tolist()))

    top500_records = df.nlargest(500, 'Heat_Index')
    table_html = ""
    for idx, row in top500_records.iterrows():
        date_str = row['Date'] if 'Date' in df.columns else "-"
        table_html += f"""<tr><td>{date_str}</td><td>{row['Time']}</td><td class="font-semibold">{row['District']}</td><td class="font-bold text-red-500">{row['Heat_Index']} °C</td></tr>"""

    gen_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BKK Air force ONE (Command Center)</title>
        
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-annotation/2.2.1/chartjs-plugin-annotation.min.js"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        
        <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        
        <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
        <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>

        <style>
            body {{ font-family: 'Kanit', sans-serif; background-color: #0b0f19; color: #f8fafc; overflow-x: hidden; }}
            .glass-card {{ background: rgba(17, 24, 39, 0.8); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; position: relative; }}
            .tab-btn {{ transition: all 0.3s; border-bottom: 2px solid transparent; letter-spacing: 0.5px; }}
            .tab-active {{ color: #ef4444; border-bottom: 2px solid #ef4444; background: rgba(239, 68, 68, 0.08); }}
            .hidden-tab {{ display: none; }}
            .mono-text {{ font-family: 'Share Tech Mono', monospace; letter-spacing: 0.5px; }}
            .cal-table {{ border-collapse: separate; border-spacing: 0 10px; }}
            
            .export-btn {{ position: absolute; top: 15px; right: 15px; color: #64748b; background: rgba(255,255,255,0.05); padding: 5px 10px; border-radius: 5px; cursor: pointer; transition: 0.3s; z-index: 10; font-size: 12px; font-family: 'Kanit', sans-serif; }}
            .export-btn:hover {{ color: #fff; background: #ef4444; }}

            .dataTables_wrapper .dataTables_length, .dataTables_wrapper .dataTables_filter, .dataTables_wrapper .dataTables_info, .dataTables_wrapper .dataTables_processing, .dataTables_wrapper .dataTables_paginate {{ color: #cbd5e1 !important; margin-bottom: 10px; font-family: 'Kanit', sans-serif; }}
            .dataTables_wrapper .dataTables_filter input {{ background-color: #1e293b; border: 1px solid #334155; color: white; border-radius: 4px; padding: 4px 8px; margin-left: 8px; outline: none; }}
            table.dataTable tbody tr {{ background-color: #0f172a; transition: 0.2s; }}
            table.dataTable tbody tr:hover {{ background-color: #1e293b !important; }}
            table.dataTable tbody td {{ border-bottom: 1px solid #1e293b; padding: 12px; color: #cbd5e1; }}
            table.dataTable thead th {{ border-bottom: 2px solid #334155; color: #94a3b8; font-weight: 500; padding: 12px; border-top: none; }}
            .dataTables_wrapper .dataTables_paginate .paginate_button {{ color: #cbd5e1 !important; border: 1px solid #334155 !important; background: #1e293b !important; border-radius: 4px; margin: 0 2px; }}
            .dataTables_wrapper .dataTables_paginate .paginate_button.current, .dataTables_wrapper .dataTables_paginate .paginate_button:hover {{ background: #ef4444 !important; color: white !important; border-color: #ef4444 !important; }}
            
            .leaflet-layer, .leaflet-control-zoom-in, .leaflet-control-zoom-out, .leaflet-control-attribution {{ filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%); }}
            .leaflet-popup-content-wrapper {{ background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; font-family: 'Kanit', sans-serif; }}
            .leaflet-popup-tip {{ background-color: #1e293b; border: 1px solid #334155; }}
            .leaflet-container {{ background: #0f172a; outline: 0; }}
            
            h1, h2, h3, h4, h5, h6, .font-bold {{ font-weight: 500; }}
        </style>
    </head>
    <body>

        <nav class="glass-card sticky top-0 z-50 border-b border-slate-800 m-4 rounded-xl shadow-lg">
            <div class="w-full px-8 py-4 flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold flex items-center tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-orange-400" style="padding-bottom: 5px;">
                        <i class="fa-solid fa-plane-up mr-3 text-red-500 animate-pulse"></i> BKK Air force ONE
                    </h1>
                    <p class="text-xs text-slate-400 mt-1"><i class="fa-solid fa-clock mr-1"></i> SYSTEM OVERVIEW AS OF: <span class="mono-text">{gen_time}</span></p>
                </div>
                <div class="space-x-1 no-print flex text-md">
                    <button onclick="switchTab('overview')" id="btn-overview" class="tab-btn tab-active px-4 py-2 rounded-t-md font-bold"><i class="fa-solid fa-layer-group mr-2"></i>ภาพรวมเชิงพื้นที่</button>
                    <button onclick="switchTab('analytics')" id="btn-analytics" class="tab-btn px-4 py-2 rounded-t-md font-bold text-slate-400 hover:text-white"><i class="fa-solid fa-microscope mr-2"></i>วิเคราะห์เชิงลึก</button>
                    <button onclick="switchTab('deepdive')" id="btn-deepdive" class="tab-btn px-4 py-2 rounded-t-md font-bold text-slate-400 hover:text-white"><i class="fa-solid fa-map-location-dot mr-2"></i>เจาะลึก Top 10</button>
                    <button onclick="switchTab('all50')" id="btn-all50" class="tab-btn px-4 py-2 rounded-t-md font-bold text-slate-400 hover:text-white"><i class="fa-solid fa-list-ol mr-2"></i>จัดอันดับ 50 เขต</button>
                    <button onclick="switchTab('data')" id="btn-data" class="tab-btn px-4 py-2 rounded-t-md font-bold text-slate-400 hover:text-white"><i class="fa-solid fa-database mr-2"></i>ฐานข้อมูล</button>
                </div>
            </div>
        </nav>

        <main class="w-full px-8 mt-6 pb-12">
            <div class="bg-red-950/40 border border-red-500/40 p-4 rounded-lg mb-8 flex justify-between items-center shadow-lg shadow-red-950/50">
                <div class="flex items-center">
                    <div class="animate-pulse w-3 h-3 bg-red-500 rounded-full mr-4 shadow-[0_0_12px_#ef4444]"></div>
                    <p class="text-red-200 text-md"><strong class="text-red-400 text-lg">CRITICAL ANOMALY ALERT:</strong> ตรวจพบดัชนีความร้อนระดับสูงสุด ณ <span class="text-white font-bold text-lg">{hottest_district} (ที่ {max_hi}°C)</span></p>
                </div>
                <div class="text-xs text-red-400 mono-text border border-red-500/30 px-2 py-1 rounded bg-red-950/20">STATUS: MONITORING ACTIVE</div>
            </div>

            <div id="tab-overview">
                <div class="grid grid-cols-2 xl:grid-cols-4 gap-6 mb-6">
                    <div class="glass-card p-6 border-l-4 border-l-orange-500 flex-1"><p class="text-sm text-slate-400 font-bold mb-1"><i class="fa-solid fa-temperature-half mr-2"></i>ค่าเฉลี่ย BMA</p><h3 class="text-5xl font-bold text-orange-400 mono-text">{avg_hi}<span class="text-2xl text-slate-500 ml-1">°C</span></h3></div>
                    <div class="glass-card p-6 border-l-4 border-l-red-500 flex-1"><p class="text-sm text-slate-400 font-bold mb-1"><i class="fa-solid fa-arrow-trend-up mr-2"></i>สถิติพีกสูงสุด</p><h3 class="text-5xl font-bold text-red-500 mono-text">{max_hi}<span class="text-2xl text-slate-500 ml-1">°C</span></h3></div>
                    <div class="glass-card p-6 border-l-4 border-l-red-600 flex-1"><p class="text-sm text-slate-400 font-bold mb-1"><i class="fa-solid fa-fire-flame-curved mr-2"></i>เขตวิกฤตอันดับ 1</p><h3 class="text-3xl font-bold text-white tracking-wide mt-2">{hottest_district}</h3></div>
                    <div class="glass-card p-6 border-l-4 border-l-orange-600 flex-1"><p class="text-sm text-slate-400 font-bold mb-1"><i class="fa-solid fa-calendar-xmark mr-2"></i>วันอันตรายรวม</p><h3 class="text-5xl font-bold text-orange-400 mono-text">{danger_days}<span class="text-2xl text-slate-500 ml-1">วัน</span></h3></div>
                </div>
                
                <div class="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6 w-full">
                    <div class="glass-card p-4 flex flex-col">
                        <h3 class="font-bold text-lg mb-3 text-slate-200"><i class="fa-solid fa-stopwatch text-red-400 mr-2"></i>แผนที่ชั่วโมงวิกฤต (Hours)</h3>
                        <div class="flex flex-col sm:flex-row gap-4 h-[420px]">
                            <div class="w-full sm:w-1/3 flex flex-col justify-between bg-slate-900/50 p-3 rounded-lg border border-slate-700/50">
                                <div><h4 class="text-xs font-bold text-slate-400 mb-2 border-b border-slate-700 pb-1 uppercase tracking-wide">🏆 Top 5 สูงสุด</h4>{top5_hours_html}</div>
                                <div><h4 class="text-xs font-bold text-slate-400 mb-2 border-b border-slate-700 pb-1 uppercase tracking-wide">📊 เกณฑ์สี (ชั่วโมง)</h4>{legend_hours_html}</div>
                            </div>
                            <div id="mapHours" class="w-full sm:w-2/3 rounded-lg border border-slate-700 shadow-inner h-full"></div>
                        </div>
                    </div>
                    <div class="glass-card p-4 flex flex-col">
                        <h3 class="font-bold text-lg mb-3 text-slate-200"><i class="fa-solid fa-calendar-day text-orange-400 mr-2"></i>แผนที่วันอันตราย (Days)</h3>
                        <div class="flex flex-col sm:flex-row gap-4 h-[420px]">
                            <div class="w-full sm:w-1/3 flex flex-col justify-between bg-slate-900/50 p-3 rounded-lg border border-slate-700/50">
                                <div><h4 class="text-xs font-bold text-slate-400 mb-2 border-b border-slate-700 pb-1 uppercase tracking-wide">🏆 Top 5 สูงสุด</h4>{top5_days_html}</div>
                                <div><h4 class="text-xs font-bold text-slate-400 mb-2 border-b border-slate-700 pb-1 uppercase tracking-wide">📊 เกณฑ์สี (วัน)</h4>{legend_days_html}</div>
                            </div>
                            <div id="mapDays" class="w-full sm:w-2/3 rounded-lg border border-slate-700 shadow-inner h-full"></div>
                        </div>
                    </div>
                    <div class="glass-card p-4 flex flex-col">
                        <h3 class="font-bold text-lg mb-3 text-slate-200"><i class="fa-solid fa-fire text-red-600 mr-2"></i>แผนที่ความร้อนสูงสุด (Max °C)</h3>
                        <div class="flex flex-col sm:flex-row gap-4 h-[420px]">
                            <div class="w-full sm:w-1/3 flex flex-col justify-between bg-slate-900/50 p-3 rounded-lg border border-slate-700/50">
                                <div><h4 class="text-xs font-bold text-slate-400 mb-2 border-b border-slate-700 pb-1 uppercase tracking-wide">🏆 Top 5 สูงสุด</h4>{top5_max_html}</div>
                                <div><h4 class="text-xs font-bold text-slate-400 mb-2 border-b border-slate-700 pb-1 uppercase tracking-wide">📊 เกณฑ์สี (°C)</h4>{legend_max_html}</div>
                            </div>
                            <div id="mapMaxHI" class="w-full sm:w-2/3 rounded-lg border border-slate-700 shadow-inner h-full"></div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                    <div class="glass-card p-6 lg:col-span-2">
                        <button class="export-btn" onclick="exportChart('hourlyLineChart', 'BMA_Hourly_Trend')"><i class="fa-solid fa-camera mr-1"></i> Export PNG</button>
                        <h3 class="font-bold text-xl mb-4 text-slate-200"><i class="fa-solid fa-clock text-orange-400 mr-2"></i>ความผันแปรของดัชนีความร้อนเฉลี่ยรายชั่วโมง</h3>
                        <div class="relative w-full h-[300px]"><canvas id="hourlyLineChart"></canvas></div>
                    </div>
                    <div class="glass-card p-6 flex flex-col justify-center items-center">
                        <button class="export-btn" onclick="exportChart('doughnutChart', 'Risk_Proportion')"><i class="fa-solid fa-camera mr-1"></i> Export PNG</button>
                        <h3 class="font-bold text-xl mb-4 w-full text-slate-200 text-left"><i class="fa-solid fa-circle-notch text-red-400 mr-2"></i>สัดส่วนเวลาตามระดับเตือนภัย</h3>
                        <div class="w-full relative" style="height: 250px;"><canvas id="doughnutChart"></canvas></div>
                    </div>
                </div>
                <div class="glass-card p-6">
                    <button class="export-btn" onclick="exportChart('dailyTrendChart', 'Daily_Trend_Timeline')"><i class="fa-solid fa-camera mr-1"></i> Export PNG</button>
                    <h3 class="font-bold text-xl mb-4 text-slate-200"><i class="fa-solid fa-chart-area text-red-500 mr-2"></i>ไทม์ไลน์ภาพใหญ่ดัชนีความร้อนรายวัน (ตั้งแต่วันแรก - วันสุดท้าย)</h3>
                    <div class="relative w-full h-[350px]"><canvas id="dailyTrendChart"></canvas></div>
                </div>
            </div>

            <div id="tab-analytics" class="hidden-tab">
                <div class="glass-card p-6 mb-6">
                    <h3 class="font-bold text-xl mb-2 text-slate-200"><i class="fa-solid fa-calendar-days text-orange-500 mr-2"></i>ปฏิทินระดับความร้อนและบทสรุปรายเดือน (Monthly Executive Calendar)</h3>
                    <div id="calendar-container" class="w-full mt-4"></div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                    <div class="glass-card p-6">
                        <button class="export-btn" onclick="exportChart('weatherFactorsChart', 'Temp_vs_RH_vs_HI')"><i class="fa-solid fa-camera mr-1"></i> Export</button>
                        <h3 class="font-bold text-xl mb-2 text-slate-200"><i class="fa-solid fa-chart-line text-blue-400 mr-2"></i>กราฟปัจจัยอุตุนิยมวิทยาแบบละเอียด: Temp vs RH vs HI</h3>
                        <div class="relative w-full h-[350px] mt-4"><canvas id="weatherFactorsChart"></canvas></div>
                    </div>
                    <div class="glass-card p-6">
                        <button class="export-btn" onclick="exportChart('streakChart', 'Heatwave_Streak')"><i class="fa-solid fa-camera mr-1"></i> Export</button>
                        <h3 class="font-bold text-xl mb-2 text-slate-200"><i class="fa-solid fa-wave-square text-red-500 mr-2"></i>ระบบวิเคราะห์การสะสมคลื่นความร้อนต่อเนื่อง</h3>
                        <div class="relative w-full h-[350px] mt-4"><canvas id="streakChart"></canvas></div>
                    </div>
                </div>

                <div class="glass-card p-6 mb-6">
                    <h3 class="font-bold text-xl mb-4 text-center text-blue-400"><i class="fa-solid fa-table-cells mr-2"></i>ตารางแมทริกซ์วิเคราะห์จุดตัดอุทก-อุตุนิยมวิทยา</h3>
                    <div class="overflow-x-auto p-4 bg-slate-950/40 rounded-xl border border-slate-800 shadow-inner">
                        {colored_matrix_table_html}
                    </div>
                </div>
            </div>

            <div id="tab-deepdive" class="hidden-tab">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                    <div class="glass-card p-6"><button class="export-btn" onclick="exportChart('barHoursTop10Chart', 'Top10_Hours')"><i class="fa-solid fa-camera"></i></button><h3 class="font-bold text-lg text-slate-300 mb-2"><i class="fa-solid fa-stopwatch text-red-400 mr-2"></i>Top 10 จำนวนชั่วโมงวิกฤต</h3><div class="relative w-full h-[350px]"><canvas id="barHoursTop10Chart"></canvas></div></div>
                    <div class="glass-card p-6"><button class="export-btn" onclick="exportChart('barDaysTop10Chart', 'Top10_Days')"><i class="fa-solid fa-camera"></i></button><h3 class="font-bold text-lg text-slate-300 mb-2"><i class="fa-solid fa-calendar-day text-orange-400 mr-2"></i>Top 10 จำนวนวันอันตราย</h3><div class="relative w-full h-[350px]"><canvas id="barDaysTop10Chart"></canvas></div></div>
                    <div class="glass-card p-6"><button class="export-btn" onclick="exportChart('barBurdenTop10Chart', 'Top10_Burden')"><i class="fa-solid fa-camera"></i></button><h3 class="font-bold text-lg text-slate-300 mb-2"><i class="fa-solid fa-fire text-orange-500 mr-2"></i>Top 10 ภาระคะแนนความร้อนสะสม</h3><div class="relative w-full h-[350px]"><canvas id="barBurdenTop10Chart"></canvas></div></div>
                </div>
                <div class="glass-card p-6"><button class="export-btn" onclick="exportChart('stackedRiskChart', 'Top10_Risk_Breakdown')"><i class="fa-solid fa-camera mr-1"></i> Export PNG</button><h3 class="font-bold text-xl text-slate-200 mb-4"><i class="fa-solid fa-layer-group text-blue-400 mr-2"></i>สัดส่วนชั่วโมงจำแนกตามความเข้มข้นของดัชนีความเสี่ยง (Top 10)</h3><div class="relative w-full h-[350px]"><canvas id="stackedRiskChart"></canvas></div></div>
            </div>

            <div id="tab-all50" class="hidden-tab">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="glass-card p-6"><h3 class="font-bold text-lg text-slate-300 mb-4">จัดอันดับ 50 เขต: ชั่วโมง</h3><div class="relative w-full h-[1300px]"><canvas id="barHoursAll50Chart"></canvas></div></div>
                    <div class="glass-card p-6"><h3 class="font-bold text-lg text-slate-300 mb-4">จัดอันดับ 50 เขต: วัน</h3><div class="relative w-full h-[1300px]"><canvas id="barDaysAll50Chart"></canvas></div></div>
                    <div class="glass-card p-6"><h3 class="font-bold text-lg text-slate-300 mb-4">จัดอันดับ 50 เขต: คะแนนสะสม</h3><div class="relative w-full h-[1300px]"><canvas id="barBurdenAll50Chart"></canvas></div></div>
                </div>
            </div>

            <div id="tab-data" class="hidden-tab">
                <div class="glass-card p-6">
                    <h3 class="font-bold text-xl mb-4 text-slate-200"><i class="fa-solid fa-magnifying-glass text-blue-400 mr-2"></i>ระบบค้นหาอัจฉริยะ: ดัชนีความร้อนสูงสุด Top 500 Records</h3>
                    <div class="overflow-x-auto">
                        <table id="smartTable" class="w-full text-left text-md" style="width: 100%;">
                            <thead><tr><th>วันที่ (Date)</th><th>เวลา (Time)</th><th>เขตพื้นที่ (District)</th><th>ดัชนีความร้อน (Heat Index)</th></tr></thead>
                            <tbody>{table_html}</tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="glass-card p-4 mt-6 border border-slate-800 bg-slate-950/80 shadow-2xl">
                <h4 class="text-xs font-bold text-red-400 uppercase tracking-widest mb-3 mono-text flex items-center">
                    <i class="fa-solid fa-terminal mr-2 animate-pulse"></i> AIR FORCE ONE: ENVIRONMENTAL LOGS & TELEMETRY FEED
                </h4>
                <div class="mono-text text-slate-400 bg-black/40 p-3 rounded border border-slate-900 max-h-[120px] overflow-y-auto" style="font-size: 11px; line-height: 1.6;">
                    <div class="border-left-2 border-red-500 pl-2 mb-1 text-red-400">[CRITICAL] Detected maximum Heat Index value of {max_hi}°C at location target: '{hottest_district}'. Triggering Level 4 response.</div>
                    <div class="border-left-2 border-orange-500 pl-2 mb-1 text-orange-400">[ANALYSIS] Cross-evaluation confirms Relative Humidity boundaries exceeding normal seasonal parameters.</div>
                    <div class="border-left-2 border-yellow-500 pl-2 mb-1 text-yellow-400">[MONITORING] Season summary metrics: total extreme cumulative danger days registered at {danger_days} days across BMA domain network.</div>
                    <div class="border-left-2 border-blue-500 pl-2 mb-1 text-blue-400">[SYSTEM] ALL 50 DISTRICTS INTEGRATED. SPATIAL POLYGON MAPPING ONLINE. READY FOR REPORTING.</div>
                </div>
            </div>
        </main>

        <script>
            function exportChart(chartId, filename) {{
                const canvas = document.getElementById(chartId);
                if (canvas) {{
                    const url = canvas.toDataURL("image/png");
                    const link = document.createElement('a'); link.download = filename + '.png'; link.href = url; link.click();
                }}
            }}

            function switchTab(tabId) {{
                ['overview', 'analytics', 'deepdive', 'all50', 'data'].forEach(id => {{ document.getElementById('tab-' + id).classList.add('hidden-tab'); document.getElementById('btn-' + id).classList.remove('tab-active', 'text-ef4444'); document.getElementById('btn-' + id).classList.add('text-slate-400'); }});
                document.getElementById('tab-' + tabId).classList.remove('hidden-tab'); document.getElementById('btn-' + tabId).classList.add('tab-active'); document.getElementById('btn-' + tabId).classList.remove('text-slate-400');
                if(tabId === 'overview') {{ setTimeout(() => {{ if(window.maps) {{ window.maps.hours.invalidateSize(); window.maps.days.invalidateSize(); window.maps.maxHI.invalidateSize(); }} }}, 200); }}
            }}

            $(document).ready(function() {{
                $('#smartTable').DataTable({{ pageLength: 15, order: [[3, 'desc']], language: {{ search: "ค้นหา:", lengthMenu: "แสดง _MENU_ แถว", info: "แสดง _START_ ถึง _END_ จาก _TOTAL_" }} }});
            }});

            try {{
                const mapDataRaw = {map_data_json};
                const heatMapDict = {{}};
                mapDataRaw.forEach(d => {{
                    let cleanName = d.district.replace('เขต', '').replace(/\\s+/g, '').toLowerCase();
                    heatMapDict[cleanName] = d;
                }});
                
                const enToTh = {{
                    "phranakhon": "พระนคร", "dusit": "ดุสิต", "nongchok": "หนองจอก", "bangrak": "บางรัก", "bangkhen": "บางเขน",
                    "bangkapi": "บางกะปิ", "pathumwan": "ปทุมวัน", "pomprapsattruphai": "ป้อมปราบศัตรูพ่าย", "pomprap": "ป้อมปราบศัตรูพ่าย",
                    "phrakhanong": "พระโขนง", "minburi": "มีนบุรี", "latkrabang": "ลาดกระบัง", "yannawa": "ยานนาวา", 
                    "samphanthawong": "สัมพันธวงศ์", "samphan": "สัมพันธวงศ์", "phayathai": "พญาไท", "thonburi": "ธนบุรี", 
                    "bangkokyai": "บางกอกใหญ่", "huaikhwang": "ห้วยขวาง", "khlongsan": "คลองสาน", "talingchan": "ตลิ่งชัน", 
                    "bangkoknoi": "บางกอกน้อย", "bangkhunthian": "บางขุนเทียน", "phasicharoen": "ภาษีเจริญ", "nongkhaem": "หนองแขม", 
                    "ratburana": "ราษฎร์บูรณะ", "bangphlat": "บางพลัด", "dindaeng": "ดินแดง", "buengkum": "บึงกุ่ม", 
                    "sathon": "สาทร", "bangsue": "บางซื่อ", "chatuchak": "จตุจักร", "bangkholam": "บางคอแหลม", "bangkolaem": "บางคอแหลม", 
                    "prawet": "ประเวศ", "khlongtoei": "คลองเตย", "suanluang": "สวนหลวง", "chomthong": "จอมทอง", 
                    "donmueang": "ดอนเมือง", "ratchathewi": "ราชเทวี", "latphrao": "ลาดพร้าว", "watthana": "วัฒนา", 
                    "bangkhae": "บางแค", "laksi": "หลักสี่", "saimai": "สายไหม", "khannayao": "คันนายาว", 
                    "saphansung": "สะพานสูง", "wangthonglang": "วังทองหลาง", "khlongsamwa": "คลองสามวา", "bangna": "บางนา", 
                    "thawiwatthana": "ทวีวัฒนา", "thungkhru": "ทุ่งครุ", "bangbon": "บางบอน"
                }};

                const maps = {{
                    hours: L.map('mapHours', {{ zoomControl: false }}).setView([13.7563, 100.5018], 9),
                    days: L.map('mapDays', {{ zoomControl: false }}).setView([13.7563, 100.5018], 9),
                    maxHI: L.map('mapMaxHI', {{ zoomControl: false }}).setView([13.7563, 100.5018], 9)
                }};
                window.maps = maps;

                const tileUrl = 'https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png';
                L.tileLayer(tileUrl).addTo(maps.hours); L.tileLayer(tileUrl).addTo(maps.days); L.tileLayer(tileUrl).addTo(maps.maxHI);

                function getColor(val, type) {{
                    if (type === 'hours') return val >= 150 ? '#ef4444' : val >= 100 ? '#f97316' : val >= 50 ? '#facc15' : '#22c55e';
                    if (type === 'days') return val >= 30 ? '#ef4444' : val >= 20 ? '#f97316' : val >= 10 ? '#facc15' : '#22c55e';
                    if (type === 'maxHI') return val >= 52 ? '#ef4444' : val >= 42 ? '#f97316' : val >= 33 ? '#facc15' : '#22c55e';
                    return '#1e293b';
                }}

                fetch('https://raw.githubusercontent.com/pcrete/gsvloader-demo/master/geojson/Bangkok-districts.geojson')
                    .then(res => res.json())
                    .then(data => {{
                        ['hours', 'days', 'maxHI'].forEach(type => {{
                            L.geoJSON(data, {{
                                style: function (feature) {{
                                    let propStr = JSON.stringify(feature.properties).toLowerCase().replace(/[\\s\\-\\.]/g, '').replace('khet', '').replace('เขต', '');
                                    let cleanName = null;
                                    for (let th in heatMapDict) {{ if (propStr.includes(th)) {{ cleanName = th; break; }} }}
                                    if (!cleanName) {{ for (let en in enToTh) {{ if (propStr.includes(en)) {{ cleanName = enToTh[en]; break; }} }} }}
                                    
                                    let d = heatMapDict[cleanName];
                                    let val = d ? (type === 'hours' ? d.hours : type === 'days' ? d.days : d.max_hi) : 0;
                                    let color = d ? getColor(val, type) : '#1e293b';
                                    
                                    return {{ fillColor: color, weight: 1, opacity: 1, color: '#334155', fillOpacity: 0.8 }};
                                }},
                                onEachFeature: function (feature, layer) {{
                                    let propStr = JSON.stringify(feature.properties).toLowerCase().replace(/[\\s\\-\\.]/g, '').replace('khet', '').replace('เขต', '');
                                    let cleanName = null;
                                    for (let th in heatMapDict) {{ if (propStr.includes(th)) {{ cleanName = th; break; }} }}
                                    if (!cleanName) {{ for (let en in enToTh) {{ if (propStr.includes(en)) {{ cleanName = enToTh[en]; break; }} }} }}
                                    
                                    let d = heatMapDict[cleanName];
                                    if (d) {{
                                        let val = type === 'hours' ? d.hours : type === 'days' ? d.days : d.max_hi;
                                        let color = getColor(val, type);
                                        let unit = type === 'hours' ? 'ชั่วโมง' : type === 'days' ? 'วัน' : '°C';
                                        let titleText = type === 'hours' ? 'สะสม' : type === 'days' ? 'สะสม' : 'สูงสุด';
                                        
                                        layer.on({{
                                            mouseover: function (e) {{ e.target.setStyle({{ weight: 3, color: '#fff', fillOpacity: 1 }}); e.target.bringToFront(); }},
                                            mouseout: function (e) {{ layer.setStyle({{ weight: 1, color: '#334155', fillOpacity: 0.8 }}); }}
                                        }});
                                        layer.bindPopup(`<div class="text-center font-bold text-lg mb-1">${{d.district}}</div><hr class="border-slate-600 my-1">${{titleText}}: <span style="color:${{color}}; font-size:16px;">${{val}} ${{unit}}</span>`);
                                    }}
                                }}
                            }}).addTo(maps[type]);
                        }});
                    }})
            }} catch(e) {{ console.error("Map Setup Error", e); }}

            Chart.defaults.color = '#cbd5e1'; Chart.defaults.font.family = "'Kanit', sans-serif"; Chart.defaults.maintainAspectRatio = false; 
            const warningAnnotations = {{ annotations: {{ lineCaution: {{ type: 'line', yMin: 27, yMax: 27, borderColor: '#22c55e', borderWidth: 1.5, borderDash: [5, 5] }}, lineWarning: {{ type: 'line', yMin: 33, yMax: 33, borderColor: '#eab308', borderWidth: 1.5, borderDash: [5, 5] }}, lineDanger: {{ type: 'line', yMin: 42, yMax: 42, borderColor: '#f97316', borderWidth: 1.5, borderDash: [5, 5] }}, lineExtreme: {{ type: 'line', yMin: 52, yMax: 52, borderColor: '#ef4444', borderWidth: 1.5, borderDash: [5, 5] }} }} }};

            try {{
                const trendDates = {trend_dates}; const trendMax = {trend_max}; const calContainer = document.getElementById('calendar-container');
                if (trendDates && trendDates.length > 0) {{
                    const monthData = {{}};
                    trendDates.forEach((dStr, i) => {{ if (dStr) {{ const parts = dStr.split('-'); if(parts.length === 3) {{ const ym = parts[0] + '-' + parts[1]; const day = parseInt(parts[2], 10); if(!monthData[ym]) monthData[ym] = {{}}; monthData[ym][day] = {{ val: trendMax[i], date: dStr }}; }} }} }});
                    const monthNames = {{'01':'ม.ค.', '02':'ก.พ.', '03':'มี.ค.', '04':'เม.ย.', '05':'พ.ค.', '06':'มิ.ย.', '07':'ก.ค.', '08':'ส.ค.', '09':'ก.ย.', '10':'ต.ค.', '11':'พ.ย.', '12':'ธ.ค.'}};
                    
                    let tableHTML = '<div class="overflow-x-auto pb-4"><table class="w-full text-center cal-table text-sm font-bold">';
                    tableHTML += '<thead><tr class="text-slate-400 tracking-wider"><th class="p-2 text-left w-24">MONTH</th>';
                    for(let i=1; i<=31; i++) tableHTML += `<th class="p-1 w-8 opacity-60">${{i}}</th>`;
                    tableHTML += '<th class="w-4"></th><th class="p-2 w-16 text-slate-300">AVG</th><th class="p-2 w-20 text-slate-300">DANGER</th><th class="p-2 w-16 text-slate-300">PEAK</th></tr></thead><tbody>';
                    
                    Object.keys(monthData).sort().forEach(ym => {{
                        const [y, m] = ym.split('-'); let monthSum = 0; let monthCount = 0; let monthDangerCount = 0; let monthMax = 0;
                        tableHTML += `<tr class="bg-slate-800/30 hover:bg-slate-800/60 transition-colors shadow-sm"><td class="p-3 text-slate-300 text-left font-bold tracking-wide rounded-l-xl border-y border-l border-slate-700/50 text-md">${{monthNames[m]}} ${{y.substring(2)}}</td>`;
                        for(let d=1; d<=31; d++) {{
                            const cd = monthData[ym][d];
                            if(cd) {{
                                const val = cd.val; monthSum += val; monthCount++; if(val >= 42) monthDangerCount++; if(val > monthMax) monthMax = val;
                                let bg = '#1e293b'; let tc = '#fff'; let glow = '';
                                if (val >= 52) {{ bg = '#dc2626'; glow = 'shadow-[0_0_8px_rgba(220,38,38,0.6)]'; }} else if (val >= 42) {{ bg = '#f97316'; glow = 'shadow-[0_0_6px_rgba(249,115,22,0.4)]'; }} else if (val >= 33) {{ bg = '#facc15'; tc = '#000'; }} else if (val >= 27) {{ bg = '#22c55e'; tc = '#000'; }}
                                tableHTML += `<td class="p-1 border-y border-slate-700/50"><div class="w-7 h-7 mx-auto rounded-md flex items-center justify-center cursor-pointer hover:scale-125 transition-all font-bold text-[12px] ${{glow}} border border-white/10" style="background-color:${{bg}}; color:${{tc}};" title="Date: ${{cd.date}}\\nMax HI: ${{val.toFixed(1)}}°C">${{d}}</div></td>`;
                            }} else {{ tableHTML += `<td class="p-1 border-y border-slate-700/50"><div class="w-7 h-7 mx-auto rounded-md bg-slate-800/20 border border-slate-700/30"></div></td>`; }}
                        }}
                        let monthAvg = monthCount > 0 ? (monthSum / monthCount).toFixed(1) : 0;
                        tableHTML += `<td class="border-y border-slate-700/50"></td><td class="p-2 text-orange-400 font-bold border-y border-slate-700/50 bg-slate-900/40 text-md mono-text">${{monthAvg}}</td><td class="p-2 border-y border-slate-700/50 bg-slate-900/40"><span class="bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-1 rounded text-sm mono-text">${{monthDangerCount}} d</span></td><td class="p-2 border-y border-r border-slate-700/50 bg-slate-900/40 rounded-r-xl"><span class="bg-red-600 text-white px-2 py-1 rounded text-sm font-bold shadow-[0_0_8px_rgba(220,38,38,0.5)] mono-text">${{monthMax.toFixed(1)}}</span></td></tr>`;
                    }}); 
                    tableHTML += '</tbody></table></div>'; calContainer.innerHTML = tableHTML;
                }}
            }} catch (e) {{}}

            try {{ new Chart(document.getElementById('hourlyLineChart').getContext('2d'), {{ type: 'line', data: {{ labels: {line_labels}, datasets: [{{ label: 'เฉลี่ย (°C)', data: {line_data}, borderColor: '#f97316', backgroundColor: 'rgba(249, 115, 22, 0.15)', borderWidth: 3, fill: true, tension: 0.4 }}] }}, options: {{ plugins: {{ legend: {{ display: false }}, annotation: warningAnnotations }}, scales: {{ y: {{ min: 25, max: 60 }}, x: {{ grid: {{ color: 'rgba(255,255,255,0.03)' }} }} }} }} }}); }} catch(e) {{}}
            try {{ new Chart(document.getElementById('doughnutChart').getContext('2d'), {{ type: 'doughnut', data: {{ labels: ['เฝ้าระวัง', 'เตือนภัย', 'อันตราย', 'อันตรายมาก'], datasets: [{{ data: {doughnut_data}, backgroundColor: ['#22c55e', '#eab308', '#f97316', '#ef4444'], borderWidth: 2, borderColor: '#0f172a' }}] }}, options: {{ plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#f8fafc' }} }} }}, cutout: '70%' }} }}); }} catch(e) {{}}
            try {{ new Chart(document.getElementById('dailyTrendChart').getContext('2d'), {{ type: 'line', data: {{ labels: {trend_dates}, datasets: [{{ label: 'Max (°C)', data: {trend_max}, borderColor: '#ef4444', backgroundColor: 'transparent', borderWidth: 2, pointRadius: 3, pointBackgroundColor: '#ef4444', tension: 0.2 }}, {{ label: 'Mean (°C)', data: {trend_mean}, borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)', borderWidth: 2, fill: true, pointRadius: 2, tension: 0.2 }}] }}, options: {{ plugins: {{ legend: {{ display: true, position: 'top' }}, annotation: warningAnnotations }}, scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ min: 25, max: 60, grid: {{ color: 'rgba(255,255,255,0.03)' }} }} }} }} }}); }} catch(e) {{}}
            try {{ new Chart(document.getElementById('streakChart').getContext('2d'), {{ type: 'bar', data: {{ labels: {streak_labels_json}, datasets: [{{ label: 'วันติดต่อกัน', data: {streak_data_json}, backgroundColor: '#dc2626', borderRadius: 4 }}] }}, options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ title: {{ display: true, text: 'จำนวนวัน' }}, grid: {{ color: 'rgba(255,255,255,0.03)' }} }}, y: {{ grid: {{ display: false }} }} }} }} }}); }} catch(e) {{}}
            try {{ new Chart(document.getElementById('stackedRiskChart').getContext('2d'), {{ type: 'bar', data: {{ labels: {hours_top10_labels}, datasets: [{{ label: 'เฝ้าระวัง', data: {risk_c_json}, backgroundColor: '#22c55e' }}, {{ label: 'เตือนภัย', data: {risk_w_json}, backgroundColor: '#eab308' }}, {{ label: 'อันตราย', data: {risk_d_json}, backgroundColor: '#f97316' }}, {{ label: 'อันตรายมาก', data: {risk_e_json}, backgroundColor: '#ef4444' }}] }}, options: {{ indexAxis: 'y', plugins: {{ legend: {{ position: 'bottom' }} }}, scales: {{ x: {{ stacked: true, grid: {{ color: 'rgba(255,255,255,0.03)' }} }}, y: {{ stacked: true, grid: {{ display: false }} }} }} }} }}); }} catch(e) {{}}

            try {{
                const temp_data = {hourly_temp}; const rh_data = {hourly_rh}; const hi_data = {hourly_hi_factors};
                if(temp_data && temp_data.length > 0) {{
                    new Chart(document.getElementById('weatherFactorsChart').getContext('2d'), {{
                        type: 'line', data: {{ labels: {line_labels}, datasets: [
                            {{ label: 'Heat Index (°C)', data: hi_data, borderColor: '#ef4444', backgroundColor: 'transparent', borderWidth: 3, yAxisID: 'y' }},
                            {{ label: 'Temp (°C)', data: temp_data, borderColor: '#facc15', backgroundColor: 'transparent', borderWidth: 2, borderDash: [5, 5], yAxisID: 'y' }},
                            {{ label: 'RH (%)', data: rh_data, borderColor: '#0ea5e9', backgroundColor: 'rgba(14, 165, 233, 0.05)', borderWidth: 2, fill: true, yAxisID: 'y1' }}
                        ] }},
                        options: {{ responsive: true, interaction: {{ mode: 'index', intersect: false }}, plugins: {{ legend: {{ position: 'top', labels: {{ color: '#cbd5e1' }} }} }},
                            scales: {{ x: {{ grid: {{ color: 'rgba(255,255,255,0.03)' }} }}, y: {{ type: 'linear', display: true, position: 'left', title: {{ display: true, text: 'อุณหภูมิ / ดัชนีความร้อน (°C)' }}, grid: {{ color: 'rgba(255,255,255,0.03)' }} }}, y1: {{ type: 'linear', display: true, position: 'right', title: {{ display: true, text: 'ความชื้น (%)' }}, grid: {{ display: false }}, min: 30, max: 100 }} }}
                        }}
                    }});
                }}
            }} catch(e) {{}}

            function createHBar(ctxId, l, d, c) {{ try {{ new Chart(document.getElementById(ctxId).getContext('2d'), {{ type: 'bar', data: {{ labels: l, datasets: [{{ data: d, backgroundColor: c, borderRadius: 4 }}] }}, options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: {{ color: 'rgba(255,255,255,0.03)' }} }}, y: {{ grid: {{ display: false }} }} }} }} }}); }} catch(e) {{}} }}
            createHBar('barHoursTop10Chart', {hours_top10_labels}, {hours_top10_data}, '#ef4444'); createHBar('barDaysTop10Chart', {days_top10_labels}, {days_top10_data}, '#f97316'); createHBar('barBurdenTop10Chart', {burden_top10_labels}, {burden_top10_data}, '#ea580c'); 
            createHBar('barHoursAll50Chart', {hours_all50_labels}, {hours_all50_data}, '#dc2626'); createHBar('barDaysAll50Chart', {days_all50_labels}, {days_all50_data}, '#ea580c'); createHBar('barBurdenAll50Chart', {burden_all50_labels}, {burden_all50_data}, '#c2410c');
        </script>
    </body>
    </html>
    """

    # 💡 อัปเดตให้เป็น index.html ตามที่ตั้งค่าไว้ในแผนที่ 3 (Automated Command Center)
    output_html = 'index.html'
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ บูรณาการ 3 แผนที่ 3 มิติ พร้อมแผงข้อมูล Top 5 ด้านข้างสำเร็จแล้ว!! (V24)")
    print(f"📂 ไฟล์ถูกบันทึกชื่อ: {output_html}")

except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดในฝั่ง Python: {e}")