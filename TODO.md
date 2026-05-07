# TODO

이 문서는 `my-sports-ai` 프로젝트의 완료 작업과 다음 작업을 한 번에 관리하기 위한 체크리스트입니다.

## 0. 현재 상태

2026-05-07 기준:

```text
전체 프로젝트 기준: 약 38%
Phase 1 Vision/OCR 기준: 약 65%
Vision detector 기준: 약 75%
OCR MVP 기준: 약 45%
```

현재 완료된 큰 흐름:

```text
SoccerNet 다운로드/검증 환경
1fps 프레임 샘플링
scoreboard + replay_logo YOLO11s detector
replay_logo 기반 replay transition / replay segment CSV 생성
scoreboard crop 생성
PaddleOCR raw OCR smoke test
score/clock parsing
OCR smoothing smoke test
score_change vs Goal label 평가 스크립트
```

현재 타겟 경기:

```text
data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley
```

## 1. 완료된 작업

### 프로젝트 기본 세팅

- [x] Git 저장소 초기화
- [x] GitHub remote 연결
- [x] Docker 기반 실행 환경 구성
- [x] GPU Docker 실행 환경 구성
- [x] `.gitignore`, `.dockerignore` 정리
- [x] SoccerNet 비밀번호 환경변수 구성
- [x] 기본 README/세팅/실행 문서 작성

### SoccerNet 데이터 준비

- [x] `verify_setup.py` 구성
- [x] SoccerNet 라이브러리 import 검증
- [x] `Labels-v2.json` 다운로드 검증
- [x] 타겟 경기 데이터 경로 확정
- [x] `data/spotting/` 구조 확인

### Phase 1A: 라벨 파서 + 프레임 샘플링

- [x] `src/data/labels.py` 구현
- [x] SoccerNet Goal/Card/Substitution label CSV 변환
- [x] `src/video/frame_sampler.py` 구현
- [x] 전반/후반 영상 자동 탐색
- [x] 1fps 프레임 샘플링
- [x] `src/phase1a.py` 통합 엔트리 구현
- [x] 타겟 경기 5400프레임 생성 확인

### Vision Detector

- [x] `src/vision/prepare_yolo_dataset.py` 구현
- [x] `src/vision/auto_label_graphics.py` 구현
- [x] `src/vision/train_detector.py` 구현
- [x] `src/vision/detect_graphics.py` 구현
- [x] `src/vision/summarize_detections.py` 구현
- [x] YOLO11n smoke training 완료
- [x] YOLO11s scoreboard training 완료
- [x] 타겟 경기 전체 scoreboard inference 완료
- [x] replay_logo strict 후보 추출
- [x] replay_logo 라벨 반영
- [x] scoreboard + replay_logo YOLO11s 재학습 완료
- [x] 타겟 경기 전체 scoreboard + replay_logo inference 완료

### Replay Event

- [x] `src/vision/extract_replay_logo_candidates.py` 구현
- [x] `src/vision/add_replay_logo_labels.py` 구현
- [x] `src/vision/build_replay_events.py` 구현
- [x] replay_logo review contact sheet 생성
- [x] replay segment review sheet 생성
- [x] 프리미어리그 중앙 전환 로고 기반 replay segment 후보 생성

### Scoreboard Crop / OCR

- [x] `src/vision/crop_detections.py` 구현
- [x] scoreboard crop smoke 생성
- [x] 타겟 경기 scoreboard crop 전체 생성
- [x] `src/ocr/run_scoreboard_ocr.py` 구현
- [x] PaddleOCR smoke test 완료
- [x] score/clock parsing 구현
- [x] `src/ocr/smooth_scoreboard_ocr.py` 구현
- [x] OCR smoothing smoke test 완료
- [x] `src/evaluation/evaluate_score_changes.py` 구현
- [x] score_change vs Goal label 평가 smoke test 완료

## 2. 바로 다음 작업

### P0. 전체 OCR 실행

- [ ] `outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv` 전체를 OCR 실행
- [ ] `outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full.csv` 생성
- [ ] OCR 결과에서 오류 행, 빈 행, 점수 파싱 성공률 확인

가이드:

```text
OCR_SCOREBOARD_TEST_GUIDE.md
```

### P0. 전체 OCR Smoothing

- [ ] 전체 OCR CSV를 smoothing
- [ ] `outputs/ocr_csv/chelsea_burnley_2015_scoreboard_smoothed.csv` 생성
- [ ] `outputs/events/chelsea_burnley_2015_score_change_events.csv` 생성
- [ ] score_change 이벤트가 실제 득점 수 2개 근처로 나오는지 확인

### P0. Goal Label 평가

- [ ] `outputs/reports/phase1a_events.csv`의 Goal label과 score_change 비교
- [ ] Recall@5/10/30s 확인
- [ ] 실패 케이스의 프레임/크롭 이미지 확인
- [ ] smoothing 파라미터 조정

### P1. OCR 품질 개선

- [ ] crop padding별 OCR 품질 비교
- [ ] 점수 영역만 잘라 읽는 secondary crop 검토
- [ ] clock OCR과 영상 timestamp 차이 분석
- [ ] 전환 그래픽/해시태그 노이즈 필터 강화
- [ ] 팀명 OCR 정규화 규칙 추가

### P1. 5경기 확장

- [ ] 같은 리그/시즌에서 5경기 선택
- [ ] 프레임 샘플링 batch 실행
- [ ] detector inference batch 실행
- [ ] scoreboard crop batch 실행
- [ ] OCR + smoothing + Goal 평가 batch 실행
- [ ] 경기별 Recall 표 생성

## 3. 주요 실행 문서

```text
PROJECT_MASTER_PLAN.md
YOLO_DATASET_TEST_GUIDE.md
OCR_SCOREBOARD_TEST_GUIDE.md
docs/PHASE_1_VISION_OCR_PIPELINE.md
docs/RESEARCH_ARCHITECTURE.md
docs/TECHNICAL_SPEC.md
REMOTE_ACCESS_GUIDE.md
```

## 4. 현재 핵심 산출물

모델:

```text
models/yolo/broadcast_graphics_yolo11s.pt
models/yolo/broadcast_graphics_yolo11s_scoreboard_replay.pt
```

탐지/이벤트:

```text
outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv
outputs/events/chelsea_burnley_2015_replay_events.csv
```

OCR 입력:

```text
outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv
```

OCR smoke:

```text
outputs/ocr_csv/chelsea_burnley_2015_scoreboard_smoke.csv
outputs/ocr_csv/chelsea_burnley_2015_scoreboard_smoke_smoothed.csv
outputs/events/chelsea_burnley_2015_score_change_smoke.csv
outputs/reports/chelsea_burnley_2015_score_change_eval_smoke.csv
```

## 5. 다음 커밋 후보

다음 코드/문서가 안정화되면 커밋합니다.

```text
src/ocr/run_scoreboard_ocr.py
src/ocr/smooth_scoreboard_ocr.py
src/evaluation/evaluate_score_changes.py
OCR_SCOREBOARD_TEST_GUIDE.md
TODO.md
PROJECT_MASTER_PLAN.md
docs/PHASE_1_VISION_OCR_PIPELINE.md
```
