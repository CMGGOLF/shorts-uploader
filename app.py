from flask import Flask, render_template, request, jsonify
import os
import json
import requests
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import threading

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
upload_status = {}

def load_instagram_config():
    try:
        with open('instagram_config.json', 'r') as f:
            return json.load(f)
    except:
        return None

def get_youtube_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('client_secret.json'):
                return None
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def upload_to_youtube(video_id, filepath, title, description, tags, privacy, schedule_time=None):
    try:
        creds = get_youtube_credentials()
        if not creds:
            upload_status[video_id]['youtube'] = {'status': 'error', 'message': 'YouTube 인증 필요'}
            return
        
        youtube = build('youtube', 'v3', credentials=creds)
        
        status_body = {
            'privacyStatus': 'private' if schedule_time else privacy,
            'selfDeclaredMadeForKids': False
        }
        
        if schedule_time:
            status_body['publishAt'] = schedule_time
            status_body['privacyStatus'] = 'private'
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags.split(',') if tags else [],
                'categoryId': '22'
            },
            'status': status_body
        }
        
        media = MediaFileUpload(filepath, chunksize=1024*1024, resumable=True)
        request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                upload_status[video_id]['youtube']['progress'] = progress
        
        result = {
            'status': 'completed',
            'video_id': response['id'],
            'url': f"https://youtube.com/shorts/{response['id']}"
        }
        if schedule_time:
            result['scheduled'] = schedule_time
            result['status'] = 'scheduled'
        
        upload_status[video_id]['youtube'] = result
    except Exception as e:
        upload_status[video_id]['youtube'] = {'status': 'error', 'message': str(e)}

def upload_to_instagram(video_id, filepath, caption, schedule_time=None):
    try:
        config = load_instagram_config()
        if not config:
            upload_status[video_id]['instagram'] = {'status': 'error', 'message': 'Instagram 설정 필요'}
            return
        
        access_token = config['access_token']
        ig_account_id = config['instagram_account_id']
        
        upload_status[video_id]['instagram']['progress'] = 10
        
        init_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/media"
        init_params = {
            'media_type': 'REELS',
            'upload_type': 'resumable',
            'caption': caption,
            'access_token': access_token
        }
        
        if schedule_time:
            init_params['scheduled_publish_time'] = schedule_time
        
        init_response = requests.post(init_url, data=init_params)
        init_data = init_response.json()
        
        if 'id' not in init_data:
            upload_status[video_id]['instagram'] = {'status': 'error', 'message': init_data.get('error', {}).get('message', 'Container 생성 실패')}
            return
        
        container_id = init_data['id']
        upload_url = init_data.get('uri', f"https://rupload.facebook.com/ig-api-upload/v18.0/{container_id}")
        
        upload_status[video_id]['instagram']['progress'] = 30
        
        file_size = os.path.getsize(filepath)
        with open(filepath, 'rb') as video_file:
            headers = {
                'Authorization': f'OAuth {access_token}',
                'offset': '0',
                'file_size': str(file_size)
            }
            upload_response = requests.post(upload_url, headers=headers, data=video_file)
        
        upload_status[video_id]['instagram']['progress'] = 70
        
        publish_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish"
        publish_params = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        publish_response = requests.post(publish_url, data=publish_params)
        publish_data = publish_response.json()
        
        if 'id' in publish_data:
            result = {
                'status': 'scheduled' if schedule_time else 'completed',
                'media_id': publish_data['id'],
                'url': f"https://instagram.com/reel/{publish_data['id']}"
            }
            if schedule_time:
                result['scheduled'] = schedule_time
            upload_status[video_id]['instagram'] = result
        else:
            upload_status[video_id]['instagram'] = {'status': 'error', 'message': publish_data.get('error', {}).get('message', '게시 실패')}
            
    except Exception as e:
        upload_status[video_id]['instagram'] = {'status': 'error', 'message': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth/status')
def auth_status():
    youtube_auth = os.path.exists('token.json') and os.path.exists('client_secret.json')
    instagram_auth = load_instagram_config() is not None
    return jsonify({
        'youtube': youtube_auth,
        'instagram': instagram_auth
    })

@app.route('/api/videos', methods=['GET'])
def get_videos():
    return jsonify(upload_status)

@app.route('/api/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': '영상 파일 필요'}), 400
    
    file = request.files['video']
    title = request.form.get('title', 'Untitled')
    description = request.form.get('description', '')
    tags = request.form.get('tags', '')
    privacy = request.form.get('privacy', 'public')
    platforms = request.form.getlist('platforms')
    schedule_date = request.form.get('schedule_date', '')
    schedule_time = request.form.get('schedule_time', '')
    
    if not platforms:
        platforms = ['youtube']
    
    schedule_datetime = None
    if schedule_date and schedule_time:
        schedule_datetime = f"{schedule_date}T{schedule_time}:00+09:00"
    
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    video_id = str(len(upload_status) + 1)
    upload_status[video_id] = {
        'filename': filename,
        'title': title,
        'platforms': platforms,
        'scheduled': schedule_datetime
    }
    
    if 'youtube' in platforms:
        upload_status[video_id]['youtube'] = {'status': 'uploading', 'progress': 0}
        thread = threading.Thread(target=upload_to_youtube, args=(video_id, filepath, title, description, tags, privacy, schedule_datetime))
        thread.start()
    
    if 'instagram' in platforms:
        upload_status[video_id]['instagram'] = {'status': 'uploading', 'progress': 0}
        caption = f"{title}\n\n{description}"
        ig_schedule = None
        if schedule_datetime:
            dt = datetime.fromisoformat(schedule_datetime.replace('+09:00', '+09:00'))
            ig_schedule = int(dt.timestamp())
        thread = threading.Thread(target=upload_to_instagram, args=(video_id, filepath, caption, ig_schedule))
        thread.start()
    
    return jsonify({'video_id': video_id, 'status': 'started'})

if __name__ == '__main__':
    print("=" * 50)
    print("YouTube & Instagram Uploader")
    print("브라우저에서 http://localhost:5000 접속")
    print("=" * 50)
    app.run(debug=True, port=5000)
