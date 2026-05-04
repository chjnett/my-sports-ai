# Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# OpenCV 및 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. requirements.txt 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. 소스 코드 복사
COPY . .

# 검증 스크립트 실행을 기본값으로 설정
CMD ["python", "verify_setup.py"]