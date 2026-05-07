# TODO

이 문서는 `my-sports-ai` 프로젝트의 완료 작업과 다음 작업을 체크리스트로 관리하기 위한 문서입니다.

## 0. 현재 완성도 판단

2026-05-07 기준:

```text
전체 프로젝트 기준: 약 35%
Phase 1 Vision/OCR 기준: 약 55%
Vision detector 기준: 약 75%
```

현재 완료된 큰 축:

```text
데이터 다운로드/검증
라벨 파싱
1fps 프레임 샘플링
scoreboard YOLO11s detector
replay_logo 후보 추출 및 라벨 반영
scoreboard + replay_logo YOLO11s 재학습
replay_transition_logo / replay_segment 이벤트 CSV 생성
```

남은 큰 축:

```text
scoreboard crop 생성
PaddleOCR 실행
score/clock parsing
OCR smoothing
Goal label evaluation
highlight candidate 생성
clip/report 생성
```

## 1. 완료한 작업

### 프로젝트 기본 세팅

- [x] Git 저장소 초기화
- [x] Docker 기반 실행 환경 구성
- [x] `Dockerfile` 작성
- [x] `docker-compose.yml` 작성
- [x] `.env` 기반 SoccerNet 비밀번호 로드 구성
- [x] `.gitignore`로 `data/`, `outputs/`, `.env`, 캐시 파일 제외
- [x] `.dockerignore`로 Docker build context 정리
- [x] `data/.gitkeep` 추가

### SoccerNet 다운로드/검증

- [x] `verify_setup.py` 구성
- [x] SoccerNet 라이브러리 import 검증
- [x] `Labels-v2.json` 테스트 다운로드 검증
- [x] Streamlit GUI 기반 경기 검색/다운로드 흐름 구성
- [x] 라벨, 224p, 720p 다운로드 모드 구성
- [x] `data/spotting/` 저장 구조 확인

### 문서 정리

- [x] `README.md` 정리
- [x] `SETUP_GUIDE.md` 정리
- [x] `RUN_GUIDE.md` 정리
- [x] `PROJECT_MASTER_PLAN.md` 작성
- [x] `docs/README.md` 작성
- [x] `docs/RESEARCH_ARCHITECTURE.md` 정리
- [x] `docs/PHASE_1_VISION_OCR_PIPELINE.md` 작성
- [x] `docs/TECHNICAL_SPEC.md` 작성
- [x] 기존 `docs/spec.md`를 `docs/TECHNICAL_SPEC.md`로 대체

### Phase 1A: 라벨 파서 + 프레임 샘플러

- [x] `src/` 기본 패키지 구조 생성
- [x] `src/data/labels.py` 구현
- [x] SoccerNet `Labels-v2.json` 파싱
- [x] Goal, Yellow card, Red card, Substitution 이벤트 추출
- [x] 이벤트 CSV 저장 기능 구현
- [x] `src/video/frame_sampler.py` 구현
- [x] 경기 폴더에서 전반/후반 영상 자동 탐색
- [x] 1fps 프레임 샘플링 구현
- [x] 샘플링 summary CSV 저장 기능 구현
- [x] `src/phase1a.py` 통합 실행 엔트리 구현
- [x] Docker 컨테이너 안에서 라벨 파서 검증
- [x] Docker 컨테이너 안에서 프레임 샘플러 검증
- [x] Docker 컨테이너 안에서 Phase 1A 통합 실행 검증

검증 명령:

```bash
docker compose run --rm soccernet-app python -m src.phase1a \
  --match-dir "data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" \
  --data-root data/spotting \
  --fps 1 \
  --max-seconds 3
```

검증 결과:

```text
Events: outputs/reports/phase1a_events.csv (10 target events)
Frame summary: outputs/reports/phase1a_frame_sampling_summary.csv
```

## 2. 바로 다음 작업

### 최우선 실행 순서

이제부터 직접 실행/테스트할 순서는 아래 문서를 기준으로 진행합니다.

```text
YOLO_DATASET_TEST_GUIDE.md
```

우선순위:

1. scoreboard + replay_logo 모델로 타겟 경기 전체 재추론
2. `replay_logo` 검출 시간대 확인
3. replay_logo 검출 review 이미지 생성
4. replay transition timestamp를 이벤트 CSV로 정리
5. scoreboard bbox 기반 crop 생성
6. PaddleOCR scoreboard OCR 실행
7. score/clock parsing 및 smoothing
8. SoccerNet Goal label 대비 score_change 평가
9. 5경기 이상으로 확장

### 현재 타겟 경기

현재 Phase 1 검증은 아래 경기 폴더를 기준으로 진행합니다.

```text
data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley
```

현재 확인된 리플레이 패턴:

```text
live play
-> Premier League center transition logo
-> replay segment
-> Premier League center transition logo
-> live play
```

따라서 스코어보드가 사라지는지만 보지 않고, `replay_logo` crop을 별도로 만들어 중앙 프리미어리그 전환 마크를 추적합니다.

### 지금 해야 할 것

1. scoreboard + replay_logo 전체 추론을 실행합니다.

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.vision.detect_graphics `
  --model models/yolo/broadcast_graphics_yolo11s_scoreboard_replay.pt `
  --frames-root "outputs/frames/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" `
  --output outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv `
  --imgsz 1280 `
  --conf 0.25
```

2. replay_logo 검출 결과를 확인합니다.

```powershell
Import-Csv outputs\detections\chelsea_burnley_2015_scoreboard_replay_full.csv |
  Where-Object { $_.class_name -eq "replay_logo" } |
  Select-Object -First 30
```

3. 검출 시간대가 strict 후보 시간대와 가까운지 봅니다.

```text
expected replay_logo examples:
half_1 408s
half_1 1523s
half_2 187s
half_2 305s
half_2 463s
half_2 847s
half_2 1032s
half_2 1999s
```

4. 검출이 괜찮으면 replay transition event CSV 생성기로 넘어갑니다.

### Phase 1B: 수동 Crop Config + Crop 적용기

- [ ] `configs/crop_config.json` 스키마 설계
- [ ] 기본 scoreboard crop 좌표 작성
- [ ] 기본 overlay crop 좌표 작성
- [ ] 기본 replay_logo crop 좌표 작성
- [ ] `src/ocr/crop_config.py` 구현
- [ ] 프레임 폴더에서 crop 이미지 생성
- [ ] `scoreboard`, `overlay`, `replay_logo` 세 crop 타입 생성
- [ ] `outputs/crops/{match_id}/half_{n}/{crop_type}/` 저장 구조 생성
- [ ] crop summary CSV 저장
- [ ] Docker 컨테이너에서 crop 적용 검증
- [ ] `docs/PHASE_1_VISION_OCR_PIPELINE.md`에 crop 실행 명령 추가
- [ ] `TODO.md`에서 Phase 1B 완료 항목 체크

예상 실행 명령:

```bash
docker compose run --rm soccernet-app python -m src.ocr.crop_config \
  --frames-root "outputs/frames/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" \
  --config configs/crop_config.json \
  --output-root outputs/crops
```

완료 기준:

```text
대표 경기 1개에서 scoreboard crop 이미지 생성
대표 경기 1개에서 overlay crop 이미지 생성
대표 경기 1개에서 replay_logo crop 이미지 생성
수동 확인 시 경기 시간/점수 영역이 crop 안에 포함됨
수동 확인 시 하단 이벤트 자막 영역이 overlay crop 안에 포함됨
수동 확인 시 프리미어리그 중앙 전환 마크가 replay_logo crop 안에 들어올 수 있음
crop summary CSV 생성
```

### Phase 1B 산출물

```text
configs/crop_config.json
src/ocr/crop_config.py
outputs/crops/...
outputs/reports/crop_summary.csv
```

## 3. Phase 1C 이후 작업

### Phase 1B-2: YOLO11s Detector Dataset

- [x] `datasets/yolo_broadcast_graphics/` 구조 생성
- [x] `datasets/yolo_broadcast_graphics/data.yaml` 작성
- [x] `models/yolo/` 구조 생성
- [x] 라벨링용 대표 프레임 추출
- [x] class 정의 확정
  - [x] `scoreboard`
  - [x] `overlay`
  - [x] `replay_logo`
- [x] 자동 라벨 초안 생성 방식 결정
- [x] `src/vision/auto_label_graphics.py` 구현
- [x] scoreboard 자동 라벨 초안 생성
- [x] review 이미지 생성
- [ ] review 이미지에서 scoreboard bbox 품질 확인
- [ ] overlay 라벨링 전략 결정
- [x] replay_logo 후보 프레임 추출 전략 구현
- [ ] YOLO format export 방식 결정
- [x] train/val split 구성
- [x] `src/vision/prepare_yolo_dataset.py` 구현
- [ ] `docs/PHASE_1_VISION_OCR_PIPELINE.md`에 YOLO dataset 절차 추가

권장 모델:

```text
기본 detector: YOLO11s
빠른 테스트 detector: YOLO11n
```

최소 데이터 목표:

```text
5경기 x 20프레임 = 100장
scoreboard bbox 80개 이상
overlay bbox 30개 이상
replay_logo bbox 20개 이상
```

### Phase 1B-3: YOLO11s Detector Training

- [x] `Dockerfile.gpu` 작성
- [x] `compose.gpu.yml` 작성
- [x] `requirements-gpu.txt` 작성
- [x] `ultralytics` 설치 구성
- [x] `src/vision/train_detector.py` 구현
- [x] `src/vision/detect_graphics.py` 구현
- [x] YOLO11n smoke training
- [x] `models/yolo/broadcast_graphics_yolo11n.pt` 저장
- [x] smoke training 결과 확인
- [x] YOLO11n으로 타겟 경기 smoke inference 실행
- [x] `outputs/detections/chelsea_burnley_2015_yolo11n_smoke.csv` 저장
- [x] inference CSV에서 scoreboard 검출 개수 확인
- [x] `src/vision/summarize_detections.py` 구현
- [x] `src/vision/pseudo_label_graphics.py` 구현
- [x] YOLO11n pseudo-label 생성 전략 구현
- [x] pseudo-label confidence threshold 1차 기준 결정
- [x] confidence 0.70 이상 pseudo-label 후보 생성
- [x] pseudo-label review 이미지 확인
- [x] confidence 0.50 이상 pseudo-label 후보 생성
- [x] `src/vision/merge_yolo_datasets.py` 구현
- [x] pseudo-label 데이터셋을 원본 라벨셋에 병합
- [x] `datasets/yolo_broadcast_graphics_merged` 생성
- [ ] confidence 낮은 프레임 검토
- [x] YOLO11s main training
- [x] `models/yolo/broadcast_graphics_yolo11s.pt` 저장
- [x] 타겟 경기 inference 실행
- [x] `outputs/detections/chelsea_burnley_2015_yolo11s_full.csv` 저장
- [x] 전체 inference 결과 요약
- [ ] 수동 crop 결과와 detector bbox 비교
- [ ] scoreboard detection 기반 crop/OCR 입력 생성
- [x] replay_logo 후보 프레임 추출기 구현
- [x] `src/vision/extract_replay_logo_candidates.py` 구현
- [x] 타겟 경기 replay_logo 후보 추출 실행
- [x] replay_logo 후보 contact sheet 생성
- [x] replay_logo 후보 화면비율/로고색상 필터 추가
- [x] strict replay_logo 후보 12장 추출
- [x] strict replay_logo 후보 12장 리뷰
- [x] 실제 replay_logo 프레임만 YOLO 라벨로 반영
- [x] `src/vision/add_replay_logo_labels.py` 구현
- [x] `datasets/yolo_broadcast_graphics_replay_logo` 생성
- [x] `datasets/yolo_broadcast_graphics_scoreboard_replay` 생성
- [x] scoreboard + replay_logo YOLO11s 재학습
- [x] `models/yolo/broadcast_graphics_yolo11s_scoreboard_replay.pt` 저장
- [x] scoreboard + replay_logo 전체 프레임 재추론
- [x] replay_logo 검출 시간대 확인
- [x] `src/vision/build_replay_events.py` 구현
- [x] replay_transition_logo 이벤트 CSV 생성
- [x] replay_segment 후보 CSV 생성
- [ ] replay_logo 검출 결과 review 이미지 생성
- [ ] replay_segment 후보 실제 영상 구간 검증

YOLO11n smoke training 결과:

```text
학습 epoch: 10
모델: YOLO11n
대상 class: scoreboard
validation images: 18
validation instances: 16
final precision: 0.986
final recall: 1.000
final mAP50: 0.995
final mAP50-95: 0.900
저장 모델: models/yolo/broadcast_graphics_yolo11n.pt
```

해석:

```text
scoreboard 1차 탐지 모델은 smoke test 통과.
현재 데이터는 자동 라벨 기반이라 지표가 높게 나올 수 있음.
다음 검증은 타겟 경기 전체/일부 프레임 inference 결과 CSV와 실제 이미지 확인.
```

YOLO11n smoke inference 결과:

```text
입력 프레임 제한: 300
검출 수: 287
class: scoreboard only
confidence min: 0.319
confidence avg: 0.649
confidence max: 0.872
confidence >= 0.50: 266
confidence >= 0.70: 87
```

Pseudo-label 1차 생성 결과:

```text
threshold: 0.70
accepted images: 87
dataset: datasets/yolo_broadcast_graphics_pseudo
review images: outputs/pseudo_labels/review
```

Pseudo-label 확장 및 병합 결과:

```text
threshold: 0.50
accepted images: 266
pseudo dataset: datasets/yolo_broadcast_graphics_pseudo_050
merged dataset: datasets/yolo_broadcast_graphics_merged
merged total images: 357
merged total labels: 357
merged data yaml: datasets/yolo_broadcast_graphics_merged/data.yaml
```

YOLO11s main training 결과:

```text
학습 epoch: 50
모델: YOLO11s
학습 이미지: 339
검증 이미지: 18
검증 인스턴스: 16
final precision: 0.997
final recall: 1.000
final mAP50: 0.995
final mAP50-95: 0.972
저장 모델: models/yolo/broadcast_graphics_yolo11s.pt
```

YOLO11s full inference 결과:

```text
입력 프레임: 5400
검출 수: 5401
unique detected frames: 5377
class: scoreboard
half 1 detections: 2696
half 2 detections: 2705
confidence min: 0.254
confidence avg: 0.931
confidence max: 0.948
confidence >= 0.50: 5372
confidence >= 0.70: 5348
confidence >= 0.85: 5295
CSV: outputs/detections/chelsea_burnley_2015_yolo11s_full.csv
```

해석:

```text
scoreboard detector는 타겟 경기 전체 프레임에서 안정적으로 동작.
스코어보드가 대부분 프레임에서 유지되므로 replay 판단은 scoreboard disappearance가 아니라 Premier League center transition logo 기준으로 진행.
```

Replay logo 후보 추출 결과:

```text
구현 파일: src/vision/extract_replay_logo_candidates.py
입력 프레임: 5400
선택 후보: 100
CSV: outputs/replay_logo_candidates/chelsea_burnley_2015/candidates.csv
리뷰 이미지: outputs/replay_logo_candidates/chelsea_burnley_2015/review
contact sheet: outputs/replay_logo_candidates/chelsea_burnley_2015/contact_sheet.jpg
```

해석:

```text
상위 후보에는 Premier League 중앙 전환 로고가 잘 포함됨.
뒤쪽 후보에는 선수/벤치/광고판 오탐이 섞임.
다음 단계는 상위 20-40장부터 리뷰하고 실제 로고 프레임만 replay_logo class 라벨로 반영.
```

Replay logo strict 후보 추출 결과:

```text
추가 필터:
- box_area_ratio
- box_aspect_ratio
- logo_color_ratio
- magenta_ratio
- center_distance

명령 기준:
- min_score: 5.68
- min_box_area_ratio: 0.05
- max_box_area_ratio: 0.38
- max_center_distance: 0.45
- min_logo_color_ratio: 0.06
- min_magenta_ratio: 0.004

선택 후보: 12
대표 box_area_ratio: 0.346481
strict CSV: outputs/replay_logo_candidates/chelsea_burnley_2015_strict_logo/candidates.csv
strict contact sheet: outputs/replay_logo_candidates/chelsea_burnley_2015_strict_logo/contact_sheet.jpg
```

Replay logo 라벨 반영 결과:

```text
구현 파일: src/vision/add_replay_logo_labels.py
입력 CSV: outputs/replay_logo_candidates/chelsea_burnley_2015_strict_logo/candidates.csv
replay_logo labels: 12
replay_logo dataset: datasets/yolo_broadcast_graphics_replay_logo
merged scoreboard+replay dataset: datasets/yolo_broadcast_graphics_scoreboard_replay
merged total images: 369
merged total labels: 369
merged data yaml: datasets/yolo_broadcast_graphics_scoreboard_replay/data.yaml
```

Scoreboard + replay_logo 재학습 결과:

```text
학습 epoch: 30
모델: YOLO11s fine-tune
학습 데이터셋: datasets/yolo_broadcast_graphics_scoreboard_replay
저장 모델: models/yolo/broadcast_graphics_yolo11s_scoreboard_replay.pt
validation note: 현재 val set에는 scoreboard만 있어 replay_logo 지표는 표시되지 않음
scoreboard final precision: 0.997
scoreboard final recall: 1.000
scoreboard final mAP50: 0.995
scoreboard final mAP50-95: 0.972
```

Scoreboard + replay_logo 전체 추론 결과:

```text
입력 CSV: outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv
전체 검출 수: 5393
scoreboard 검출 수: 5380
replay_logo 검출 수: 13
replay_logo unique frames: 10
replay_logo confidence min: 0.253
replay_logo confidence avg: 0.262
replay_logo confidence max: 0.272
```

해석:

```text
replay_logo는 confidence가 낮지만 strict 후보 시간대와 정확히 겹침.
학습 샘플이 12장뿐이므로 replay_logo 이벤트화 기준은 min_conf=0.25로 사용.
```

Replay event 생성 결과:

```text
구현 파일: src/vision/build_replay_events.py
입력: outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv
출력: outputs/events/chelsea_burnley_2015_replay_events.csv
min_conf: 0.25
transition events: 10
replay segment candidates: 2
```

검출된 replay_logo timestamp:

```text
half_1: 408, 1523, 1747
half_2: 305, 379, 463, 847, 1032, 1630, 1999
```

### Phase 1C: OCR 실행

- [x] OCR 엔진 선택: PaddleOCR PP-OCRv5
- [ ] PaddleOCR PP-OCRv5 server 적용
- [ ] PaddleOCR PP-OCRv5 mobile 빠른 실험 옵션 적용
- [ ] GPU 버전은 별도 Dockerfile로 분리 검토
- [ ] `src/ocr/run_ocr.py` 구현
- [ ] `scoreboard`, `overlay` detected crop에서 OCR 실행
- [ ] OCR raw 결과 CSV 저장
- [ ] replay_logo crop은 OCR 대신 시각 이벤트 탐지 후보로 별도 저장
- [ ] 컬럼 정의
  - [ ] `match_id`
  - [ ] `half`
  - [ ] `timestamp_sec`
  - [ ] `crop_type`
  - [ ] `raw_text`
  - [ ] `confidence`
  - [ ] `parsed_clock`
  - [ ] `parsed_home_score`
  - [ ] `parsed_away_score`
  - [ ] `event_keyword`
- [ ] Docker 컨테이너에서 OCR 실행 검증

완료 기준:

```text
5경기 기준 OCR CSV 생성
score/clock 후보 컬럼 분리
OCR confidence 저장
```

### Phase 1D: OCR Cleaning

- [ ] `src/ocr/clean_ocr.py` 구현
- [ ] 숫자/문자 혼동 보정 규칙 작성
- [ ] 점수 문자열 파싱
- [ ] 경기 시간 문자열 파싱
- [ ] 이벤트 키워드 파싱
- [ ] 불가능한 점수 감소 제거

대표 보정 규칙:

```text
I-0 -> 1-0
O-0 -> 0-0
l -> 1
S8:12 -> 58:12
0O -> 00
```

### Phase 1D-2: Replay Logo Boundary Detection

- [ ] `src/vision/replay_logo.py` 구현
- [ ] `replay_logo` crop 이미지 변화량 계산
- [ ] 프리미어리그 중앙 전환 마크 등장 후보 timestamp 추출
- [ ] 가까운 두 전환 마크 사이를 `replay_segment` 후보로 묶기
- [ ] `outputs/reports/replay_logo_events.csv` 저장

출력 이벤트:

```text
replay_transition_logo
replay_segment
```

### Phase 1E: Temporal Smoothing

- [ ] `src/ocr/smoothing.py` 구현
- [ ] 5초 window 기반 점수 다수결
- [ ] 경기 시간 단조 증가 보정
- [ ] 단발 score change 제거
- [ ] smoothed OCR CSV 저장

완료 기준:

```text
raw OCR 대비 false score_change 감소
smoothed score timeline 생성
```

### Phase 1F: Goal Label Evaluation

- [ ] `src/evaluation/metrics.py` 구현
- [ ] OCR 기반 score_change timestamp 추출
- [ ] SoccerNet Goal label timestamp 추출
- [ ] Recall@5s 계산
- [ ] Recall@10s 계산
- [ ] Recall@30s 계산
- [ ] false positive per match 계산
- [ ] raw OCR vs smoothed OCR 비교표 생성

출력:

```text
outputs/reports/phase1_goal_recall_table.csv
outputs/reports/phase1_ocr_ablation.md
```

## 4. Phase 1.5 확장 작업

### 자동 영역 탐지

- [x] 기본 모델: YOLO11s
- [x] 빠른 테스트 모델: YOLO11n
- [ ] scoreboard/overlay detection 라벨링 방식 설계
- [ ] replay_logo detection 라벨링 방식 설계
- [ ] 학습용 crop annotation 포맷 정의
- [ ] `models/yolo_scoreboard.pt` 관리 방식 결정
- [ ] 자동 crop 결과와 수동 crop 결과 비교

### GPU OCR/디코딩

- [ ] `Dockerfile.gpu` 작성
- [ ] `compose.gpu.yml` 작성
- [ ] CUDA/PaddleOCR 호환 버전 확정
- [ ] GPU PaddleOCR batch inference 테스트
- [ ] NVIDIA DALI 적용 필요성 평가

## 5. Phase 2 이후 연구 작업

### Event Graph

- [ ] `src/graph/event_graph.py` 구현
- [ ] `src/graph/graph_schema.py` 구현
- [ ] `score_state` 노드 생성
- [ ] `score_change` 노드 생성
- [ ] `replay_overlay` 노드 생성
- [ ] `replay_transition_logo` 노드 생성
- [ ] `replay_segment` 노드 생성
- [ ] `label_nearby` 노드 생성
- [ ] `highlight_candidate` 노드 생성
- [ ] 이벤트 그래프 JSON 저장

### Highlight Generation

- [ ] `src/highlight/candidate_generator.py` 구현
- [ ] Goal 후보 구간 생성
- [ ] Card 후보 구간 생성
- [ ] Substitution 후보 구간 생성
- [ ] 가까운 후보 병합
- [ ] rule-based scoring 구현
- [ ] `src/video/clipper.py` 구현
- [ ] ffmpeg 기반 클립 생성
- [ ] 후보별 explanation JSON 생성

### 논문 실험 패키지

- [ ] 10경기 이상 실험
- [ ] 30경기 이상 확장 실험
- [ ] baseline 비교
- [ ] ablation 실험
- [ ] 실패 사례 분석
- [ ] 결과표 생성
- [ ] case study 작성
- [ ] 한국어 논문 초안 작성

## 6. 운영 규칙

- [ ] 모든 실행은 Docker 기반으로 수행
- [ ] 로컬 Python 환경에 의존하지 않기
- [ ] 대용량 데이터는 Git에 올리지 않기
- [ ] `data/`, `outputs/`, `paper/`는 Git 추적 제외 유지
- [ ] 구현 후 실행 명령은 관련 문서에 반영
- [ ] 각 Phase는 Docker 명령으로 재현 가능해야 함

## 7. 참고 문서

| 문서 | 역할 |
|---|---|
| [README.md](README.md) | 프로젝트 소개와 빠른 시작 |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 최초 세팅 |
| [RUN_GUIDE.md](RUN_GUIDE.md) | GUI 실행과 다운로드 사용법 |
| [PROJECT_MASTER_PLAN.md](PROJECT_MASTER_PLAN.md) | 개발 우선순위와 로드맵 |
| [docs/RESEARCH_ARCHITECTURE.md](docs/RESEARCH_ARCHITECTURE.md) | 연구 아키텍처 |
| [docs/PHASE_1_VISION_OCR_PIPELINE.md](docs/PHASE_1_VISION_OCR_PIPELINE.md) | Phase 1 실행 명세 |
| [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md) | 기술 사양 |
