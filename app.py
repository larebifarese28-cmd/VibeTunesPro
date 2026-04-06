import os
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# الواجهة اللي خدمناها قبل التشهير (فخامة وسرعة)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Tunes Pro V14 | larebifarese28</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
    <style>
        body {
            background: radial-gradient(circle at top, #1a1a2e, #16213e, #0f3460);
            color: white; font-family: 'Cairo', sans-serif;
            margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center;
        }
        .header { padding: 50px 20px; text-align: center; width: 100%; }
        .header h1 { font-size: 3.5rem; margin: 0; text-shadow: 0 0 20px rgba(255,75,43,0.5); }
        .header span { color: #ff4b2b; }
        .container { width: 90%; max-width: 600px; }
        .search-area {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1);
            padding: 15px; border-radius: 50px; display: flex; gap: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        input {
            flex: 1; background: transparent; border: none; color: white;
            font-size: 18px; padding-right: 15px; outline: none;
        }
        .btn-search {
            background: linear-gradient(45deg, #ff4b2b, #ff416c);
            color: white; border: none; padding: 12px 35px; border-radius: 40px;
            cursor: pointer; font-weight: 800; transition: 0.4s;
        }
        .btn-search:hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(255,75,43,0.4); }
        .result-card {
            background: rgba(255, 255, 255, 0.03); margin-top: 15px;
            padding: 12px; border-radius: 20px; display: flex; align-items: center;
            gap: 15px; border: 1px solid rgba(255,255,255,0.05); transition: 0.3s;
        }
        .thumb { width: 65px; height: 65px; border-radius: 12px; object-fit: cover; border: 2px solid #ff4b2b; }
        .track-info { flex: 1; }
        .play-btn {
            background: #ff4b2b; border: none; color: white; width: 40px; height: 40px;
            border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;
        }
        #player-bar {
            position: fixed; bottom: 0; width: 100%; background: rgba(10, 10, 10, 0.95);
            padding: 20px; display: none; border-top: 3px solid #ff4b2b; text-align: center; z-index: 9999;
        }
        audio { width: 100%; max-width: 500px; margin-top: 10px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Vibe <span>Tunes</span> Pro</h1>
        <p style="opacity: 0.7;">بواسطة المطور: larebifarese28-cmd</p>
    </div>

    <div class="container">
        <div class="search-area">
            <input type="text" id="query" placeholder="اكتب اسم الأغنية هنا...">
            <button class="btn-search" onclick="searchMusic()">بحث</button>
        </div>
        <div id="loader" style="display:none; text-align:center; margin: 40px;">🚀 جاري البحث في السحابة...</div>
        <div id="results"></div>
    </div>

    <div id="player-bar">
        <div id="track-name" style="font-size: 14px; font-weight: bold;"></div>
        <audio id="audio-tag" controls autoplay></audio>
    </div>

    <script>
        async function searchMusic() {
            const query = document.getElementById('query').value;
            if(!query) return;
            document.getElementById('loader').style.display = 'block';
            document.getElementById('results').innerHTML = '';
            try {
                const res = await fetch(`/search?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                document.getElementById('loader').style.display = 'none';
                data.forEach(item => {
                    document.getElementById('results').innerHTML += `
                        <div class="result-card">
                            <img src="${item.thumb}" class="thumb">
                            <div class="track-info">
                                <div style="font-weight:bold; font-size: 14px;">${item.title}</div>
                                <div style="font-size: 11px; opacity: 0.5;">YouTube Music</div>
                            </div>
                            <button class="play-btn" onclick="play('${item.url}', '${item.title.replace(/'/g, "")}')">▶</button>
                        </div>`;
                });
            } catch(e) { 
                document.getElementById('loader').innerText = "❌ حدث خطأ، حاول مرة أخرى"; 
            }
        }
        function play(url, title) {
            document.getElementById('player-bar').style.display = 'block';
            document.getElementById('track-name').innerText = "تستمع الآن إلى: " + title;
            const audio = document.getElementById('audio-tag');
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
    ydl_opts = {
        'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True,
        'default_search': 'ytsearch5', 'no_warnings': True,
        'cachedir': False
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            results = [{'title': e['title'], 'url': e['url'], 'thumb': e['thumbnail']} for e in info['entries']]
            return jsonify(results)
        except: return jsonify([]), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

