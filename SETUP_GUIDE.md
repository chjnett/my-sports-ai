# SoccerNet 프로젝트 세팅 가이드

이 문서는 `my-sports-ai` 프로젝트를 처음 실행하기 위한 Docker 기반 세팅 절차를 정리합니다. 한 번만 완료하면 이후에는 `RUN_GUIDE.md`를 참고해 실행하면 됩니다.

## 1. 사전 준비

아래 항목이 설치되어 있어야 합니다.

* Docker Desktop
* Docker Compose
* Git
* SoccerNet 데이터 접근 비밀번호

Windows에서는 Docker Desktop 실행 후 Docker Engine이 정상적으로 켜져 있는지 확인하세요.

```bash
docker --version
docker compose version
```

## 2. 프로젝트 구조

현재 프로젝트의 기본 구조는 다음과 같습니다.

```text
my-sports-ai/
├── .dockerignore
├── Dockerfile
├── README.md
├── RUN_GUIDE.md
├── SETUP_GUIDE.md
├── data/
│   └── .gitkeep
├── docker-compose.yml
└── verify_setup.py
```

`data` 폴더는 SoccerNet 라벨, 특징 파일, 영상 데이터를 저장하는 공간입니다. 대용량 데이터가 들어갈 수 있으므로 Docker 이미지에는 포함하지 않고 호스트 폴더로 마운트합니다.

## 3. Dockerfile 구성

`Dockerfile`은 Python 3.11 기반 실행 환경을 만듭니다.

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    SoccerNet \
    opencv-python \
    numpy \
    tqdm

COPY verify_setup.py .

CMD ["python", "verify_setup.py"]
```

`libgl1`과 `libglib2.0-0`은 OpenCV 실행에 필요한 Linux 시스템 라이브러리입니다.

## 4. Docker Compose 구성

`docker-compose.yml`은 프로젝트 폴더와 `data` 폴더를 컨테이너 내부 `/app`에 연결합니다.

```yaml
services:
  soccernet-app:
    build: .
    container_name: soccernet_checker
    volumes:
      - .:/app
      - ./data:/app/data
    environment:
      - SOCCERNET_PW=s0cc3rn3t
    tty: true
    stdin_open: true
```

실제 SoccerNet 비밀번호가 따로 있다면 `SOCCERNET_PW` 값을 받은 비밀번호로 바꾸세요.

## 5. 검증 스크립트 구성

`verify_setup.py`는 다음 두 가지를 확인합니다.

1. SoccerNet Python 라이브러리 import 가능 여부
2. SoccerNet 라벨 파일 하나를 `data/spotting` 아래로 다운로드할 수 있는지

검증에 성공하면 아래 메시지가 출력됩니다.

```text
✅ SoccerNet 라이브러리가 성공적으로 로드되었습니다.
✅ API 연결 및 데이터 다운로드 테스트 성공!
이제 프로젝트를 시작할 준비가 되었습니다.
```

## 6. 최초 세팅 확인

프로젝트 루트에서 아래 명령을 실행합니다.

```bash
docker compose config
```

Compose 설정이 출력되면 기본 설정 파일은 정상입니다.

이후 최초 빌드와 검증을 실행합니다.

```bash
docker compose up --build
```

처음 실행할 때는 Python 이미지, Debian 패키지, Python 패키지를 다운로드하므로 시간이 걸릴 수 있습니다.

## 7. 세팅 완료 기준

아래 조건을 만족하면 기초 세팅은 완료된 상태입니다.

* Docker 이미지 빌드 성공
* `soccernet_checker` 컨테이너 실행 성공
* SoccerNet 라이브러리 로드 성공
* `data/spotting/.../Labels-v2.json` 라벨 파일 다운로드 성공

세팅이 완료되면 이후 실행은 `RUN_GUIDE.md`를 참고하세요.
