import os
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# كود HTML اللي يرجع الواجهة كيما كانت مع مشغل مخفي يخدم في الخلفية
HTML_CODE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Tunes Pro</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background: #000; color: white; font-family: sans-serif; margin: 0; padding: 15px; }
        .header { color: #1DB954; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
        .search-box { background: #282828; border-radius: 10px; padding: 12px; display: flex; margin-bottom: 20px; }
        .search-box input { background: none; border: none; color: white; flex: 1; outline: none; }
        .song-card { background: #181818; border-radius: 8px; padding: 10px; margin-bottom: 10px; display: flex; align-items: center; cursor: pointer; }
        .song-card img { width: 60px; height: 60px; border-radius: 5px; margin-left: 15px; }
        .playing-bar { position: fixed; bottom: 0; left: 0; width: 100%; background: #1DB954; color: black; padding: 10px; display: none; justify-content: space-between; align-items: center; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">VIBE TUNES PRO</div>
    <div class="search-box">
        <input type="text" id="q" placeholder="ابحث عن أغنيتك المفضل..." onkeypress="if(event.key==='Enter') search()">
        <i class="fas fa-search" onclick="search()" style="color:#1DB954"></i>
    </div>
    
    <div id="results">
        </div>

    <div id="playing-bar" class="playing-bar">
        <span id="now-playing">جاري التحميل...</span>
        <i class="fas fa-pause" id="ctrl-btn" onclick="toggle()"></i>
    </div>

    <audio id="audio-player"></audio>

    <script>
        let audio = document.getElementById('audio-player');
        function search() {
            let q = document.getElementById('q').value;
            fetch('/api/search?q=' + q).then(r => r.json()).then(data => {
                let h = "";
                data.forEach(s => {
                    h += `<div class="song-card" onclick="play('${s.id}', '${s.title.replace(/'/g,"")}')">
                        <img src="${s.thumb}">
                        <div style="flex:1; text-align:right;">
                            <h4 style="margin:0">${s.title}</h4>
                            <p style="margin:5px 0 0; font-size:12px; color:#b3b3b3;">YouTube Music Engine</p>
                        </div>
                        <i class="fas fa-play-circle" style="font-size:25px; color:#1DB954"></i>
                    </div>`;
                });
                document.getElementById('results').innerHTML = h;
            });
        }
        function play(id, title) {
            document.getElementById('playing-bar').style.display = "flex";
            document.getElementById('now-playing').innerText = title;
            fetch('/api/get_url?id=' + id).then(r => r.json()).then(url => {
                audio.src = url;
                audio.play();
            });
        }
        function toggle() {
            if(audio.paused) { audio.play(); document.getElementById('ctrl-btn').className="fas fa-pause"; }
            else { audio.pause(); document.getElementById('ctrl-btn').className="fas fa-play"; }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_CODE)

@app.route('/api/search')
def api_search():
    q = request.args.get('q')
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        res = ydl.extract_info(f"ytsearch10:{q}", download=False)
        return jsonify([{'id': e['id'], 'title': e['title'], 'thumb': e['thumbnails'][0]['url']} for e in res['entries']])

@app.route('/api/get_url')
def api_url():
    vid_id = request.args.get('id')
    # إعدادات خاصة باش الصوت يمشي ديركت بلا ما يتحظر
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid_id}", download=False)
        return jsonify(info['url'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

