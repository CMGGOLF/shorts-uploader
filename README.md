# YouTube Shorts Uploader

유튜브 Shorts 업로드 관리 프로그램 (로컬 웹앱)

## 설치

```bash
pip install flask google-api-python-client google-auth-oauthlib google-auth-httplib2
```

## 설정

1. [Google Cloud Console](https://console.cloud.google.com)에서 프로젝트 생성
2. YouTube Data API v3 활성화
3. OAuth 클라이언트 ID 생성 (데스크톱 앱)
4. `client_secret.json` 파일을 이 폴더에 넣기

## 실행

```bash
python app.py
```

브라우저에서 http://localhost:5000 접속

## 사용법

1. 처음 실행 시 "Google 로그인" 버튼 클릭
2. 영상 파일 선택 후 제목/설명/태그 입력
3. "목록에 추가" 클릭
4. 목록에서 "업로드" 버튼 클릭

## 파일 구조

- `app.py` - 서버
- `templates/index.html` - UI
- `client_secret.json` - Google 인증 파일 (직접 추가)
- `token.json` - 로그인 토큰 (자동 생성)
- `videos.json` - 영상 목록 데이터 (자동 생성)
- `uploads/` - 업로드된 영상 저장 폴더
