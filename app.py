import os
import threading
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# مسار الحفظ لـ Termux
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
        <title>Vibe Tunes Pro</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            :root { --green: #1DB954; --dark: #121212; --card: #181818; }
            * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
            body { background: #000; color: white; font-family: sans-serif; margin: 0; padding: 15px; }
            .header { text-align: center; padding: 20px; font-weight: 900; color: var(--green); font-size: 26px; }
            .search-bar { background: var(--dark); border-radius: 10px; padding: 12px 18px; display: flex; align-items: center; border: 1px solid #333; margin-bottom: 20px; }
            .search-bar input { background: none; border: none; color: white; flex: 1; outline: none; font-size: 16px; text-align: right; }
            
            .song-card { background: var(--card); border-radius: 12px; padding: 12px; margin-bottom: 12px; display: flex; align-items: center; cursor: pointer; border: 1px solid transparent; transition: 0.2s; }
            .song-card:active { background: #282828; border-color: var(--green); }
            .song-card img { width: 55px; height: 55px; border-radius: 8px; margin-left: 15px; }
            .info { flex: 1; min-width: 0; text-align: right; }
            .info h4 { margin: 0; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .dl-icon { color: var(--green); font-size: 22px; padding: 10px; z-index: 10; }

            #full-player { position: fixed; top: 100%; left: 0; width: 100%; height: 100%; background: linear-gradient(to bottom, #222, #000); z-index: 3000; transition: 0.4s ease; padding: 40px 25px; text-align: center; }
            #full-player.active { top: 0; }
            #f-img { width: 100%; max-width: 300px; border-radius: 15px; box-shadow: 0 15px 40px rgba(0,0,0,0.7); margin: 30px 0; }
            .controls { display: flex; justify-content: center; align-items: center; gap: 40px; margin-top: 30px; }
            .play-main { background: white; color: black; width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28px; }
        </style>
    </head>
    <body onload="suggested()">
        <div class="header">VIBE TUNES PRO</div>
        <div class="search-bar">
            <input type="text" id="q" placeholder="ابحث عن أغانيك المفضلة..." onkeypress="if(event.key==='Enter') startSearch()">
            <i class="fas fa-search" style="color:var(--green)" onclick="startSearch()"></i>
        </div>
        <div id="loader" style="display:none; text-align:center; color:var(--green); margin:10px;">🚀 جاري الاستخراج...</div>
        <div id="results"></div>

        <div id="full-player">
            <i class="fas fa-chevron-down" style="font-size:30px; color:#777;" onclick="closeFull()"></i><br>
            <img id="f-img" src="">
            <h2 id="f-title" style="margin:20px 0 5px;">...</h2>
            <p style="color:var(--green); font-weight:bold;">قيد التشغيل الآن</p>
            <div class="controls">
                <i class="fas fa-step-backward" style="font-size:25px;"></i>
                <div class="play-main" onclick="togglePlay()"><i class="fas fa-play" id="f-play"></i></div>
                <i class="fas fa-step-forward" style="font-size:25px;"></i>
            </div>
            <audio id="audio" onplay="sync(true)" onpause="sync(false)"></audio>
        </div>

        <script>
            let audio = document.getElementById('audio');

            function suggested() {
                // عرض أغاني مقترحة تلقائياً عند الدخول
                fetch('/api/search?q=' + encodeURIComponent('Top Algeria Music 2026')).then(r => r.json()).then(render);
            }

            function startSearch() {
                let q = document.getElementById('q').value;
                if(!q) return;
                document.getElementById('loader').style.display = "block";
                fetch(`/api/search?q=${encodeURIComponent(q)}`).then(r => r.json()).then(data => {
                    document.getElementById('loader').style.display = "none";
                    render(data);
                });
            }

            function render(data) {
                let h = "";
                data.forEach(s => {
                    h += `<div class="song-card" onclick="init('${s.id}', '${s.title.replace(/'/g, "")}', '${s.thumb}')">
                        <img src="${s.thumb}">
                        <div class="info"><h4>${s.title}</h4><p style="font-size:11px;color:#888">YouTube Music Engine</p></div>
                        <i class="fas fa-arrow-circle-down dl-icon" onclick="event.stopPropagation(); dl('${s.id}')" id="btn-${s.id}"></i>
                    </div>`;
                });
                document.getElementById('results').innerHTML = h;
            }

            function init(id, t, img) {
                document.getElementById('f-title').innerText = t;
                document.getElementById('f-img').src = img;
                openFull();
                fetch('/api/get_url?id=' + id).then(r => r.json()).then(u => { audio.src = u; audio.play(); });
            }

            function openFull() { document.getElementById('full-player').classList.add('active'); }
            function closeFull() { document.getElementById('full-player').classList.remove('active'); }
            function togglePlay() { audio.paused ? audio.play() : audio.pause(); }
            function sync(p) { document.getElementById('f-play').className = p ? "fas fa-pause" : "fas fa-play"; }

            function dl(id) {
                const btn = document.getElementById('btn-'+id);
                btn.className = "fas fa-spinner fa-spin dl-icon";
                fetch('/api/download?id=' + id);
                let itv = setInterval(() => {
                    fetch('/api/status?id=' + id).then(r => r.json()).then(res => {
                        if(res.progress == "100") { clearInterval(itv); btn.className = "fas fa-check-circle dl-icon"; }
                    });
                }, 2000);
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
    with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
        return jsonify(ydl.extract_info(request.args.get('id'), download=False)['url'])

@app.route('/api/download')
def download_api():
    vid_id = request.args.get('id')
    def run():
        opts = {'format': 'bestaudio/best', 'outtmpl': f'{DOWNLOAD_PATH}/%(title)s.%(ext)s', 'progress_hooks': [my_hook], 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}], 'quiet': True}
        with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([f"https://www.youtube.com/watch?v={vid_id}"])
    threading.Thread(target=run).start()
    return "OK"

@app.route('/api/status')
def status_api():
    return jsonify({"progress": progress_store.get(request.args.get('id'), "0")})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

