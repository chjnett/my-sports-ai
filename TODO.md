# TODO

이 문서는 `my-sports-ai` 프로젝트의 완료 작업과 다음 작업을 체크리스트로 관리하기 위한 문서입니다.

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

1. 타겟 경기 프레임 개수 확인
2. YOLO 학습 데이터셋 폴더 구조 생성
3. 라벨링용 대표 프레임 100장 추출
4. 자동 라벨 초안 생성
5. 리뷰 이미지 확인 및 필요한 라벨만 수정
6. YOLO11n smoke training
7. YOLO11s main training
8. 타겟 경기 inference
9. detection CSV 확인

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

1. 전체 프레임 샘플링이 완료됐는지 확인합니다.

```powershell
(Get-ChildItem "outputs\frames\england_epl\2014-2015\2015-02-21 - 18-00 Chelsea 1 - 1 Burnley\half_1" -Filter *.jpg).Count
(Get-ChildItem "outputs\frames\england_epl\2014-2015\2015-02-21 - 18-00 Chelsea 1 - 1 Burnley\half_2" -Filter *.jpg).Count
```

2. 대표 프레임 몇 장을 눈으로 확인합니다.

```text
half_1/0000000000.jpg
half_1/0000060000.jpg
half_1/0000600000.jpg
half_2/0000000000.jpg
half_2/0000600000.jpg
```

3. 아래 세 영역의 대략적인 좌표를 잡습니다.

```text
scoreboard  : 좌상단 또는 상단의 시간/점수 영역
overlay     : 하단 또는 중앙 하단의 선수명/카드/교체/VAR 자막 영역
replay_logo : 중앙 프리미어리그 전환 마크가 뜨는 영역
```

4. 30경기 batch 분석을 위해 YOLO11s detector 학습 데이터셋을 준비합니다.
5. 자동 라벨 초안을 생성하고 리뷰 이미지로 품질을 확인합니다.
6. 수동 crop은 모델 결과 검증용 baseline으로 유지합니다.

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
- [ ] replay_logo 후보 프레임 추출 전략 구현
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
- [ ] replay_logo 후보 프레임 추출기 구현

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
