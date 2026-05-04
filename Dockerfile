# Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# OpenCV 및 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# SoccerNet 공식 라이브러리 및 필수 도구 설치
RUN pip install --no-cache-dir \
    SoccerNet \
    opencv-python \
    numpy \
    tqdm

# 검증 스크립트 복사
COPY verify_setup.py .

CMD ["python", "verify_setup.py"]
