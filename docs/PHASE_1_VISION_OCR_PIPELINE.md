# Phase 1: Vision & OCR Pipeline

본 문서는 축구 중계 영상에서 하이라이트 탐지의 기초가 되는 시각 정보 추출 및 OCR 시계열 정제 파이프라인을 정의합니다.

Phase 1은 이 프로젝트의 첫 구현 우선순위입니다. 단, 최종 기술 스택과 초기 MVP 구현 범위를 분리해서 진행합니다.

## 1. Phase 1 목표

1. 프레임 샘플링: 풀 경기 영상을 1fps 기준으로 샘플링합니다.
2. 영역 설정: 스코어보드, 이벤트 자막, 리플레이 전환 로고 영역을 crop합니다.
3. OCR 실행: 팀명, 점수, 경기 시간, 이벤트 텍스트를 추출합니다.
4. 시계열 정제: OCR 오류를 시간축 논리로 보정합니다.
5. Goal 검증: SoccerNet `Labels-v2.json`의 Goal label과 score change를 비교합니다.

## 2. 실행 전략

30경기 batch 분석을 목표로 하므로 자동 탐지 모델을 사용합니다. 다만 학습 데이터셋이 만들어지기 전까지는 수동 crop으로 샘플 결과를 검증하고, 이후 YOLO detector로 자동화합니다.

```text
MVP: OpenCV/ffmpeg + manual crop + PaddleOCR + replay logo boundary + smoothing
Batch 분석 기본: YOLO11s detector + PaddleOCR PP-OCRv5 server
빠른 테스트: YOLO11n detector + PaddleOCR PP-OCRv5 mobile
최적화: NVIDIA DALI + batch GPU OCR
```

Detector class:

```text
scoreboard
overlay
replay_logo
```

현재 구현 상태:

```text
Phase 1A frame sampling 완료
scoreboard YOLO11s detector 학습 완료
scoreboard full inference 완료
replay_logo strict 후보 12장 라벨 반영 완료
scoreboard + replay_logo YOLO11s 재학습 완료
replay_transition_logo / replay_segment 이벤트 CSV 생성 완료
scoreboard crop 전체 생성 완료
PaddleOCR scoreboard OCR smoke test 완료
score/clock parsing 완료
OCR smoothing smoke test 완료
score_change vs Goal label 평가 smoke test 완료
strict score parser 적용 완료
기존 OCR CSV 재파싱 도구 완료
text_cue 추출 완료
highlight_candidate fusion 완료
highlight_candidate ranking 완료
Top-K Recall 평가 완료
Top-5 visual review contact sheet 생성 완료
```

현재 다음 작업:

```text
Top-5 후보 육안 판정 반영
ranking weight 2차 조정
text_cue stopword/선수명 정규화
5경기 확장
```

Phase 1 기준 완성도:

```text
Frame sampling: 완료
Vision detector: 1차 완료
Replay logo event: 1차 완료
OCR execution: 1차 완료
OCR smoothing: 1차 완료
Goal evaluation: 1차 완료
Overlay/scorer fusion: 미완료
Event fusion: 1차 완료
Ranking/Top-K: 1차 완료
Visual review: 1차 완료

Phase 1 전체 기준: 약 80%
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

이 타겟 경기의 리플레이 패턴은 스코어보드가 사라지는 것만으로 판단하지 않습니다. 프리미어리그 중앙 전환 마크가 등장하고, 리플레이 장면이 나온 뒤, 같은 전환 마크가 다시 등장하며 라이브 화면으로 돌아옵니다.

```text
live play
-> Premier League center transition logo
-> replay segment
-> Premier League center transition logo
-> live play
```

따라서 crop 영역은 최소 3개를 사용합니다.

```text
scoreboard  : 경기 시간, 팀명, 점수 OCR
overlay     : 선수명, 카드, 교체, VAR, 이벤트 자막 OCR
replay_logo : 중앙 프리미어리그 리플레이 전환 마크 탐지
```

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
    "overlay": { "x": 200, "y": 520, "w": 880, "h": 160 },
    "replay_logo": { "x": 420, "y": 180, "w": 440, "h": 320 }
  }
}
```

완료 기준:

```text
5경기 이상 scoreboard crop 생성
crop 이미지에 경기 시간과 점수 영역이 포함됨
replay_logo crop 이미지에 중앙 전환 마크가 포함될 수 있는 영역이 잡힘
```

### 3.2.1 Replay Logo Boundary Detection

리플레이 구간은 OCR 텍스트가 아니라 중앙 전환 로고의 시각적 신호로 먼저 탐지합니다.

초기 MVP 규칙:

```text
replay_logo crop에서 프리미어리그 전환 마크가 강하게 등장하는 timestamp를 찾음
가까운 두 전환 마크 사이 구간을 replay_segment 후보로 묶음
```

출력 이벤트:

```text
replay_transition_logo
replay_segment
```

이 신호는 이후 Event Graph에서 `score_change`, `label_nearby`, `audio_peak`와 함께 하이라이트 후보의 근거로 사용합니다.

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
리플레이 전환 로고 등장 시점
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
visual_event
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

### 4.1 YOLO11s Detection

목표:

```text
스코어보드 영역 자동 탐지
이벤트 자막 overlay 영역 자동 탐지
프리미어리그 중앙 replay_logo 자동 탐지
경기별 crop config 자동 생성
```

산출물:

```text
datasets/yolo_broadcast_graphics/
models/yolo/broadcast_graphics_yolo11s.pt
models/yolo/broadcast_graphics_yolo11s_scoreboard_replay.pt
outputs/detections/{match_id}.json
```

현재 완료된 detector 산출물:

```text
scoreboard model:
  models/yolo/broadcast_graphics_yolo11s.pt

scoreboard + replay_logo model:
  models/yolo/broadcast_graphics_yolo11s_scoreboard_replay.pt

scoreboard full inference:
  outputs/detections/chelsea_burnley_2015_yolo11s_full.csv

다음 inference 대상:
  outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv
```

현재 replay event 산출물:

```text
detection csv:
  outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv

replay event csv:
  outputs/events/chelsea_burnley_2015_replay_events.csv

transition events:
  10

replay segment candidates:
  2
```

학습 데이터 최소 목표:

```text
5경기 x 20프레임 = 100장
scoreboard bbox 80개 이상
overlay bbox 30개 이상
replay_logo bbox 20개 이상
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

이미 구현한 vision 파일:

```text
src/vision/prepare_yolo_dataset.py
src/vision/auto_label_graphics.py
src/vision/train_detector.py
src/vision/detect_graphics.py
src/vision/summarize_detections.py
src/vision/pseudo_label_graphics.py
src/vision/merge_yolo_datasets.py
src/vision/extract_replay_logo_candidates.py
src/vision/add_replay_logo_labels.py
```

출력 폴더:

```text
outputs/frames/
outputs/crops/
outputs/ocr_csv/
outputs/reports/
configs/
datasets/
models/
outputs/detections/
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

### 7.4 Scoreboard + Replay Logo 전체 추론

현재 재학습된 모델:

```text
models/yolo/broadcast_graphics_yolo11s_scoreboard_replay.pt
```

실행 명령:

```bash
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.vision.detect_graphics \
  --model models/yolo/broadcast_graphics_yolo11s_scoreboard_replay.pt \
  --frames-root "outputs/frames/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" \
  --output outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv \
  --imgsz 1280 \
  --conf 0.25
```

replay_logo 검출 확인:

```powershell
Import-Csv outputs\detections\chelsea_burnley_2015_scoreboard_replay_full.csv |
  Where-Object { $_.class_name -eq "replay_logo" } |
  Select-Object -First 30
```

완료 기준:

```text
replay_logo 검출이 Premier League 중앙 전환 로고 timestamp 근처에 집중됨
scoreboard 검출 성능이 기존 모델 대비 크게 흔들리지 않음
replay_transition_logo 이벤트 후보 CSV 생성 준비 완료
```

### 7.5 Replay Event CSV 생성

`replay_logo` 검출 confidence는 낮게 나오지만 strict 후보 timestamp와 일치하므로 `min-conf 0.25`를 사용합니다.

```bash
docker compose run --rm soccernet-app python -m src.vision.build_replay_events \
  --detections outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv \
  --output outputs/events/chelsea_burnley_2015_replay_events.csv \
  --min-conf 0.25 \
  --merge-gap-sec 3 \
  --min-segment-sec 4 \
  --max-segment-sec 90
```

현재 결과:

```text
input replay detections: 13
transition events: 10
replay segments: 2
```

### 7.6 Detection Review 이미지 생성

`replay_logo` 검출 결과를 이미지로 확인합니다.

```bash
docker compose run --rm soccernet-app python -m src.vision.render_detection_reviews \
  --detections outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv \
  --output-root outputs/reviews/chelsea_burnley_2015_replay_logo \
  --class-name replay_logo \
  --min-conf 0.25
```

현재 결과:

```text
rows selected: 13
review images: 10
contact sheet: outputs/reviews/chelsea_burnley_2015_replay_logo/contact_sheet.jpg
```

### 7.7 Replay Segment Review 생성

`replay_segment` 후보 구간을 일정 간격 프레임 contact sheet로 확인합니다.

```bash
docker compose run --rm soccernet-app python -m src.vision.render_event_segments \
  --events outputs/events/chelsea_burnley_2015_replay_events.csv \
  --frames-root "outputs/frames/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" \
  --output-root outputs/reviews/chelsea_burnley_2015_replay_segments \
  --event-type replay_segment \
  --sample-every-sec 5
```

현재 결과:

```text
segments selected: 2
segment sheets written: 2
```

### 7.8 Scoreboard Crop 생성

검출된 scoreboard bbox를 OCR 입력 이미지로 crop합니다.

```bash
docker compose run --rm soccernet-app python -m src.vision.crop_detections \
  --detections outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv \
  --output-root outputs/crops/chelsea_burnley_2015_detector \
  --summary outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv \
  --class-name scoreboard \
  --min-conf 0.70 \
  --padding 8 \
  --best-per-frame
```

현재 결과:

```text
crops written: 5277
output root: outputs/crops/chelsea_burnley_2015_detector
summary: outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv
```

### 7.9 Scoreboard OCR 실행

PaddleOCR로 scoreboard crop에서 팀명, 점수, 경기 시간을 추출합니다.

Smoke test:

```bash
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.ocr.run_scoreboard_ocr \
  --crops outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv \
  --output outputs/ocr_csv/chelsea_burnley_2015_scoreboard_smoke.csv \
  --limit 20 \
  --device gpu
```

현재 smoke 결과:

```text
raw_text 예시: CHE 0-0 BUR 00:13
score/clock parsing 정상
전환 그래픽 구간에서는 CHE BUR #CHEBUR 같은 OCR 노이즈 존재
```

전체 실행:

```bash
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.ocr.run_scoreboard_ocr \
  --crops outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv \
  --output outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full.csv \
  --device gpu
```

### 7.10 OCR Smoothing

같은 점수가 최근 window 안에서 여러 번 반복될 때만 안정 점수로 인정합니다.

OCR을 다시 돌리지 않고 기존 `raw_text`만 재파싱할 때는 다음 명령을 먼저 실행합니다.

```bash
docker compose run --rm soccernet-app python -m src.ocr.reparse_scoreboard_ocr \
  --input outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full.csv \
  --output outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full_reparsed.csv
```

score parser는 `1-0`, `1 - 1`처럼 하이픈이 있는 값만 점수로 인정합니다. `80:30` 같은 clock 값은 점수로 인정하지 않습니다.

```bash
docker compose run --rm soccernet-app python -m src.ocr.smooth_scoreboard_ocr \
  --ocr outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full_reparsed.csv \
  --output outputs/ocr_csv/chelsea_burnley_2015_scoreboard_smoothed_reparsed.csv \
  --events-output outputs/events/chelsea_burnley_2015_score_change_events_reparsed.csv \
  --window-sec 8 \
  --min-votes 3
```

Smoke test 결과:

```text
input rows: 20
smoothed rows: 20
score-change events: 0
0-0 안정 점수 유지 확인
```

전체 OCR 재파싱 결과:

```text
input rows: 5277
parsed score rows: 3426
parsed clock rows: 5186
score-change events: 1
```

### 7.11 Goal Label 평가

OCR 기반 score_change 이벤트를 SoccerNet Goal label과 비교합니다.

```bash
docker compose run --rm soccernet-app python -m src.evaluation.evaluate_score_changes \
  --labels outputs/reports/phase1a_events.csv \
  --score-events outputs/events/chelsea_burnley_2015_score_change_events_reparsed.csv \
  --output outputs/reports/chelsea_burnley_2015_score_change_eval_reparsed.csv \
  --tolerances 5,10,30
```

Smoke test는 초반 20초만 사용하므로 score_change가 없는 것이 정상입니다.
전체 OCR 이후에는 Chelsea 1 - 1 Burnley 경기의 Goal 2개 근처에서 score_change가 잡히는지 확인합니다.

현재 Chelsea 1 - 1 Burnley 결과:

```text
Goal labels: 2
score-change events: 1
Recall@30s: 1/2 = 0.500
첫 골: 13:10 label -> 13:21 score_change
두 번째 골: 80:21 근처 scoreboard가 1-1을 안정적으로 읽지 못함
80:31 raw_text에서 VOKES scorer 후보 확인
```

### 7.12 Text Cue + Event Fusion

scoreboard 점수 변화만으로 놓치는 Goal은 OCR text cue와 replay signal을 함께 사용합니다.

```bash
docker compose run --rm soccernet-app python -m src.ocr.extract_text_cues \
  --ocr outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full_reparsed.csv \
  --output outputs/events/chelsea_burnley_2015_text_cues.csv \
  --team-tokens CHE,BUR \
  --stopwords CORN,CORNER,CORNERS,CORNRS,RUR \
  --min-token-length 4 \
  --merge-gap-sec 20
```

```bash
docker compose run --rm soccernet-app python -m src.events.fuse_highlight_candidates \
  --score-events outputs/events/chelsea_burnley_2015_score_change_events_reparsed.csv \
  --text-events outputs/events/chelsea_burnley_2015_text_cues.csv \
  --replay-events outputs/events/chelsea_burnley_2015_replay_events.csv \
  --output outputs/events/chelsea_burnley_2015_highlight_candidates.csv \
  --merge-window-sec 30
```

평가:

```bash
docker compose run --rm soccernet-app python -m src.evaluation.evaluate_score_changes \
  --labels outputs/reports/phase1a_events.csv \
  --score-events outputs/events/chelsea_burnley_2015_highlight_candidates.csv \
  --output outputs/reports/chelsea_burnley_2015_highlight_candidate_eval.csv \
  --tolerances 5,10,30 \
  --event-types highlight_candidate
```

현재 결과:

```text
text cue events: 180
highlight candidates: 50
Recall@30s: 2/2 = 1.000
첫 골: score_change, delta 11초
두 번째 골: VOKES text_cue, delta 12초
```

### 7.13 Candidate Ranking / Top-K

후보 50개를 evidence 기반 점수로 정렬합니다.

```bash
docker compose run --rm soccernet-app python -m src.events.rank_highlight_candidates \
  --input outputs/events/chelsea_burnley_2015_highlight_candidates.csv \
  --output outputs/events/chelsea_burnley_2015_highlight_candidates_ranked.csv \
  --boost-tokens DROGBA,VOKES
```

Top-K 평가:

```bash
docker compose run --rm soccernet-app python -m src.evaluation.evaluate_topk_candidates \
  --labels outputs/reports/phase1a_events.csv \
  --candidates outputs/events/chelsea_burnley_2015_highlight_candidates_ranked.csv \
  --output outputs/reports/chelsea_burnley_2015_highlight_topk_eval.csv \
  --details-output outputs/reports/chelsea_burnley_2015_highlight_topk_eval_details.csv \
  --top-k 1,3,5,10,20 \
  --tolerances 5,10,30
```

현재 결과:

```text
Top-1 Recall@30s: 0.500
Top-3 Recall@30s: 0.500
Top-5 Recall@30s: 1.000
Top-10 Recall@30s: 1.000
```

### 7.14 Top-K Visual Review

랭킹된 후보를 사람이 빠르게 검수할 수 있도록 contact sheet로 렌더링합니다.
렌더링 이미지는 전반/후반 영상 내부 시간(`video`)과 90분 경기 기준 시간(`match`)을 함께 표시합니다.

```bash
docker compose run --rm soccernet-app python -m src.events.render_ranked_candidates \
  --candidates outputs/events/chelsea_burnley_2015_highlight_candidates_ranked.csv \
  --output-root outputs/reviews/chelsea_burnley_2015_highlight_top5 \
  --top-k 5 \
  --context-sec=-10,0,10 \
  --thumb-width 320 \
  --cols 1
```

출력:

```text
outputs/reviews/chelsea_burnley_2015_highlight_top5/contact_sheet.jpg
outputs/reviews/chelsea_burnley_2015_highlight_top5/images/
```

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
