# TODO

이 문서는 `my-sports-ai` 프로젝트의 완료 작업과 다음 작업을 한 번에 관리하기 위한 체크리스트입니다.

## 0. 현재 상태

2026-05-11 기준:

```text
전체 프로젝트 기준: 약 48%
Phase 1 Vision/OCR 기준: 약 83%
Vision detector 기준: 약 75%
OCR MVP 기준: 약 75%
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
highlight candidate ranking
Top-K 평가
Top-5 visual review contact sheet 생성
5경기 batch 설정
batch runner 구현
하이라이트 영상 자동 생성 설계 문서 작성
GUI 다운로드 프리셋 개선
누락 3경기 라벨/720p 영상 다운로드 완료
5경기 batch 재실행 시작
candidate 대표 timestamp score_change 우선 적용
interval 기반 Top-K 평가 적용
Top-5 review sheet +30초 프레임 추가
```

현재 타겟 경기:

```text
configs/batch_5_matches.yml의 EPL 2014-2015 5경기
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
ranked Top-5 Recall@30s: 2/2 = 1.000
5경기 Top-5 interval Recall@30s: 11/11 = 1.000
첫 골: label 13:10 -> score_change 13:21
두 번째 골: 후반 80:21 근처 scoreboard OCR 단독으로는 1-1을 안정적으로 읽지 못함
두 번째 골: 후반 80:31 VOKES text_cue로 검출
Swansea-Man United 첫 골: stale OCR 후보 smoothing 문제 수정 후 Top-5에서 검출
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
- [x] `src/events/rank_highlight_candidates.py` 구현
- [x] `src/evaluation/evaluate_topk_candidates.py` 구현
- [x] ranked Top-5 Recall@30s 2/2 확인
- [x] `src/events/render_ranked_candidates.py` 구현
- [x] Top-5 contact sheet 생성
- [x] `configs/batch_5_matches.yml` 작성
- [x] `src/pipeline/run_batch.py` 구현
- [x] `BATCH_5_MATCH_GUIDE.md` 작성
- [x] `HIGHLIGHT_VIDEO_AUTOMATION_DESIGN.md` 작성
- [x] candidate 대표 timestamp가 score_change 이후 text/replay 병합으로 밀리는 문제 수정
- [x] interval 기반 Top-K 평가 추가
- [x] review contact sheet에 +30초 프레임 추가

## 2. 바로 다음 작업

### P0. 5경기 batch 실행

- [x] 5경기 다운로드 완료 확인
- [x] 누락 3경기 `Labels-v2.json` 확인
- [x] 누락 3경기 `1_720p.mkv`, `2_720p.mkv` 확인
- [x] `--skip-existing`로 전체 pipeline 재실행 시작
- [x] `docker logs -f --tail 100 my_sports_ai_batch5`로 진행 상황 확인
- [x] batch 컨테이너 종료 상태 확인
- [x] `outputs/batch_5/batch_summary.csv` 확인
- [x] 경기별 Top-5 contact sheet 생성 확인
- [x] 실패 경기/실패 Goal 기록
- [x] Swansea-Man United 첫 골 stale score 후보 문제 수정
- [x] 5경기 Top-5 interval Recall@30s 11/11 확인

### P0. 내가 지금 해야 할 일

- [x] batch가 끝날 때까지 노트북 전원/절전 상태 유지
- [x] 주기적으로 `docker logs -f --tail 100 my_sports_ai_batch5` 확인
- [x] 완료 후 `Get-Content outputs\batch_5\batch_summary.csv` 실행
- [x] `status`가 `completed`가 아닌 경기 확인
- [x] 각 경기 `reviews/highlight_top5/contact_sheet.jpg`를 실제 영상과 비교
- [x] Top-5가 골 장면을 포함하는지 경기별로 메모 (첼시 vs 번리 검증 완료)
- [x] Burnley-Arsenal 대표 timestamp/interval 평가 문제 확인
- [x] Swansea-Man United 세 번째 골 대표 timestamp/리뷰 window 문제 확인
- [x] Swansea-Man United 첫 골 후보 rank 개선 필요 여부 확인

### P1. Highlight Video 자동 생성

- [x] `src/video/build_clip_plan.py` 구현
- [x] ranked Top-5 후보에서 `clip_plan.csv` 생성
- [x] 후보별 clip start/end가 실제 골 장면을 포함하는지 확인
- [x] `src/video/extract_highlight_clips.py` 구현
- [x] 후보별 mp4 clip 생성
- [x] `src/video/compose_highlight_video.py` 구현
- [x] 경기별 `highlight_top5.mp4` 생성
- [x] `run_batch.py`에 `clip_plan`, `clips`, `compose` stage 추가
- [x] replay 후보는 리플레이 이후가 아니라 리플레이 직전 실제 플레이 중심으로 clip window 수정
- [x] Red/Yellow card와 Substitution SoccerNet label을 highlight candidate fusion에 추가
- [x] 최종 highlight mp4 병합 순서를 rank 순서가 아니라 경기 타임라인 순서로 수정

### P1. Highlight Candidate 오탐 줄이기

- [x] Swansea-Man United 첫 골 주변 후보 rank 문제 분석
- [x] stale OCR score 후보가 실제 점수 변화로 확정되는 smoothing 문제 수정
- [x] text_cue 후보 180개를 줄이는 stopword 정리 (축구 중계/통계 용어 추가)
- [x] Chelsea/Burnley 관련 OCR 노이즈 정규화
- [x] boost token 기능을 끄고 이벤트 본연의 가치로 순위 산정
- [x] text_cue 단독 후보는 페널티(-30점)를 부여하여 강력 필터링
- [x] 하이라이트 추출 시 min_rank_score 임계값(Threshold=80) 적용

### P1. Overlay OCR 확장

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
BATCH_5_MATCH_GUIDE.md
HIGHLIGHT_VIDEO_AUTOMATION_DESIGN.md
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
outputs/events/chelsea_burnley_2015_highlight_candidates_ranked.csv
outputs/reviews/chelsea_burnley_2015_highlight_top5/contact_sheet.jpg
```

OCR:

```text
outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv
outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full.csv
outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full_reparsed.csv
outputs/ocr_csv/chelsea_burnley_2015_scoreboard_smoothed_reparsed.csv
outputs/reports/chelsea_burnley_2015_score_change_eval_reparsed.csv
outputs/reports/chelsea_burnley_2015_highlight_candidate_eval.csv
outputs/reports/chelsea_burnley_2015_highlight_topk_eval.csv
outputs/reports/chelsea_burnley_2015_highlight_topk_eval_details.csv
outputs/batch_5/batch_summary.csv
```

## 5. 다음 커밋 후보

```text
src/ocr/scoreboard_text.py
src/ocr/reparse_scoreboard_ocr.py
src/ocr/run_scoreboard_ocr.py
src/ocr/smooth_scoreboard_ocr.py
src/ocr/extract_text_cues.py
src/events/fuse_highlight_candidates.py
src/events/rank_highlight_candidates.py
src/events/render_ranked_candidates.py
src/evaluation/evaluate_score_changes.py
src/evaluation/evaluate_topk_candidates.py
src/pipeline/run_batch.py
configs/batch_5_matches.yml
BATCH_5_MATCH_GUIDE.md
HIGHLIGHT_VIDEO_AUTOMATION_DESIGN.md
OCR_SCOREBOARD_TEST_GUIDE.md
TODO.md
PROJECT_MASTER_PLAN.md
docs/PHASE_1_VISION_OCR_PIPELINE.md
```
