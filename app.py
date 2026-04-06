import os
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# الواجهة المتطورة (Modern Glassmorphism UI)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Tunes Pro V14 | larebifarese28</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: white; font-family: 'Cairo', sans-serif;
            margin: 0; min-height: 100vh; overflow-x: hidden;
        }
        .header { padding: 40px 20px; text-align: center; }
        .header h1 { font-size: 3rem; margin: 0; letter-spacing: 2px; }
        .header span { color: #ff4b2b; }
        .container { max-width: 600px; margin: auto; padding: 20px; }
        .search-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px; border-radius: 50px;
            display: flex; align-items: center;
            backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2);
        }
        input {
            flex: 1; background: transparent; border: none;
            color: white; padding: 15px 20px; font-size: 18px; outline: none;
        }
        .btn-search {
            background: #ff4b2b; color: white; border: none;
            padding: 12px 30px; border-radius: 40px;
            cursor: pointer; font-weight: bold; transition: 0.3s;
        }
        .btn-search:hover { background: #ff416c; transform: scale(1.05); }
        .result-card {
            background: rgba(255, 255, 255, 0.05);
            margin-top: 20px; padding: 15px; border-radius: 20px;
            display: flex; align-items: center; gap: 15px;
            border: 1px solid rgba(255,255,255,0.1); transition: 0.3s;
        }
        .thumb { width: 70px; height: 70px; border-radius: 15px; object-fit: cover; }
        .info { flex: 1; }
        .play-btn {
            background: #ff4b2b; border: none; color: white;
            width: 45px; height: 45px; border-radius: 50%;
            cursor: pointer; font-size: 20px;
        }
        #player-bar {
            position: fixed; bottom: 0; width: 100%;
            background: rgba(0,0,0,0.9); padding: 20px;
            display: none; border-top: 3px solid #ff4b2b; text-align: center;
        }
        audio { width: 100%; max-width: 500px; filter: hue-rotate(180deg); }
    </style>
</head>
<body>
    <div class="header">
        <h1>Vibe <span>Tunes</span> Pro</h1>
        <p style="opacity: 0.6;">بواسطة: larebifarese28-cmd</p>
    </div>

    <div class="container">
        <div class="search-box">
            <input type="text" id="query" placeholder="ابحث عن ديدين كلاش، سولكينغ...">
            <button class="btn-search" onclick="search()">بحث</button>
        </div>
        <div id="loader" style="display:none; text-align:center; margin-top:30px;">🚀 جاري البحث بسرعة البرق...</div>
        <div id="results"></div>
    </div>

    <div id="player-bar">
        <div id="track-title" style="margin-bottom: 10px; font-size: 14px;"></div>
        <audio id="audio" controls autoplay></audio>
    </div>

    <script>
        async function search() {
            const q = document.getElementById('query').value;
            if(!q) return;
            document.getElementById('loader').style.display = 'block';
            document.getElementById('results').innerHTML = '';
            
            try {
                const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
                const data = await res.json();
                document.getElementById('loader').style.display = 'none';
                data.forEach(item => {
                    document.getElementById('results').innerHTML += `
                        <div class="result-card">
                            <img src="${item.thumb}" class="thumb">
                            <div class="info">
                                <div style="font-weight:bold;">${item.title}</div>
                                <div style="font-size:10px; opacity:0.5;">YouTube Music</div>
                            </div>
                            <button class="play-btn" onclick="play('${item.url}', '${item.title.replace(/'/g, "")}')">▶</button>
                        </div>`;
                });
            } catch(e) { alert("حدث خطأ، حاول مرة أخرى"); }
        }

        function play(url, title) {
            document.getElementById('player-bar').style.display = 'block';
            document.getElementById('track-title').innerText = "تستمع إلى: " + title;
            const audio = document.getElementById('audio');
            audio.src = url; audio.play();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE)

@app.route('/search')
def search():
    query = request.args.get('q')
    # إعدادات سريعة جداً لتجنب تعليق Render
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch5',
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch5:{query}", download=False)
        return jsonify([{'title': e['title'], 'url': e['url'], 'thumb': e['thumbnail']} for e in info['entries']])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

