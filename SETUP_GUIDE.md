# 세팅 가이드

이 문서는 `my-sports-ai` 프로젝트를 처음 실행하기 위한 환경 세팅 절차를 정리합니다.

## 1. 사전 준비

필요한 도구:

```text
Docker Desktop
Docker Compose
Git
SoccerNet 데이터 접근 비밀번호
```

Docker Desktop을 실행한 뒤 Docker Engine이 켜져 있는지 확인합니다.

```bash
docker --version
docker compose version
```

## 2. 프로젝트 위치

```bash
cd C:\chun\workspace\my-sports-ai
```

## 3. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 만들고 SoccerNet 비밀번호를 저장합니다.

```text
SOCCERNET_PW=
```

`docker-compose.yml`은 `.env` 파일을 자동으로 읽습니다.

```yaml
env_file:
  - .env
```

## 4. Docker 이미지 빌드

최초 실행 또는 의존성 변경 후에는 이미지를 다시 빌드합니다.

```bash
docker compose up --build
```

이 명령은 다음 작업을 수행합니다.

```text
Python 3.11 기반 이미지 생성
OpenCV 실행에 필요한 시스템 패키지 설치
requirements.txt의 Python 패키지 설치
Streamlit GUI 서버 실행
```

정상 실행되면 브라우저에서 아래 주소를 엽니다.

```text
http://localhost:8501
```

## 5. Docker Compose 구성

현재 Compose 서비스는 GUI 앱을 기본 실행합니다.

```yaml
services:
  soccernet-app:
    build: .
    container_name: soccernet_checker
    volumes:
      - .:/app
      - ./data:/app/data
    env_file:
      - .env
    ports:
      - "8501:8501"
    command: streamlit run gui_app.py --server.address=0.0.0.0 --server.port=8501
```

`data/` 폴더는 호스트와 컨테이너가 공유합니다. 컨테이너를 지워도 다운로드한 데이터는 호스트의 `data/` 아래에 남습니다.

## 6. 의존성

주요 Python 패키지는 `requirements.txt`에서 관리합니다.

```text
SoccerNet
opencv-python
numpy
tqdm
questionary
python-dotenv
streamlit
pandas
```

Phase 1 OCR 실험에서 추가될 수 있는 패키지:

```text
paddleocr
paddlepaddle-gpu
ultralytics
ffmpeg-python
```

GPU 실험 환경은 기존 GUI용 Dockerfile을 바로 바꾸지 않고, 별도 GPU Dockerfile로 분리하는 것을 권장합니다.

## 7. 세팅 검증

SoccerNet 라이브러리와 데이터 접근을 확인합니다.

```bash
docker compose run --rm soccernet-app python verify_setup.py
```

성공 기준:

```text
SoccerNet 라이브러리 import 성공
valid split의 Labels-v2.json 다운로드 성공
```

## 8. 세팅 완료 기준

아래 조건을 만족하면 세팅 완료입니다.

```text
Docker 이미지 빌드 성공
Streamlit GUI 실행 성공
http://localhost:8501 접속 성공
SoccerNet 연결 검증 성공
data/spotting 경로에 라벨 저장 성공
```

다음 단계는 [RUN_GUIDE.md](RUN_GUIDE.md)를 따라 GUI에서 데이터를 다운로드하는 것입니다.
