import os
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# إعدادات لتجاوز حظر الصوت في المتصفحات
@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# واجهة المستخدم (Spotify Style)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Vibe Tunes Pro</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root { --sp-green: #1DB954; --bg-black: #000; --card-bg: #181818; }
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { background: var(--bg-black); color: white; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 15px; }
        
        .header { text-align: center; padding: 15px; color: var(--sp-green); font-size: 22px; font-weight: bold; }
        .search-box { background: #282828; border-radius: 50px; padding: 10px 20px; display: flex; align-items: center; margin-bottom: 20px; }
        .search-box input { background: none; border: none; color: white; flex: 1; outline: none; font-size: 16px; }

        .song-item { background: var(--card-bg); border-radius: 8px; padding: 10px; margin-bottom: 10px; display: flex; align-items: center; transition: 0.3s; }
        .song-item:active { background: #282828; }
        .song-item img { width: 50px; height: 50px; border-radius: 4px; margin-left: 15px; object-fit: cover; }
        .song-info { flex: 1; text-align: right; overflow: hidden; }
        .song-info h4 { margin: 0; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .song-info p { margin: 3px 0 0; font-size: 11px; color: #b3b3b3; }

        /* المشغل الكامل */
        #player-overlay { 
            position: fixed; top: 100%; left: 0; width: 100%; height: 100%; 
            background: linear-gradient(to bottom, #333 0%, #000 100%); 
            z-index: 9999; transition: 0.4s cubic-bezier(0.3, 0, 0.2, 1); 
            display: flex; flex-direction: column; align-items: center; padding: 20px;
        }
        #player-overlay.active { top: 0; }
        .close-btn { align-self: flex-start; font-size: 24px; color: #b3b3b3; padding: 10px; }
        #f-img { width: 85vw; height: 85vw; max-width: 320px; border-radius: 12px; margin: 40px 0; box-shadow: 0 10px 40px rgba(0,0,0,0.6); }
        .meta { width: 100%; text-align: right; padding: 0 15px; }
        .meta h2 { margin: 0; font-size: 20px; }
        .meta p { color: var(--sp-green); font-weight: bold; margin-top: 5px; }

        .controls { width: 100%; display: flex; justify-content: space-evenly; align-items: center; margin-top: 50px; }
        .play-main { background: white; color: black; width: 65px; height: 65px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28px; }
        
        #status { text-align: center; color: var(--sp-green); font-size: 12px; margin-bottom: 10px; display: none; }
    </style>
</head>
<body>
    <div class="header">VIBE TUNES PRO</div>
    <div class="search-box">
        <input type="text" id="query" placeholder="ماذا تريد أن تسمع؟" onkeypress="if(event.key==='Enter') doSearch()">
        <i class="fas fa-search" onclick="doSearch()"></i>
    </div>
    <div id="status">🚀 جاري التحميل...</div>
    <div id="results"></div>

    <div id="player-overlay">
        <i class="fas fa-chevron-down close-btn" onclick="togglePlayer(false)"></i>
        <img id="f-img" src="">
        <div class="meta">
            <h2 id="f-title">...</h2>
            <p>قيد التشغيل الآن</p>
        </div>
        <div class="controls">
            <i class="fas fa-random" style="color:var(--sp-green)"></i>
            <i class="fas fa-step-backward" style="font-size:24px;"></i>
            <div class="play-main" onclick="toggleAudio()"><i class="fas fa-play" id="p-icon"></i></div>
            <i class="fas fa-step-forward" style="font-size:24px;"></i>
            <i class="fas fa-redo"></i>
        </div>
        <audio id="main-audio" onplay="syncUI(true)" onpause="syncUI(false)"></audio>
    </div>

    <script>
        const audio = document.getElementById('main-audio');

        function doSearch() {
            const q = document.getElementById('query').value;
            if(!q) return;
            document.getElementById('status').style.display = "block";
            fetch('/api/search?q=' + encodeURIComponent(q))
                .then(r => r.json())
                .then(data => {
                    document.getElementById('status').style.display = "none";
                    let html = "";
                    data.forEach(s => {
                        html += `
                        <div class="song-item" onclick="initPlayer('${s.id}', '${s.title.replace(/'/g, "")}', '${s.thumb}')">
                            <img src="${s.thumb}">
                            <div class="song-info"><h4>${s.title}</h4><p>أغنية • YouTube Music</p></div>
                        </div>`;
                    });
                    document.getElementById('results').innerHTML = html;
                });
        }

        function initPlayer(id, title, img) {
            document.getElementById('f-title').innerText = title;
            document.getElementById('f-img').src = img;
            togglePlayer(true);
            fetch('/api/get_url?id=' + id)
                .then(r => r.json())
                .then(url => {
                    audio.src = url;
                    audio.play();
                });
        }

        function togglePlayer(show) {
            document.getElementById('player-overlay').classList.toggle('active', show);
        }

        function toggleAudio() {
            audio.paused ? audio.play() : audio.pause();
        }

        function syncUI(playing) {
            document.getElementById('p-icon').className = playing ? "fas fa-pause" : "fas fa-play";
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/search')
def api_search():
    query = request.args.get('q')
    ydl_opts = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch10:{query}", download=False)
        return jsonify([{'id': e['id'], 'title': e['title'], 'thumb': e['thumbnails'][0]['url']} for e in info['entries']])

@app.route('/api/get_url')
def api_url():
    video_id = request.args.get('id')
    # إعدادات خاصة لتجاوز حظر التشغيل المباشر
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        return jsonify(info['url'])

if __name__ == '__main__':
    # تشغيل السيرفر على الشبكة المحلية لـ Termux
    app.run(host='0.0.0.0', port=5000)

