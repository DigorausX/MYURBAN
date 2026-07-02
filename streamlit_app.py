<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BKK AIR FORCE ONE - Tactical Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
</head>
<body class="bg-black text-orange-500 font-sans p-4">

<div id="dashboard-content" class="max-w-md mx-auto space-y-4 bg-black">
    <header class="text-center pb-2 border-b border-orange-900">
        <h1 class="font-bold tracking-[0.2em] text-lg uppercase text-orange-500">BKK AIR FORCE ONE</h1>
        <p id="status" class="text-[9px] text-orange-700 uppercase mt-1 tracking-widest">SYSTEM INITIALIZING...</p>
    </header>

    <div class="bg-neutral-900 p-4 rounded-xl border border-orange-900">
        <canvas id="rainChart" height="200"></canvas>
    </div>

    <button id="downloadBtn" class="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-xs font-bold uppercase">
        ดาวน์โหลดภาพรายงาน (.png)
    </button>
</div>

<script>
    // [ใส่ฟังก์ชัน loadTacticalData และ Logic การวาดกราฟจากขั้นตอนก่อนหน้านี้ไว้ตรงนี้]
    //... (นำโค้ด JS ที่เราทำไว้มาวางในนี้)
    
    // ฟังก์ชันดาวน์โหลดภาพ
    document.getElementById('downloadBtn').addEventListener('click', function() {
        html2canvas(document.querySelector("#dashboard-content")).then(canvas => {
            const link = document.createElement('a');
            link.download = 'BKK-Tactical-Report.png';
            link.href = canvas.toDataURL();
            link.click();
        });
    });
</script>
</body>
</html>
