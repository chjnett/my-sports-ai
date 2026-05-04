# ⚽ SoccerNet 하이라이트 추출 프로젝트 기초 세팅

이 문서는 **SoccerNet** 데이터셋을 활용하여 축구 경기 내 주요 이벤트(Goal, Card, Substitution)를 탐지하고 하이라이트를 추출하기 위한 Docker 기반 환경 설정 가이드를 담고 있습니다.

## 1. 프로젝트 정보 및 개요

* **데이터셋**: SoccerNet (500개 경기, 총 764시간 분량의 유럽 리그 영상)
* **주요 태스크**: **Action Spotting** (특정 이벤트가 발생하는 정확한 타임스탬프를 찾는 작업)
* **추출 대상**:
  * **득점 (Goal)**: 공이 골라인을 넘는 순간
  * **카드 (Card)**: 심판이 카드를 보여주는 순간
  * **교체 (Substitution)**: 선수가 경기장에 입장하는 순간

---

## 2. 구성 파일 (복사하여 사용)

프로젝트 폴더 내에 아래 세 파일을 각각 생성하세요.

### ① Dockerfile

환경의 일관성을 유지하기 위해 Python 3.11과 관련 라이브러리를 포함합니다.

```dockerfile
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
```

### ② docker-compose.yml

호스트 시스템의 `data` 폴더와 컨테이너를 연결하여 대용량 데이터를 관리합니다.

```yaml
services:
  soccernet-app:
    build: .
    container_name: soccernet_checker
    volumes:
      - .:/app
      - ./data:/app/data  # 대용량 영상 및 특징 데이터 저장소
    environment:
      - SOCCERNET_PW=s0cc3rn3t  # 메일로 수령한 비밀번호
    tty: true
    stdin_open: true
```

### ③ verify_setup.py

라이브러리가 정상 작동하는지, API를 통해 데이터셋 라벨을 가져올 수 있는지 확인합니다.

```python
import os
from pathlib import Path

from SoccerNet.Downloader import SoccerNetDownloader, getListGames


def check_setup():
    print("--- [1/2] 라이브러리 로드 테스트 ---")
    try:
        import SoccerNet
        print("✅ SoccerNet 라이브러리가 성공적으로 로드되었습니다.")
    except ImportError:
        print("❌ 라이브러리 로드 실패.")
        return

    print("\n--- [2/2] 데이터 접근 테스트 ---")
    pw = os.getenv("SOCCERNET_PW", "s0cc3rn3t")

    # 저장 경로를 data 폴더로 지정하여 다운로더 초기화
    local_dir = Path("data") / "spotting"
    downloader = SoccerNetDownloader(LocalDirectory=str(local_dir))
    downloader.password = pw

    try:
        # valid split의 첫 경기 라벨 하나만 다운로드하여 연결 확인
        game = getListGames(split="valid", task="spotting")[0]
        label_file = local_dir / game / "Labels-v2.json"

        downloader.downloadGame(game=game, files=["Labels-v2.json"], spl="valid")

        if not label_file.exists() or label_file.stat().st_size == 0:
            raise RuntimeError(f"라벨 파일 다운로드 확인 실패: {label_file}")

        print("\n✅ API 연결 및 데이터 다운로드 테스트 성공!")
        print("이제 프로젝트를 시작할 준비가 되었습니다.")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        print("네트워크 상태나 비밀번호(SOCCERNET_PW)를 확인하세요.")


if __name__ == "__main__":
    check_setup()
```

## 3. 실행 방법

1. `data` 폴더를 포함한 프로젝트 구조를 준비합니다.

2. 컨테이너를 빌드하고 실행합니다.

```bash
docker-compose up --build
```
