"""
YouTube Shorts Uploader - Local Web App
유튜브 Shorts 업로드 관리 프로그램
"""
import os
import json
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Google API
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
DATA_FILE = "videos.json"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 업로드 상태 저장
upload_status = {}


def load_videos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_videos(videos):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)


def get_youtube_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return build("youtube", "v3", credentials=creds)


def do_upload(video_id, filepath, title, description, tags, privacy):
    """실제 업로드 실행 (백그라운드)"""
    global upload_status
    try:
        upload_status[video_id] = {"status": "uploading", "progress": 0, "message": "업로드 시작"}
        
        youtube = get_youtube_service()
        if not youtube:
            upload_status[video_id] = {"status": "error", "message": "인증 실패. client_secret.json을 확인하세요."}
            return
        
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }
        
        media = MediaFileUpload(filepath, mimetype="video/mp4", resumable=True, chunksize=1024*1024)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                upload_status[video_id]["progress"] = progress
                upload_status[video_id]["message"] = f"업로드 중... {progress}%"
        
        yt_id = response["id"]
        upload_status[video_id] = {
            "status": "done",
            "progress": 100,
            "message": "완료",
            "youtube_id": yt_id,
            "url": f"https://youtu.be/{yt_id}",
            "shorts_url": f"https://youtube.com/shorts/{yt_id}"
        }
        
        # 데이터 파일 업데이트
        videos = load_videos()
        for v in videos:
            if v["id"] == video_id:
                v["status"] = "done"
                v["youtube_id"] = yt_id
                v["url"] = f"https://youtu.be/{yt_id}"
                break
        save_videos(videos)
        
    except Exception as e:
        upload_status[video_id] = {"status": "error", "message": str(e)}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/videos', methods=['GET'])
def get_videos():
    return jsonify(load_videos())


@app.route('/api/videos', methods=['POST'])
def add_video():
    if 'video' not in request.files:
        return jsonify({"error": "파일이 없습니다"}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "파일명이 없습니다"}), 400
    
    filename = secure_filename(file.filename)
    # 한글 파일명 지원을 위해 타임스탬프 추가
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_name = f"{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
    file.save(filepath)
    
    video = {
        "id": timestamp,
        "filename": filename,
        "filepath": filepath,
        "title": request.form.get('title', filename),
        "description": request.form.get('description', ''),
        "tags": [t.strip() for t in request.form.get('tags', '').split(',') if t.strip()],
        "privacy": request.form.get('privacy', 'public'),
        "status": "ready",
        "created_at": datetime.now().isoformat()
    }
    
    videos = load_videos()
    videos.append(video)
    save_videos(videos)
    
    return jsonify(video)


@app.route('/api/upload/<video_id>', methods=['POST'])
def upload_video(video_id):
    videos = load_videos()
    video = next((v for v in videos if v["id"] == video_id), None)
    
    if not video:
        return jsonify({"error": "영상을 찾을 수 없습니다"}), 404
    
    # 백그라운드에서 업로드
    thread = threading.Thread(
        target=do_upload,
        args=(video_id, video["filepath"], video["title"], video["description"], video["tags"], video["privacy"])
    )
    thread.start()
    
    return jsonify({"message": "업로드 시작됨"})


@app.route('/api/status/<video_id>')
def get_status(video_id):
    return jsonify(upload_status.get(video_id, {"status": "unknown"}))


@app.route('/api/auth/status')
def auth_status():
    has_secret = os.path.exists(CLIENT_SECRET_FILE)
    has_token = os.path.exists(TOKEN_FILE)
    return jsonify({
        "has_client_secret": has_secret,
        "has_token": has_token,
        "ready": has_secret and has_token
    })


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    try:
        youtube = get_youtube_service()
        if youtube:
            return jsonify({"success": True, "message": "인증 완료"})
        else:
            return jsonify({"success": False, "message": "client_secret.json이 필요합니다"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


if __name__ == '__main__':
    print("=" * 50)
    print("YouTube Shorts Uploader")
    print("브라우저에서 http://localhost:5000 접속")
    print("=" * 50)
    app.run(debug=True, port=5000)
