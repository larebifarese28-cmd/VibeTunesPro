import os
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# الواجهة اللي تجمع كلش (بحث + نتائج + تحميل + مشغل)
HTML_CODE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Tunes Pro</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background: #000; color: white; font-family: sans-serif; margin: 0; padding: 15px; padding-bottom: 80px; }
        .header { color: #1DB954; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
        
        /* خانة البحث والنتائج في صفحة واحدة */
        .search-box { background: #282828; border-radius: 25px; padding: 12px 20px; display: flex; align-items: center; margin-bottom: 25px; border: 1px solid #333; }
        .search-box input { background: none; border: none; color: white; flex: 1; outline: none; font-size: 16px; }
        
        .song-card { background: #121212; border-radius: 12px; padding: 12px; margin-bottom: 12px; display: flex; align-items: center; border: 1px solid #181818; }
        .song-card img { width: 55px; height: 55px; border-radius: 6px; margin-left: 15px; object-fit: cover; }
        .info { flex: 1; text-align: right; overflow: hidden; }
        .info h4 { margin: 0; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .info p { margin: 5px 0 0; font-size: 11px; color: #1DB954; }

        /* أزرار التحكم والتحميل */
        .actions { display: flex; gap: 15px; align-items: center; }
        .btn-play { color: #1DB954; font-size: 28px; }
        .btn-down { color: #fff; font-size: 20px; text-decoration: none; }

        /* شريط التشغيل السفلي */
        .player-bar { position: fixed; bottom: 0; left: 0; width: 100%; background: #1DB954; color: black; padding: 12px; display: none; align-items: center; justify-content: space-between; font-weight: bold; z-index: 100; }
        #status { text-align: center; color: #1DB954; font-size: 12px; display: none; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="header">VIBE TUNES PRO</div>
    
    <div class="search-box">
        <i class="fas fa-search" style="margin-left:10px; color:#1DB954"></i>
        <input type="text" id="query" placeholder="ابحث عن أغنيتك المفضلة..." onkeypress="if(event.key==='Enter') search()">
    </div>

    <div id="status">🚀 جاري البحث بسرعة البرق...</div>
    <div id="results">
        </div>

    <div id="player-bar" class="player-bar">
        <div style="display:flex; align-items:center; gap:10px;">
            <i class="fas fa-music"></i>
            <span id="current-title" style="font-size:13px;">...</span>
        </div>
        <i class="fas fa-pause" id="play-pause" onclick="toggleAudio()" style="font-size:20px;"></i>
    </div>

    <audio id="main-audio" onplay="updateIcon(true)" onpause="updateIcon(false)"></audio>

    <script>
        const audio = document.getElementById('main-audio');
        
        function search() {
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
                        <div class="song-card">
                            <img src="${s.thumb}">
                            <div class="info">
                                <h4>${s.title}</h4>
                                <p>YouTube Music Engine</p>
                            </div>
                            <div class="actions">
                                <a href="/api/download?id=${s.id}" class="btn-down" title="تحميل"><i class="fas fa-download"></i></a>
                                <i class="fas fa-play-circle btn-play" onclick="playSong('${s.id}', '${s.title.replace(/'/g, "")}')"></i>
                            </div>
                        </div>`;
                    });
                    document.getElementById('results').innerHTML = html;
                });
        }

        function playSong(id, title) {
            document.getElementById('player-bar').style.display = "flex";
            document.getElementById('current-title').innerText = title;
            // جلب الرابط المباشر مع تجاوز الحظر
            fetch('/api/get_url?id=' + id)
                .then(r => r.json())
                .then(url => {
                    audio.src = url;
                    audio.play().catch(e => alert("اضغط على زر التشغيل مرة أخرى للبدء"));
                });
        }

        function toggleAudio() {
            audio.paused ? audio.play() : audio.pause();
        }

        function updateIcon(playing) {
            document.getElementById('play-pause').className = playing ? "fas fa-pause" : "fas fa-play";
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
    query = request.args.get('q')
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        info = ydl.extract_info(f"ytsearch10:{query}", download=False)
        return jsonify([{'id': e['id'], 'title': e['title'], 'thumb': e['thumbnails'][0]['url']} for e in info['entries']])

@app.route('/api/get_url')
def api_url():
    video_id = request.args.get('id')
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        return jsonify(info['url'])

@app.route('/api/download')
def download():
    video_id = request.args.get('id')
    # توجيه المستخدم لرابط التحميل المباشر
    with yt_dlp.YoutubeDL({'format': 'bestaudio'}) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        return jsonify({"download_url": info['url']}) # أو يمكنك تحويله لملف

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

