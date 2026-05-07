# TODO

이 문서는 `my-sports-ai` 프로젝트의 완료 작업과 다음 작업을 한 번에 관리하기 위한 체크리스트입니다.

## 0. 현재 상태

2026-05-07 기준:

```text
전체 프로젝트 기준: 약 43%
Phase 1 Vision/OCR 기준: 약 75%
Vision detector 기준: 약 75%
OCR MVP 기준: 약 65%
```

현재 완료된 큰 흐름:

```text
SoccerNet 다운로드/검증 환경
1fps 프레임 샘플링
scoreboard + replay_logo YOLO11s detector
replay_logo 기반 replay transition / replay segment CSV 생성
scoreboard crop 생성
PaddleOCR full OCR 실행
strict score/clock parsing
OCR smoothing
score_change vs Goal label 평가
text cue 추출
highlight candidate fusion
```

현재 타겟 경기:

```text
data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley
```

현재 실험 결과:

```text
OCR rows: 5277
strict parsed score rows: 3426
strict parsed clock rows: 5186
score_change events: 1
Goal labels: 2
scoreboard 단독 Recall@30s: 1/2 = 0.500
fused highlight_candidate Recall@30s: 2/2 = 1.000
첫 골: label 13:10 -> score_change 13:21
두 번째 골: 후반 80:21 근처 scoreboard OCR 단독으로는 1-1을 안정적으로 읽지 못함
두 번째 골: 후반 80:31 VOKES text_cue로 검출
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

### Vision Detector / Replay Event

- [x] `src/vision/prepare_yolo_dataset.py` 구현
- [x] `src/vision/auto_label_graphics.py` 구현
- [x] `src/vision/train_detector.py` 구현
- [x] `src/vision/detect_graphics.py` 구현
- [x] `src/vision/summarize_detections.py` 구현
- [x] `src/vision/extract_replay_logo_candidates.py` 구현
- [x] `src/vision/add_replay_logo_labels.py` 구현
- [x] `src/vision/build_replay_events.py` 구현
- [x] YOLO11n smoke training 완료
- [x] YOLO11s scoreboard training 완료
- [x] replay_logo strict 후보 추출 및 라벨 반영
- [x] scoreboard + replay_logo YOLO11s 재학습 완료
- [x] 타겟 경기 전체 scoreboard + replay_logo inference 완료
- [x] replay_logo review contact sheet 생성
- [x] replay segment review sheet 생성

### Scoreboard OCR / Evaluation

- [x] `src/vision/crop_detections.py` 구현
- [x] 타겟 경기 scoreboard crop 전체 생성
- [x] `src/ocr/run_scoreboard_ocr.py` 구현
- [x] `src/ocr/scoreboard_text.py` strict parser 구현
- [x] `src/ocr/reparse_scoreboard_ocr.py` 구현
- [x] `src/ocr/smooth_scoreboard_ocr.py` 구현
- [x] `src/evaluation/evaluate_score_changes.py` 구현
- [x] PaddleOCR full OCR 완료
- [x] 기존 OCR CSV strict 재파싱 완료
- [x] OCR smoothing 완료
- [x] Goal label 평가 완료
- [x] `src/ocr/extract_text_cues.py` 구현
- [x] `src/events/fuse_highlight_candidates.py` 구현
- [x] text_cue + score_change + replay event fusion 완료
- [x] fused highlight_candidate Recall@30s 2/2 확인

## 2. 바로 다음 작업

### P0. Highlight Candidate 오탐 줄이기

- [ ] text_cue 후보 180개를 줄이는 stopword 정리
- [ ] Chelsea/Burnley 관련 OCR 노이즈 정규화
- [ ] 후보 50개를 evidence 기반으로 ranking
- [ ] score_change 포함 후보에 높은 점수 부여
- [ ] text_cue 단독 후보는 replay_logo/시간 문맥으로 필터링

### P0. Overlay OCR 확장

- [ ] full frame 또는 lower-third 영역 crop 생성
- [ ] overlay OCR 전용 CSV 생성
- [ ] 선수명/카드/교체/골 자막 후보 분리
- [ ] 현재 scoreboard crop 기반 text_cue와 비교

### P1. OCR 품질 개선

- [ ] score 영역만 분리하는 secondary crop 검토
- [ ] overlay 영역 detector 라벨 추가
- [ ] crop padding별 OCR 품질 비교
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
outputs/events/chelsea_burnley_2015_score_change_events_reparsed.csv
outputs/events/chelsea_burnley_2015_text_cues.csv
outputs/events/chelsea_burnley_2015_highlight_candidates.csv
```

OCR:

```text
outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv
outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full.csv
outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full_reparsed.csv
outputs/ocr_csv/chelsea_burnley_2015_scoreboard_smoothed_reparsed.csv
outputs/reports/chelsea_burnley_2015_score_change_eval_reparsed.csv
outputs/reports/chelsea_burnley_2015_highlight_candidate_eval.csv
```

## 5. 다음 커밋 후보

```text
src/ocr/scoreboard_text.py
src/ocr/reparse_scoreboard_ocr.py
src/ocr/run_scoreboard_ocr.py
src/ocr/smooth_scoreboard_ocr.py
src/ocr/extract_text_cues.py
src/events/fuse_highlight_candidates.py
src/evaluation/evaluate_score_changes.py
OCR_SCOREBOARD_TEST_GUIDE.md
TODO.md
PROJECT_MASTER_PLAN.md
docs/PHASE_1_VISION_OCR_PIPELINE.md
```
