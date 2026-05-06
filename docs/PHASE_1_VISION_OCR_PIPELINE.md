# Phase 1: Vision & OCR Pipeline

본 문서는 축구 중계 영상에서 하이라이트 탐지의 기초가 되는 시각 정보 추출 및 OCR 시계열 정제 파이프라인을 정의합니다.

Phase 1은 이 프로젝트의 첫 구현 우선순위입니다. 단, 최종 기술 스택과 초기 MVP 구현 범위를 분리해서 진행합니다.

## 1. Phase 1 목표

1. 프레임 샘플링: 풀 경기 영상을 1fps 기준으로 샘플링합니다.
2. 영역 설정: 스코어보드와 이벤트 자막 영역을 crop합니다.
3. OCR 실행: 팀명, 점수, 경기 시간, 이벤트 텍스트를 추출합니다.
4. 시계열 정제: OCR 오류를 시간축 논리로 보정합니다.
5. Goal 검증: SoccerNet `Labels-v2.json`의 Goal label과 score change를 비교합니다.

## 2. 실행 전략

처음부터 YOLO, DALI, CUDA 최적화를 모두 적용하지 않습니다. 연구 결과를 빨리 확인하기 위해 MVP를 먼저 구현하고, 이후 자동화와 GPU 최적화를 확장합니다.

```text
MVP: OpenCV/ffmpeg + manual crop + PaddleOCR + smoothing
확장: YOLO11n + NVIDIA DALI + batch GPU OCR
```

## 3. MVP 범위

### 3.1 Frame Sampling

입력:

```text
data/spotting/{league}/{season}/{match}/1_224p.mkv
data/spotting/{league}/{season}/{match}/1_720p.mkv
```

처리:

```text
1fps로 프레임 추출
전반/후반 구분
timestamp 기반 파일명 저장
```

출력:

```text
outputs/frames/{match_id}/{half}/{timestamp}.jpg
```

완료 기준:

```text
5경기 기준 프레임 추출 성공
프레임 파일명과 영상 시간이 매칭됨
추출 로그 저장
```

### 3.2 Manual Crop Config

초기에는 수동 crop으로 시작합니다. 자동 탐지는 Phase 1.5로 둡니다.

입력:

```text
대표 프레임 이미지
```

출력:

```text
configs/crop_config.json
outputs/crops/{match_id}/{half}/{timestamp}.jpg
```

설정 예시:

```json
{
  "default": {
    "scoreboard": { "x": 0, "y": 0, "w": 420, "h": 90 },
    "overlay": { "x": 200, "y": 520, "w": 880, "h": 160 }
  }
}
```

완료 기준:

```text
5경기 이상 scoreboard crop 생성
crop 이미지에 경기 시간과 점수 영역이 포함됨
```

### 3.3 OCR Execution

우선 OCR 엔진은 PaddleOCR을 사용합니다.

추출 대상:

```text
경기 시간
홈/원정 팀명
현재 점수
추가시간
Replay / VAR / Goal / Card / Substitution 자막
선수명 그래픽
```

출력 CSV:

```text
outputs/ocr_csv/{match_id}.csv
```

권장 컬럼:

```text
match_id
half
timestamp_sec
crop_type
raw_text
confidence
parsed_clock
parsed_home_score
parsed_away_score
event_keyword
```

완료 기준:

```text
5경기 기준 OCR CSV 생성
score/clock 후보 컬럼 분리
OCR confidence 저장
```

### 3.4 OCR Cleaning

대표 보정 규칙:

```text
I-0 -> 1-0
O-0 -> 0-0
l -> 1
S8:12 -> 58:12
0O -> 00
```

점수 검증 규칙:

```text
점수는 음수가 될 수 없음
점수는 감소할 수 없음
한 번에 여러 골이 증가하는 경우 confidence 낮게 처리
한 프레임만 등장한 score_change는 보류
```

### 3.5 Temporal Smoothing

기본 규칙:

```text
최근 5초 window에서 점수 다수결
경기 시간은 단조 증가하도록 보정
불가능한 점수 감소 제거
짧은 단발 OCR 결과 제거
```

출력:

```text
outputs/ocr_csv/{match_id}_smoothed.csv
```

완료 기준:

```text
raw OCR 대비 false score_change 감소
smoothed score timeline 생성
```

### 3.6 Goal Label Evaluation

SoccerNet `Labels-v2.json`의 Goal label과 OCR 기반 score change를 비교합니다.

평가 지표:

```text
Recall@5s
Recall@10s
Recall@30s
False positive per match
```

출력:

```text
outputs/reports/phase1_goal_recall_table.csv
outputs/reports/phase1_ocr_ablation.md
```

완료 기준:

```text
5-10경기 기준 평가표 생성
raw OCR vs smoothed OCR 비교 가능
성공/실패 사례 정리
```

## 4. Phase 1.5 확장 범위

MVP가 동작한 뒤 아래 기능을 추가합니다.

### 4.1 YOLO11n Detection

목표:

```text
스코어보드 영역 자동 탐지
이벤트 자막 overlay 영역 자동 탐지
경기별 crop config 자동 생성
```

산출물:

```text
models/yolo_scoreboard.pt
outputs/detections/{match_id}.json
```

### 4.2 NVIDIA DALI Decoding

목표:

```text
GPU 기반 비디오 디코딩
frame sampling 병목 감소
batch OCR 입력 최적화
```

적용 기준:

```text
OpenCV/ffmpeg 방식이 실험 속도 병목이 될 때 적용
```

## 5. Docker 전략

현재 GUI/다운로드 Docker 환경은 유지합니다.

GPU OCR 실험은 별도 파일로 분리합니다.

```text
Dockerfile        : GUI/다운로드/기본 검증
Dockerfile.gpu    : CUDA/PaddleOCR/YOLO 실험
docker-compose.yml: GUI 실행
compose.gpu.yml   : GPU OCR 실행
```

GPU Dockerfile 목표:

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

## 6. 구현 파일 계획

Phase 1A에서 우선 구현한 파일:

```text
src/data/labels.py
src/video/frame_sampler.py
src/phase1a.py
```

다음 단계에서 추가할 파일:

```text
src/ocr/crop_config.py
src/ocr/run_ocr.py
src/ocr/clean_ocr.py
src/ocr/smoothing.py
src/evaluation/metrics.py
```

출력 폴더:

```text
outputs/frames/
outputs/crops/
outputs/ocr_csv/
outputs/reports/
configs/
```

## 7. Docker 실행 명령

모든 Phase 1A 작업은 Docker 컨테이너 안에서 실행합니다.

### 7.1 라벨 파서 실행

```bash
docker compose run --rm soccernet-app python -m src.data.labels \
  --data-root data/spotting \
  --output outputs/reports/labels_events.csv
```

출력:

```text
outputs/reports/labels_events.csv
```

### 7.2 프레임 샘플러 실행

```bash
docker compose run --rm soccernet-app python -m src.video.frame_sampler \
  --match-dir "data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" \
  --data-root data/spotting \
  --fps 1 \
  --summary outputs/reports/frame_sampling_summary.csv
```

빠른 테스트만 할 때는 `--max-seconds`를 사용합니다.

```bash
docker compose run --rm soccernet-app python -m src.video.frame_sampler \
  --match-dir "data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" \
  --data-root data/spotting \
  --fps 1 \
  --max-seconds 3
```

### 7.3 Phase 1A 통합 실행

```bash
docker compose run --rm soccernet-app python -m src.phase1a \
  --match-dir "data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" \
  --data-root data/spotting \
  --fps 1 \
  --max-seconds 3
```

출력:

```text
outputs/reports/phase1a_events.csv
outputs/reports/phase1a_frame_sampling_summary.csv
outputs/frames/{match_id}/half_1/
outputs/frames/{match_id}/half_2/
```

전체 영상을 처리할 때는 `--max-seconds`를 제거합니다.

## 8. Phase 1 완료 기준

```text
5-10경기 기준 프레임 추출 성공
수동 crop config 저장
PaddleOCR CSV 생성
OCR smoothing 결과 생성
Goal label 대비 Recall@5/10/30s 계산
raw OCR vs smoothed OCR 비교표 생성
실패 사례 3개 이상 정리
```

## 9. Phase 1 이후 연결

Phase 1 산출물은 이후 Event Graph 단계로 연결됩니다.

```text
smoothed OCR timeline
-> score_state
-> score_change
-> replay_overlay
-> label_nearby
-> highlight_candidate
```
