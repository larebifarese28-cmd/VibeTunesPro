import os
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# الواجهة الأصلية: خلفية متدرجة، صور الأغاني، وتصميم عصري
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Tunes Pro V14 | larebifarese28</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: white; font-family: 'Cairo', sans-serif;
            margin: 0; padding: 0; min-height: 100vh;
        }
        .header { padding: 30px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .container { max-width: 700px; margin: auto; padding: 20px; }
        .search-area { position: sticky; top: 0; background: rgba(15, 12, 41, 0.9); padding: 15px; border-radius: 0 0 20px 20px; z-index: 1000; }
        input { width: 100%; padding: 15px; border-radius: 30px; border: none; background: rgba(255,255,255,0.1); color: white; outline: none; font-size: 16px; box-sizing: border-box; }
        button#search-btn { position: absolute; left: 25px; top: 22px; background: #ff4b2b; border: none; color: white; padding: 8px 20px; border-radius: 20px; cursor: pointer; }
        .result-card { background: rgba(255,255,255,0.05); margin-top: 15px; padding: 15px; border-radius: 15px; display: flex; align-items: center; gap: 15px; transition: 0.3s; }
        .result-card:hover { background: rgba(255,255,255,0.1); transform: scale(1.02); }
        .thumb { width: 80px; height: 80px; border-radius: 10px; object-fit: cover; }
        .info { flex: 1; }
        .title { font-weight: bold; font-size: 14px; margin-bottom: 5px; }
        .play-btn { background: #00d2ff; border: none; color: white; padding: 10px; border-radius: 50%; cursor: pointer; width: 40px; height: 40px; }
        .player-bar { position: fixed; bottom: 0; width: 100%; background: rgba(0,0,0,0.9); padding: 15px; display: none; border-top: 2px solid #ff4b2b; }
        audio { width: 100%; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Vibe <span style="color:#ff4b2b">Tunes</span> Pro</h1>
        <p style="font-size: 12px; opacity: 0.7;">بواسطة: larebifarese28-cmd</p>
    </div>

    <div class="container">
        <div class="search-area">
            <input type="text" id="query" placeholder="ابحث عن أغنيتك المفضلة...">
            <button id="search-btn" onclick="searchMusic()">بحث</button>
        </div>
        <div id="loader" style="display:none; text-align:center; margin-top:20px;">🚀 جاري استخراج الموسيقى...</div>
        <div id="results"></div>
    </div>

    <div id="player-bar" class="player-bar">
        <div id="playing-title" style="font-size: 12px; margin-bottom: 10px; text-align: center;"></div>
        <audio id="main-audio" controls autoplay></audio>
    </div>

    <script>
        async function searchMusic() {
            const query = document.getElementById('query').value;
            const results = document.getElementById('results');
            const loader = document.getElementById('loader');
            if(!query) return;

            loader.style.display = 'block';
            results.innerHTML = '';

            const res = await fetch(`/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            
            loader.style.display = 'none';
            data.forEach(item => {
                results.innerHTML += `
                    <div class="result-card">
                        <img src="${item.thumb}" class="thumb">
                        <div class="info">
                            <div class="title">${item.title}</div>
                            <div style="font-size: 10px; opacity: 0.5;">YouTube Music</div>
                        </div>
                        <button class="play-btn" onclick="play('${item.url}', '${item.title.replace(/'/g, "")}')">▶</button>
                    </div>
                `;
            });
        }

        function play(url, title) {
            document.getElementById('player-bar').style.display = 'block';
            document.getElementById('playing-title').innerText = "تشغيل: " + title;
            const audio = document.getElementById('main-audio');
            audio.src = url;
            audio.play();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/search')
def search():
    query = request.args.get('q')
    ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch10'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch10:{query}", download=False)
        return jsonify([{'title': e['title'], 'url': e['url'], 'thumb': e['thumbnail']} for e in info['entries']])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

