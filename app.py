import os
import threading
import subprocess
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# إعدادات المسار (تخدم في Termux فقط)
DOWNLOAD_PATH = '/sdcard/Music/VibeTunes'
if not os.path.exists(DOWNLOAD_PATH) and 'TERMUX_VERSION' in os.environ:
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
        <title>Vibe Tunes Pro | Official</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            :root { --spotify-green: #1DB954; --bg-black: #121212; --card-bg: #181818; }
            * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body { background: #000; color: white; margin: 0; padding: 15px; }
            
            .header { text-align: center; padding: 25px; font-weight: 900; color: var(--spotify-green); font-size: 28px; letter-spacing: 1px; }
            
            .search-bar { background: var(--bg-black); border-radius: 8px; padding: 14px 20px; display: flex; align-items: center; border: 1px solid #333; margin-bottom: 25px; }
            .search-bar input { background: none; border: none; color: white; flex: 1; outline: none; font-size: 16px; font-weight: 500; }

            .song-card { background: var(--card-bg); border-radius: 10px; padding: 12px; margin-bottom: 12px; display: flex; align-items: center; transition: 0.3s; }
            .song-card:hover { background: #282828; }
            .song-card img { width: 55px; height: 55px; border-radius: 5px; margin-left: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
            
            .info { flex: 1; min-width: 0; cursor: pointer; text-align: right; }
            .info h4 { margin: 0; font-size: 15px; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .info p { margin: 5px 0 0; font-size: 12px; color: #b3b3b3; }

            /* زر تنزيل عصري */
            .dl-btn { background: #333; color: var(--spotify-green); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; border: none; cursor: pointer; transition: 0.3s; }
            .dl-btn:active { transform: scale(0.9); background: var(--spotify-green); color: #000; }

            /* المشغل بأسلوب سبوتيفاي */
            #full-player {
                position: fixed; top: 100%; left: 0; width: 100%; height: 100%;
                background: linear-gradient(to bottom, #2a2a2a, #000);
                z-index: 3000; transition: 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                display: flex; flex-direction: column; align-items: center; padding: 40px 25px;
            }
            #full-player.active { top: 0; }
            .close-icon { align-self: flex-start; font-size: 28px; color: #b3b3b3; margin-bottom: 30px; }
            #f-img { width: 100%; max-width: 320px; aspect-ratio: 1; border-radius: 12px; margin-top: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
            .player-meta { width: 100%; margin-top: 40px; text-align: right; }
            .player-meta h2 { margin: 0; font-size: 22px; font-weight: 900; }
            .player-meta p { color: var(--spotify-green); margin: 5px 0; font-size: 14px; font-weight: 600; }

            .controls { width: 100%; display: flex; justify-content: center; align-items: center; gap: 40px; margin-top: 40px; }
            .play-btn-large { background: #fff; color: #000; width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28px; }

            .mini-player { position: fixed; bottom: 0; left: 0; right: 0; background: #181818; border-top: 1px solid #333; padding: 10px 15px; display: none; z-index: 2000; border-radius: 12px 12px 0 0; }
        </style>
    </head>
    <body>
        <div class="header">VIBE TUNES PRO</div>
        <div class="search-bar">
            <input type="text" id="q" placeholder="ابحث عن أغانيك المفضلة..." onkeypress="if(event.key==='Enter') startSearch()">
            <i class="fas fa-search" style="color:var(--spotify-green)" onclick="startSearch()"></i>
        </div>
        <div id="loader" style="display:none; text-align:center; color:var(--spotify-green); margin-bottom:20px;">🚀 جاري البحث...</div>
        <div id="results"></div>

        <div class="mini-player" id="mini" onclick="openFull()">
            <div style="display:flex; align-items:center;">
                <img id="m-img" src="" style="width:40px; height:40px; border-radius:4px; margin-left:12px;">
                <div class="info"><h4 id="m-title" style="font-size:13px;">...</h4></div>
                <i class="fas fa-play" id="m-play" style="font-size:20px; color:#fff; margin-right:15px;"></i>
            </div>
        </div>

        <div id="full-player">
            <i class="fas fa-chevron-down close-icon" onclick="closeFull()"></i>
            <img id="f-img" src="">
            <div class="player-meta">
                <h2 id="f-title">اسم الأغنية</h2>
                <p>قيد التشغيل الآن</p>
            </div>
            <div class="controls">
                <i class="fas fa-step-backward" style="font-size:25px;"></i>
                <div class="play-btn-large" onclick="togglePlay()"><i class="fas fa-play" id="f-play"></i></div>
                <i class="fas fa-step-forward" style="font-size:25px;"></i>
            </div>
            <audio id="audio" onplay="sync(true)" onpause="sync(false)"></audio>
        </div>

        <script>
            let audio = document.getElementById('audio');
            function startSearch() {
                let q = document.getElementById('q').value;
                if(!q) return;
                document.getElementById('loader').style.display = "block";
                document.getElementById('results').innerHTML = "";
                fetch(`/api/search?q=${encodeURIComponent(q)}`)
                .then(r => r.json()).then(data => {
                    document.getElementById('loader').style.display = "none";
                    data.forEach(s => {
                        document.getElementById('results').innerHTML += `
                        <div class="song-card">
                            <img src="${s.thumb}">
                            <div class="info" onclick="init('${s.id}', '${s.title.replace(/'/g, "")}', '${s.thumb}')">
                                <h4>${s.title}</h4><p>YouTube Music Engine</p>
                            </div>
                            <button class="dl-btn" id="act-${s.id}" onclick="dl('${s.id}')">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>`;
                    });
                });
            }
            function init(id, t, img) {
                document.getElementById('mini').style.display = "block";
                document.getElementById('m-title').innerText = t;
                document.getElementById('f-title').innerText = t;
                document.getElementById('m-img').src = img;
                document.getElementById('f-img').src = img;
                fetch('/api/get_url?id=' + id).then(r => r.json()).then(u => { audio.src = u; audio.play(); });
            }
            function openFull() { document.getElementById('full-player').classList.add('active'); }
            function closeFull() { document.getElementById('full-player').classList.remove('active'); }
            function togglePlay() { audio.paused ? audio.play() : audio.pause(); }
            function sync(p) {
                document.getElementById('m-play').className = p ? "fas fa-pause" : "fas fa-play";
                document.getElementById('f-play').className = p ? "fas fa-pause" : "fas fa-play";
            }
            function dl(id) {
                const btn = document.getElementById('act-'+id);
                btn.innerHTML = "<span style='font-size:10px;'>0%</span>";
                fetch('/api/download?id=' + id);
                let itv = setInterval(() => {
                    fetch('/api/status?id=' + id).then(r => r.json()).then(res => {
                        btn.innerHTML = `<span style='font-size:10px;'>${res.progress}%</span>`;
                        if(res.progress == "100") { clearInterval(itv); btn.innerHTML = "<i class='fas fa-check'></i>"; btn.style.color = "#fff"; }
                    });
                }, 1500);
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/api/search')
def search_api():
    q = request.args.get('q')
    with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
        info = ydl.extract_info(f"ytsearch10:{q}", download=False)
        return jsonify([{'id': e['id'], 'title': e['title'], 'thumb': e['thumbnails'][0]['url']} for e in info['entries']])

@app.route('/api/get_url')
def get_url():
    with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
        return jsonify(ydl.extract_info(request.args.get('id'), download=False)['url'])

@app.route('/api/download')
def download_api():
    vid_id = request.args.get('id')
    def run():
        opts = {'format': 'bestaudio/best', 'outtmpl': f'{DOWNLOAD_PATH}/%(title)s.%(ext)s', 
                'progress_hooks': [my_hook], 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}], 'quiet': True}
        with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([f"https://www.youtube.com/watch?v={vid_id}"])
    threading.Thread(target=run).start()
    return "OK"

@app.route('/api/status')
def status_api():
    return jsonify({"progress": progress_store.get(request.args.get('id'), "0")})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

