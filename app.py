import os
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# التصميم الفخم الذي طلبته (Modern Dark UI)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Tunes Pro V14 | larebifarese28</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #ff4b2b; --bg: #0a0a0a; --card: #1a1a1a; --text: #ffffff; }
        body { background-color: var(--bg); color: var(--text); font-family: 'Tajawal', sans-serif; margin: 0; padding: 0; }
        .header { padding: 40px 20px; text-align: center; background: linear-gradient(to bottom, #1a1a1a, #0a0a0a); border-bottom: 2px solid var(--primary); }
        .container { max-width: 800px; margin: auto; padding: 20px; }
        .search-box { position: sticky; top: 10px; z-index: 100; display: flex; gap: 10px; margin-bottom: 30px; }
        input { flex: 1; padding: 15px; border-radius: 12px; border: 1px solid #333; background: #1a1a1a; color: white; outline: none; font-size: 16px; }
        button { padding: 15px 25px; border-radius: 12px; border: none; background: var(--primary); color: white; cursor: pointer; font-weight: bold; transition: 0.3s; }
        button:hover { transform: scale(1.05); opacity: 0.9; }
        .track-card { background: var(--card); padding: 15px; margin-bottom: 15px; border-radius: 15px; display: flex; align-items: center; gap: 15px; border: 1px solid #222; }
        .track-info { flex: 1; }
        .track-title { font-weight: bold; font-size: 16px; color: var(--primary); margin-bottom: 5px; }
        .player-container { position: fixed; bottom: 0; left: 0; width: 100%; background: #111; padding: 15px; border-top: 2px solid var(--primary); display: none; }
        audio { width: 100%; }
        .loader { display: none; color: var(--primary); margin: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Vibe <span style="color:var(--primary)">Tunes</span> Pro</h1>
        <p>النسخة النهائية V14 - استمتع بموسيقاك</p>
    </div>

    <div class="container">
        <div class="search-box">
            <input type="text" id="query" placeholder="ابحث عن أغنية أو فنان...">
            <button onclick="searchMusic()">ابحث</button>
        </div>
        
        <div id="loader" class="loader">جاري البحث في السحابة... 🚀</div>
        <div id="results"></div>
    </div>

    <div id="player" class="player-container">
        <div id="now-playing" style="font-size: 12px; margin-bottom: 5px; text-align: center;"></div>
        <audio id="audio-player" controls></audio>
    </div>

    <script>
        async function searchMusic() {
            const query = document.getElementById('query').value;
            const resultsDiv = document.getElementById('results');
            const loader = document.getElementById('loader');
            
            if (!query) return;
            
            loader.style.display = 'block';
            resultsDiv.innerHTML = '';
            
            try {
                const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                loader.style.display = 'none';
                data.forEach(track => {
                    const card = document.createElement('div');
                    card.className = 'track-card';
                    card.innerHTML = `
                        <div class="track-info">
                            <div class="track-title">${track.title}</div>
                        </div>
                        <button onclick="playTrack('${track.url}', '${track.title.replace(/'/g, "\\'")}')">تشغيل</button>
                    `;
                    resultsDiv.appendChild(card);
                });
            } catch (e) {
                loader.innerText = 'حدث خطأ في الاتصال بالسيرفر';
            }
        }

        function playTrack(url, title) {
            const playerContainer = document.getElementById('player');
            const audioPlayer = document.getElementById('audio-player');
            const nowPlaying = document.getElementById('now-playing');
            
            playerContainer.style.display = 'block';
            nowPlaying.innerText = "تشغيل الآن: " + title;
            audioPlayer.src = url;
            audioPlayer.play();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search')
def search():
    query = request.args.get('q')
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch8',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch8:{query}", download=False)
            results = [{'title': e['title'], 'url': e['url']} for e in info['entries']]
            return jsonify(results)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

