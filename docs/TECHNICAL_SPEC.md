# 기술 사양

이 문서는 최종 지향 기술 스택과 GPU 실험 환경을 정리합니다. 초기 구현은 [PHASE_1_VISION_OCR_PIPELINE.md](PHASE_1_VISION_OCR_PIPELINE.md)의 MVP 범위를 우선합니다.

## 1. 하드웨어 목표

```text
GPU: NVIDIA GeForce RTX 3090
VRAM: 24GB
목표: 90분 풀 경기 기준 1fps OCR 분석을 연구 실험 가능한 시간 안에 처리
```

## 2. 기술 스택

| 구분 | 도구/모델 | 역할 | 적용 시점 |
|---|---|---|---|
| 컨테이너 | Docker / Docker Compose | 실행 환경 격리 | 현재 |
| GUI | Streamlit | SoccerNet 경기 탐색 및 다운로드 | 현재 |
| 비디오 처리 | OpenCV / ffmpeg | 프레임 추출, 클립 생성 | Phase 1 MVP |
| GPU 디코딩 | NVIDIA DALI | 고속 비디오 읽기 | 최적화 단계 |
| 영역 탐지 | YOLO11n | 스코어보드/자막 영역 자동 탐지 | Phase 1.5 |
| OCR | PaddleOCR | 텍스트 인식 | Phase 1 |
| OCR 정제 | Pandas / NumPy | 시계열 smoothing | Phase 1 |
| 오디오 | PANNs / librosa | 함성, 휘슬, 피크 분석 | Phase 2 |
| 장면 전환 | PySceneDetect | 리플레이/컷 밀도 추정 | Phase 2 |
| 그래프 | NetworkX / PyTorch Geometric | 이벤트 그래프 구축 | Phase 3 |
| 설명 생성 | Rule template / Local LLM | 후보 선택 이유 생성 | Phase 3+ |

## 3. Docker 전략

현재 Dockerfile은 GUI와 SoccerNet 다운로드를 안정적으로 실행하는 CPU/기본 환경입니다.

GPU OCR 실험은 기존 환경을 바로 바꾸지 않고 별도 파일로 분리하는 것을 권장합니다.

```text
Dockerfile        : GUI/다운로드/기본 검증
Dockerfile.gpu    : CUDA/PaddleOCR/YOLO/DALI 실험
docker-compose.yml: 기본 GUI 실행
compose.gpu.yml   : GPU OCR 실험 실행
```

## 4. GPU Dockerfile 목표 예시

```dockerfile
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

ENV PADDLE_MODEL_DIR=/root/.paddleocr
ENV TORCH_HOME=/root/.cache/torch

COPY . .
```

실제 GPU Dockerfile은 PaddlePaddle CUDA 버전 호환성을 확인한 뒤 고정합니다.

## 5. Phase별 모델 계획

### Phase 1. Vision & OCR Pipeline

우선 구현:

```text
OpenCV/ffmpeg frame sampling
Manual crop config
PaddleOCR
Pandas/NumPy smoothing
Goal label evaluation
```

확장 구현:

```text
YOLO11n scoreboard/overlay detection
NVIDIA DALI video decoding
batch OCR optimization
```

### Phase 2. Multi-modal Feature Extraction

```text
audio_peak
whistle/crowd reaction
camera_cut_density
replay segment detection
```

### Phase 3. Event Graph & Reasoning

```text
Broadcast Graphic Event Graph
rule-based scoring baseline
lightweight ML scoring
explanation report
```

## 6. 주요 산출물

```text
outputs/frames/
outputs/crops/
outputs/ocr_csv/
outputs/event_graphs/
outputs/candidates/
outputs/clips/
outputs/reports/
```

## 7. 성능 목표

초기 목표:

```text
5경기 기준 프레임 추출 성공
5경기 기준 OCR CSV 생성
Goal label 대비 Recall@10s 계산 가능
```

확장 목표:

```text
10-20경기 OCR 실험
raw OCR vs smoothed OCR ablation
YOLO 자동 crop 적용
30-50경기 mini benchmark
```
