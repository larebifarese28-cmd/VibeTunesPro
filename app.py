import os
import threading
import subprocess
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# مسار الحفظ (يشتغل في Termux فقط، وفي Render يتم تجاهله)
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
        file_path = d.get('info_dict').get('_filename')
        if file_path and 'TERMUX_VERSION' in os.environ:
            subprocess.run(['termux-media-scan', file_path])

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
            * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
            body { background: #000; color: white; font-family: sans-serif; margin: 0; padding: 15px; }
            .header { text-align: center; padding: 20px; font-weight: 900; color: #1DB954; font-size: 26px; }
            .search-bar { background: #121212; border-radius: 50px; padding: 12px 20px; display: flex; align-items: center; border: 1px solid #333; margin-bottom: 20px; }
            .search-bar input { background: none; border: none; color: white; flex: 1; outline: none; font-size: 16px; }
            .song-card { background: #181818; border-radius: 12px; padding: 12px; margin-bottom: 12px; display: flex; align-items: center; border: 1px solid transparent; }
            .song-card:active { border-color: #1DB954; background: #282828; }
            .song-card img { width: 60px; height: 60px; border-radius: 8px; margin-left: 15px; }
            .info { flex: 1; min-width: 0; cursor: pointer; text-align: right; }
            .info h4 { margin: 0; font-size: 14px; color: #fff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            .mini-player { position: fixed; bottom: 0; left: 0; right: 0; background: #121212; border-top: 2px solid #1DB954; padding: 12px 20px; z-index: 2000; display: none; }
            #full-player { position: fixed; top: 100%; left: 0; width: 100%; height: 100%; background: #000; z-index: 3000; transition: 0.5s; padding: 40px 25px; text-align: center; }
            #full-player.active { top: 0; }
            #f-img { width: 300px; height: 300px; border-radius: 20px; margin-top: 50px; box-shadow: 0 10px 30px rgba(29,185,84,0.3); }
            .play-circle { background: #fff; color: #000; width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 30px; margin: 30px auto; }
        </style>
    </head>
    <body>
        <div class="header">VIBE TUNES PRO</div>
        <div class="search-bar">
            <input type="text" id="q" placeholder="ابحث عن أغاني، فنانين..." onkeypress="if(event.key==='Enter') startSearch()">
            <i class="fas fa-search" style="color:#1DB954" onclick="startSearch()"></i>
        </div>
        <div id="loader" style="display:none; text-align:center; color:#1DB954; margin:20px;">🚀 جاري استخراج الموسيقى...</div>
        <div id="results"></div>

        <div class="mini-player" id="mini" onclick="openFull()">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <img id="m-img" src="" style="width:45px; height:45px; border-radius:6px; margin-left:12px;">
                <div class="info"><h4 id="m-title">...</h4></div>
                <i class="fas fa-play" id="m-play" style="font-size:22px; color:#1DB954;"></i>
            </div>
        </div>

        <div id="full-player">
            <i class="fas fa-chevron-down" style="font-size:30px; color:#555;" onclick="closeFull()"></i><br>
            <img id="f-img" src="">
            <h2 id="f-title" style="margin-top:30px;">...</h2>
            <div class="play-circle" onclick="togglePlay()"><i class="fas fa-play" id="f-play"></i></div>
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
                                <h4>${s.title}</h4><p style="font-size:11px; color:#666;">High Quality MP3</p>
                            </div>
                            <div id="act-${s.id}"><i class="fas fa-cloud-download-alt" style="color:#1DB954; font-size:24px" onclick="dl('${s.id}')"></i></div>
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
                const box = document.getElementById('act-'+id);
                box.innerHTML = "<span id='p-"+id+"' style='color:#1DB954'>0%</span>";
                fetch('/api/download?id=' + id);
                let itv = setInterval(() => {
                    fetch('/api/status?id=' + id).then(r => r.json()).then(res => {
                        document.getElementById('p-'+id).innerText = res.progress + "%";
                        if(res.progress == "100") { clearInterval(itv); box.innerHTML = "✅"; }
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

