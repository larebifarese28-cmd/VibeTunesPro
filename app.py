import os
import threading
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# تحديد مسار الحفظ (خاص بـ Termux)
DOWNLOAD_PATH = '/sdcard/Music/VibeTunes'
if not os.path.exists(DOWNLOAD_PATH):
    try:
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    except:
        DOWNLOAD_PATH = 'downloads' # مسار احتياطي إذا فشل الوصول للذاكرة
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)

progress_store = {}

def my_hook(d):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%').replace('%','').strip()
        progress_store[d['info_dict']['id']] = p
    elif d['status'] == 'finished':
        progress_store[d['info_dict']['id']] = "100"

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Vibe Tunes Pro | Spotify Style</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            :root { --sp-green: #1DB954; --sp-black: #121212; --sp-card: #181818; }
            * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; font-family: 'Segoe UI', Roboto, sans-serif; }
            body { background: #000; color: white; margin: 0; padding: 15px; overflow-x: hidden; }
            
            /* الهيدر والبحث */
            .header { text-align: center; padding: 20px; font-weight: 900; color: var(--sp-green); font-size: 24px; }
            .search-bar { background: #282828; border-radius: 50px; padding: 12px 20px; display: flex; align-items: center; margin-bottom: 25px; }
            .search-bar input { background: none; border: none; color: white; flex: 1; outline: none; font-size: 15px; }

            /* كروت الأغاني */
            .song-card { background: var(--sp-card); border-radius: 8px; padding: 10px; margin-bottom: 10px; display: flex; align-items: center; transition: 0.2s; }
            .song-card:active { background: #282828; }
            .song-card img { width: 50px; height: 50px; border-radius: 4px; margin-left: 15px; object-fit: cover; }
            .info { flex: 1; text-align: right; overflow: hidden; }
            .info h4 { margin: 0; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .dl-btn { color: var(--sp-green); font-size: 20px; padding: 10px; cursor: pointer; }

            /* المشغل بأسلوب سبوتيفاي الحقيقي */
            #player-ui {
                position: fixed; top: 100%; left: 0; width: 100%; height: 100%;
                background: linear-gradient(to bottom, #404040 0%, #121212 100%);
                z-index: 9999; transition: transform 0.4s cubic-bezier(0.3, 0, 0.2, 1);
                display: flex; flex-direction: column; align-items: center; padding: 20px;
            }
            #player-ui.active { transform: translateY(-100%); }
            .close-btn { align-self: flex-start; font-size: 25px; color: #b3b3b3; padding: 10px; }
            
            /* صورة الأغنية الكبيرة */
            #f-img { 
                width: 85vw; height: 85vw; max-width: 350px; max-height: 350px;
                border-radius: 12px; margin: 40px 0; 
                box-shadow: 0 15px 50px rgba(0,0,0,0.6); object-fit: cover;
            }

            .meta-data { width: 100%; text-align: right; padding: 0 15px; }
            .meta-data h2 { margin: 0; font-size: 22px; font-weight: 800; }
            .meta-data p { color: #b3b3b3; margin: 5px 0; font-size: 15px; }

            /* أزرار التحكم */
            .controls { width: 100%; display: flex; justify-content: space-around; align-items: center; margin-top: 50px; }
            .play-trigger { 
                background: #fff; color: #000; width: 65px; height: 65px; 
                border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 25px; 
            }
        </style>
    </head>
    <body onload="loadInitial()">
        <div class="header">VIBE TUNES PRO</div>
        <div class="search-bar">
            <input type="text" id="q" placeholder="ماذا تريد أن تسمع؟" onkeypress="if(event.key==='Enter') startSearch()">
            <i class="fas fa-search" onclick="startSearch()"></i>
        </div>
        
        <div id="results"></div>

        <div id="player-ui">
            <i class="fas fa-chevron-down close-btn" onclick="closePlayer()"></i>
            <img id="f-img" src="">
            <div class="meta-data">
                <h2 id="f-title">اسم الأغنية</h2>
                <p id="f-artist">YouTube Music</p>
            </div>
            <div class="controls">
                <i class="fas fa-random" style="color:var(--sp-green)"></i>
                <i class="fas fa-step-backward" style="font-size:24px;"></i>
                <div class="play-trigger" onclick="togglePlay()"><i class="fas fa-play" id="f-play-icon"></i></div>
                <i class="fas fa-step-forward" style="font-size:24px;"></i>
                <i class="fas fa-redo"></i>
            </div>
            <audio id="main-audio" onplay="sync(true)" onpause="sync(false)"></audio>
        </div>

        <script>
            let audio = document.getElementById('main-audio');

            function loadInitial() {
                fetch('/api/search?q=' + encodeURIComponent('Top 2026 Hits')).then(r => r.json()).then(render);
            }

            function startSearch() {
                let q = document.getElementById('q').value;
                if(!q) return;
                fetch(`/api/search?q=${encodeURIComponent(q)}`).then(r => r.json()).then(render);
            }

            function render(data) {
                let html = "";
                data.forEach(s => {
                    html += `
                    <div class="song-card" onclick="openAndPlay('${s.id}', '${s.title.replace(/'/g, "")}', '${s.thumb}')">
                        <img src="${s.thumb}">
                        <div class="info"><h4>${s.title}</h4><p style="font-size:12px;color:#b3b3b3">أغنية • YouTube</p></div>
                        <i class="fas fa-download dl-btn" onclick="event.stopPropagation(); downloadSong('${s.id}')" id="dl-${s.id}"></i>
                    </div>`;
                });
                document.getElementById('results').innerHTML = html;
            }

            function openAndPlay(id, title, img) {
                document.getElementById('f-title').innerText = title;
                document.getElementById('f-img').src = img;
                document.getElementById('player-ui').classList.add('active');
                fetch('/api/get_url?id=' + id).then(r => r.json()).then(url => {
                    audio.src = url;
                    audio.play();
                });
            }

            function closePlayer() { document.getElementById('player-ui').classList.remove('active'); }
            function togglePlay() { audio.paused ? audio.play() : audio.pause(); }
            function sync(playing) { document.getElementById('f-play-icon').className = playing ? "fas fa-pause" : "fas fa-play"; }

            function downloadSong(id) {
                const icon = document.getElementById('dl-'+id);
                icon.className = "fas fa-circle-notch fa-spin dl-btn";
                fetch('/api/download?id=' + id).then(() => {
                    let checker = setInterval(() => {
                        fetch('/api/status?id=' + id).then(r => r.json()).then(res => {
                            if(res.progress === "100") {
                                clearInterval(checker);
                                icon.className = "fas fa-check-circle dl-btn";
                            }
                        });
                    }, 2000);
                });
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/api/search')
def search():
    q = request.args.get('q')
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        res = ydl.extract_info(f"ytsearch10:{q}", download=False)
        return jsonify([{'id': e['id'], 'title': e['title'], 'thumb': e['thumbnails'][0]['url']} for e in res['entries']])

@app.route('/api/get_url')
def get_url():
    with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
        return jsonify(ydl.extract_info(request.args.get('id'), download=False)['url'])

@app.route('/api/download')
def download():
    vid_id = request.args.get('id')
    def run_dl():
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_PATH}/%(title)s.%(ext)s',
            'progress_hooks': [my_hook],
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
            'quiet': True
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={vid_id}"])
    threading.Thread(target=run_dl).start()
    return "OK"

@app.route('/api/status')
def status():
    return jsonify({"progress": progress_store.get(request.args.get('id'), "0")})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

