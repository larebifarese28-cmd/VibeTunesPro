import os
from flask import Flask, render_template_string, request, jsonify, Response
import yt_dlp
import requests

app = Flask(__name__)

# واجهة المستخدم مدمجة (البحث + النتائج + زر التحميل)
HTML_CODE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Tunes Pro</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background: #000; color: white; font-family: sans-serif; margin: 0; padding: 15px; padding-bottom: 100px; }
        .header { color: #1DB954; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
        .search-box { background: #282828; border-radius: 25px; padding: 12px 20px; display: flex; align-items: center; margin-bottom: 25px; }
        .search-box input { background: none; border: none; color: white; flex: 1; outline: none; font-size: 16px; text-align: right; }
        .song-card { background: #121212; border-radius: 12px; padding: 12px; margin-bottom: 12px; display: flex; align-items: center; border: 1px solid #181818; }
        .song-card img { width: 55px; height: 55px; border-radius: 6px; margin-left: 15px; }
        .info { flex: 1; text-align: right; }
        .info h4 { margin: 0; font-size: 14px; }
        .actions { display: flex; gap: 20px; align-items: center; }
        .btn-play { color: #1DB954; font-size: 30px; cursor: pointer; }
        .btn-down { color: #fff; font-size: 22px; text-decoration: none; }
        .player-bar { position: fixed; bottom: 0; left: 0; width: 100%; background: #1DB954; color: black; padding: 15px; display: none; align-items: center; justify-content: space-between; }
    </style>
</head>
<body>
    <div class="header">VIBE TUNES PRO</div>
    <div class="search-box">
        <input type="text" id="query" placeholder="ابحث عن أغنيتك المفضلة..." onkeypress="if(event.key==='Enter') search()">
        <i class="fas fa-search" style="color:#1DB954; cursor:pointer;" onclick="search()"></i>
    </div>
    <div id="results"></div>

    <div id="player-bar" class="player-bar">
        <span id="playing-title">جاري التحغيل...</span>
        <i class="fas fa-pause" id="p-icon" onclick="toggle()" style="cursor:pointer; font-size:24px;"></i>
    </div>

    <audio id="audio"></audio>

    <script>
        const audio = document.getElementById('audio');
        function search() {
            const q = document.getElementById('query').value;
            if(!q) return;
            document.getElementById('results').innerHTML = "<p style='text-align:center;'>جاري البحث...</p>";
            fetch('/api/search?q=' + encodeURIComponent(q)).then(r => r.json()).then(data => {
                let h = "";
                data.forEach(s => {
                    h += `<div class="song-card">
                        <img src="${s.thumb}">
                        <div class="info"><h4>${s.title}</h4><p style="color:#1DB954; font-size:10px;">YouTube Music</p></div>
                        <div class="actions">
                            <a href="/api/download?id=${s.id}" class="btn-down"><i class="fas fa-cloud-download-alt"></i></a>
                            <i class="fas fa-play-circle btn-play" onclick="playSong('${s.id}', '${s.title}')"></i>
                        </div>
                    </div>`;
                });
                document.getElementById('results').innerHTML = h;
            });
        }
        function playSong(id, title) {
            document.getElementById('player-bar').style.display = "flex";
            document.getElementById('playing-title').innerText = title;
            // استخدام البروكسي لتجاوز قيود الصوت
            audio.src = '/api/stream?id=' + id;
            audio.play();
        }
        function toggle() {
            const icon = document.getElementById('p-icon');
            if(audio.paused) { audio.play(); icon.className = "fas fa-pause"; }
            else { audio.pause(); icon.className = "fas fa-play"; }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_CODE)

@app.route('/api/search')
def api_search():
    q = request.args.get('q')
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        res = ydl.extract_info(f"ytsearch10:{q}", download=False)
        return jsonify([{'id': e['id'], 'title': e['title'], 'thumb': e['thumbnails'][0]['url']} for e in res['entries']])

@app.route('/api/stream')
def stream():
    video_id = request.args.get('id')
    with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        # ميزة البروكسي: جلب البيانات وتمريرها مباشرة للمتصفح لتشغيل الصوت
        return Response(requests.get(info['url'], stream=True).iter_content(chunk_size=1024), content_type="audio/mpeg")

@app.route('/api/download')
def download():
    video_id = request.args.get('id')
    with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        # التحميل عبر رابط مباشر
        return Response(requests.get(info['url'], stream=True).iter_content(chunk_size=1024), 
                        headers={"Content-Disposition": f"attachment; filename={video_id}.mp3"})

if __name__ == '__main__':
    # دعم بورت Render وتثبيته محلياً على 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

