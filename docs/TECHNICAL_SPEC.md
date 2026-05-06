# 기술 사양

이 문서는 최종 지향 기술 스택과 GPU 실험 환경을 정리합니다. 초기 구현은 [PHASE_1_VISION_OCR_PIPELINE.md](PHASE_1_VISION_OCR_PIPELINE.md)의 MVP 범위를 우선합니다.

## 1. 하드웨어 목표

```text
GPU: NVIDIA GeForce RTX 3090
VRAM: 24GB
목표: 90분 풀 경기 기준 1fps OCR 분석을 연구 실험 가능한 시간 안에 처리
```

## 2. 모델 선정 결론

30경기 batch 분석을 목표로 하므로 자동 탐지 모델을 사용합니다. 최종 선택은 다음과 같습니다.

```text
Detector 기본 모델: Ultralytics YOLO11s
Detector 빠른 테스트 모델: Ultralytics YOLO11n
OCR 기본 모델: PaddleOCR PP-OCRv5 server
OCR 빠른 테스트 모델: PaddleOCR PP-OCRv5 mobile
Replay logo 처리: YOLO detector의 replay_logo class
```

선정 이유:

```text
YOLO11s는 30경기 batch 추론에서 RTX 3090이 감당 가능한 속도와 YOLO11n보다 나은 정확도의 균형점이다.
YOLO11n은 라벨링/학습 파이프라인 smoke test와 빠른 실험용으로 사용한다.
PaddleOCR PP-OCRv5 server는 crop 이미지 단위 OCR 정확도를 우선할 때 기본값으로 둔다.
PP-OCRv5 mobile은 처리량 비교와 빠른 반복 실험용으로 둔다.
replay_logo는 OCR 대상이 아니라 object detection class로 탐지한다.
```

탐지 클래스:

```yaml
names:
  0: scoreboard
  1: overlay
  2: replay_logo
```

## 3. 기술 스택

| 구분 | 도구/모델 | 역할 | 적용 시점 |
|---|---|---|---|
| 컨테이너 | Docker / Docker Compose | 실행 환경 격리 | 현재 |
| GUI | Streamlit | SoccerNet 경기 탐색 및 다운로드 | 현재 |
| 비디오 처리 | OpenCV / ffmpeg | 프레임 추출, 클립 생성 | Phase 1 MVP |
| GPU 디코딩 | NVIDIA DALI | 고속 비디오 읽기 | 최적화 단계 |
| 영역 탐지 | YOLO11s | 스코어보드/자막/리플레이 로고 자동 탐지 | Phase 1B+ |
| 빠른 탐지 실험 | YOLO11n | 데이터셋 smoke test 및 빠른 추론 | Phase 1B+ |
| OCR | PaddleOCR PP-OCRv5 server | scoreboard/overlay 텍스트 인식 | Phase 1C |
| 빠른 OCR 실험 | PaddleOCR PP-OCRv5 mobile | 처리량 비교 및 빠른 반복 실험 | Phase 1C |
| OCR 정제 | Pandas / NumPy | 시계열 smoothing | Phase 1 |
| 오디오 | PANNs / librosa | 함성, 휘슬, 피크 분석 | Phase 2 |
| 장면 전환 | PySceneDetect | 리플레이/컷 밀도 추정 | Phase 2 |
| 그래프 | NetworkX / PyTorch Geometric | 이벤트 그래프 구축 | Phase 3 |
| 설명 생성 | Rule template / Local LLM | 후보 선택 이유 생성 | Phase 3+ |

## 4. Docker 전략

현재 Dockerfile은 GUI와 SoccerNet 다운로드를 안정적으로 실행하는 CPU/기본 환경입니다.

GPU OCR 실험은 기존 환경을 바로 바꾸지 않고 별도 파일로 분리하는 것을 권장합니다.

```text
Dockerfile        : GUI/다운로드/기본 검증
Dockerfile.gpu    : CUDA/PaddleOCR/YOLO/DALI 실험
docker-compose.yml: 기본 GUI 실행
compose.gpu.yml   : GPU OCR 실험 실행
```

## 5. GPU Dockerfile 목표 예시

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

## 6. 데이터셋 구조

YOLO 학습 데이터는 Git 추적 대상에서 제외하고 로컬에 보관합니다.

```text
datasets/
  yolo_broadcast_graphics/
    images/
      train/
      val/
    labels/
      train/
      val/
    data.yaml

models/
  yolo/
    broadcast_graphics_yolo11s.pt
```

`data.yaml` 기본 형식:

```yaml
path: /app/datasets/yolo_broadcast_graphics
train: images/train
val: images/val
names:
  0: scoreboard
  1: overlay
  2: replay_logo
```

## 7. Phase별 모델 계획

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
YOLO11s scoreboard/overlay/replay_logo detection
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

## 8. 주요 산출물

```text
outputs/frames/
outputs/crops/
outputs/ocr_csv/
outputs/event_graphs/
outputs/candidates/
outputs/clips/
outputs/reports/
outputs/detections/
```

## 9. 성능 목표

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
