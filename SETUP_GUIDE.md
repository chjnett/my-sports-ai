# 세팅 가이드

이 문서는 `my-sports-ai` 프로젝트를 처음 실행하기 위한 환경 세팅 절차를 정리합니다.

한 번 세팅을 완료한 뒤에는 [RUN_GUIDE.md](RUN_GUIDE.md)를 참고해 GUI를 실행하면 됩니다.

## 1. 사전 준비

아래 도구가 필요합니다.

```text
Docker Desktop
Docker Compose
Git
SoccerNet 데이터 접근 비밀번호
```

Windows에서는 Docker Desktop을 먼저 실행하고 Docker Engine이 켜져 있는지 확인합니다.

```bash
docker --version
docker compose version
```

## 2. 프로젝트 위치

현재 작업 경로는 다음과 같습니다.

```bash
cd C:\chun\workspace\my-sports-ai
```

## 3. 환경 변수 설정

SoccerNet 비밀번호는 `.env` 파일에 저장합니다.

```text
SOCCERNET_PW=s0cc3rn3t
```

메일로 받은 실제 비밀번호가 있다면 `s0cc3rn3t` 값을 교체합니다.

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
1. Python 3.11 기반 Docker 이미지 생성
2. OpenCV 실행에 필요한 Linux 패키지 설치
3. requirements.txt의 Python 패키지 설치
4. Streamlit GUI 서버 실행
```

정상 실행되면 아래 주소가 표시됩니다.

```text
http://localhost:8501
```

## 5. Docker Compose 구성

현재 `docker-compose.yml`은 GUI 앱을 기본 실행합니다.

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
    tty: true
    stdin_open: true
    command: streamlit run gui_app.py --server.address=0.0.0.0 --server.port=8501
```

`data` 폴더는 호스트와 컨테이너가 공유합니다. 다운로드한 영상과 라벨은 컨테이너를 지워도 호스트의 `data/` 아래에 남습니다.

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

향후 OCR 실험을 시작하면 아래 패키지를 추가할 수 있습니다.

```text
easyocr 또는 paddleocr
ffmpeg-python
scikit-learn
lightgbm 또는 xgboost
```

## 7. 세팅 검증

SoccerNet 라이브러리와 데이터 접근을 확인하려면 다음 명령을 실행합니다.

```bash
docker compose run --rm soccernet-app python verify_setup.py
```

검증 스크립트는 다음을 확인합니다.

```text
1. SoccerNet Python 라이브러리 import 가능 여부
2. valid split의 라벨 파일 다운로드 가능 여부
```

## 8. 세팅 완료 기준

아래 조건을 만족하면 세팅이 완료된 상태입니다.

```text
Docker 이미지 빌드 성공
Streamlit GUI 서버 실행 성공
http://localhost:8501 접속 성공
SoccerNet 라이브러리 import 성공
Labels-v2.json 테스트 다운로드 성공
```

## 9. 다음 단계

세팅 후에는 [RUN_GUIDE.md](RUN_GUIDE.md)의 순서대로 GUI에서 경기 목록을 검색하고 영상을 다운로드합니다.

연구 설계는 [docs/RESEARCH_ARCHITECTURE.md](docs/RESEARCH_ARCHITECTURE.md)를 기준으로 진행합니다.
