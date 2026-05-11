# 프로젝트 마스터 플랜

이 문서는 `my-sports-ai`의 전체 개발 우선순위와 연구 로드맵을 한 번에 보기 위한 통합 문서입니다.

## 1. 프로젝트 목표

SoccerNet 풀 경기 영상과 라벨 데이터를 기반으로, 축구 중계 화면의 그래픽 OCR 정보를 시간축 이벤트 그래프로 구조화하고 설명 가능한 하이라이트 후보를 생성합니다.

핵심 연구 질문:

```text
중계 화면의 스코어보드, 점수 변화, 경기 시간, 리플레이/VAR/선수명 자막 같은 OCR 정보는
축구 하이라이트 탐지의 신뢰 가능한 시간적 단서가 될 수 있는가?
```

## 2. 문서 역할

| 문서 | 역할 |
|---|---|
| [README.md](README.md) | 프로젝트 소개와 빠른 시작 |
| [MDGUIDE.md](MDGUIDE.md) | 현재 상황을 이해하기 위한 문서 읽기 순서 |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 최초 환경 세팅 |
| [RUN_GUIDE.md](RUN_GUIDE.md) | GUI 실행과 다운로드 사용법 |
| [YOLO_DATASET_TEST_GUIDE.md](YOLO_DATASET_TEST_GUIDE.md) | YOLO 데이터셋 준비/라벨링/학습 테스트 |
| [OCR_SCOREBOARD_TEST_GUIDE.md](OCR_SCOREBOARD_TEST_GUIDE.md) | scoreboard OCR/smoothing/Goal 평가 실행 |
| [BATCH_5_MATCH_GUIDE.md](BATCH_5_MATCH_GUIDE.md) | 5경기 batch 검증 실행 |
| [HIGHLIGHT_VIDEO_AUTOMATION_DESIGN.md](HIGHLIGHT_VIDEO_AUTOMATION_DESIGN.md) | 하이라이트 clip/영상 자동 생성 설계 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 실제 문제 원인과 해결 기록 |
| [docs/README.md](docs/README.md) | 연구 문서 인덱스 |
| [docs/RESEARCH_ARCHITECTURE.md](docs/RESEARCH_ARCHITECTURE.md) | 전체 연구 아키텍처 |
| [docs/PHASE_1_VISION_OCR_PIPELINE.md](docs/PHASE_1_VISION_OCR_PIPELINE.md) | 1순위 OCR 파이프라인 실행 명세 |
| [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md) | GPU/모델/인프라 기술 사양 |

## 3. 현재 구현 상태

전체 아키텍처 기준 현재 완성도 판단:

```text
전체 프로젝트 기준: 약 52%
Phase 1 Vision/OCR 기준: 약 88%
Vision detector 기준: 약 75%
OCR MVP 기준: 약 82%
```

요약:

```text
프레임 추출, scoreboard 탐지, replay_logo 후보 추출/검출, replay event CSV 생성까지 완료.
scoreboard crop, PaddleOCR full OCR, strict score 재파싱, smoothing까지 완료.
현재 scoreboard 단독 Recall@30s는 1/2.
text_cue와 결합한 highlight_candidate 기준 Recall@30s는 2/2.
ranked Top-5 기준 Recall@30s도 2/2.
두 번째 골은 VOKES text cue로 잡힘.
5경기 batch runner와 하이라이트 영상 자동 생성 설계까지 준비됨.
누락됐던 3경기 다운로드를 완료했고, 5경기 batch 정상 완료.
candidate 대표 timestamp, interval 기반 평가, stale OCR smoothing 문제를 수정해 5경기 Top-5 Recall@30s는 11/11 = 1.000.
```

완료:

```text
Streamlit GUI
SoccerNet 경기 목록 조회
split/리그/시즌/날짜/검색어 필터
Labels-v2.json, 224p, 720p 다운로드
Docker 실행 환경
SoccerNet 검증 스크립트
Phase 1A 라벨 파서
Phase 1A 프레임 샘플러
YOLO11s scoreboard detector 학습
타겟 경기 5400프레임 scoreboard inference
replay_logo 후보 추출
replay_logo strict 후보 12장 라벨 반영
scoreboard + replay_logo YOLO11s 재학습
scoreboard crop 전체 생성
PaddleOCR scoreboard OCR smoke test
OCR smoothing smoke test
score_change vs Goal label 평가 smoke test
strict score parser
기존 OCR CSV 재파싱 도구
text_cue 추출
score_change + text_cue + replay event fusion
highlight candidate ranking
Top-K Recall 평가
Top-5 visual review contact sheet
5경기 batch 설정
batch runner
```

현재 모델 산출물:

```text
models/yolo/broadcast_graphics_yolo11s.pt
models/yolo/broadcast_graphics_yolo11s_scoreboard_replay.pt
```

현재 주요 데이터셋:

```text
datasets/yolo_broadcast_graphics
datasets/yolo_broadcast_graphics_merged
datasets/yolo_broadcast_graphics_replay_logo
datasets/yolo_broadcast_graphics_scoreboard_replay
```

다음 구현 대상:

```text
5경기 다운로드 완료 확인
batch 실행
경기별 Top-5 Recall@30s 비교
실패 사례 수집
```

## 4. 개발 우선순위

### P0. 데이터 수집 안정화

목표:

```text
GUI로 원하는 경기와 파일을 안정적으로 다운로드
.env 기반 SoccerNet 비밀번호 관리
다운로드 경로 일관성 유지
verify_setup.py 통과
```

완료 기준:

```text
3경기 이상 Labels-v2.json 다운로드
1경기 이상 224p 영상 다운로드
data/spotting 경로 구조 확인
```

### P1. Phase 1 OCR MVP

기준 문서:

```text
docs/PHASE_1_VISION_OCR_PIPELINE.md
```

목표:

```text
OpenCV/ffmpeg 기반 1fps 프레임 추출
수동 scoreboard crop
수동 replay_logo crop
PaddleOCR CSV 생성
프리미어리그 중앙 전환 로고 기반 replay_segment 후보 생성
OCR cleaning 및 temporal smoothing
Goal label 대비 Recall@5/10/30s 평가
```

현재 완료:

```text
src/data/labels.py
src/video/frame_sampler.py
src/phase1a.py
Docker 기반 Phase 1A 실행 검증
src/vision/prepare_yolo_dataset.py
src/vision/auto_label_graphics.py
src/vision/train_detector.py
src/vision/detect_graphics.py
src/vision/summarize_detections.py
src/vision/pseudo_label_graphics.py
src/vision/merge_yolo_datasets.py
src/vision/extract_replay_logo_candidates.py
src/vision/add_replay_logo_labels.py
src/vision/build_replay_events.py
src/vision/crop_detections.py
src/ocr/run_scoreboard_ocr.py
src/ocr/reparse_scoreboard_ocr.py
src/ocr/scoreboard_text.py
src/ocr/smooth_scoreboard_ocr.py
src/evaluation/evaluate_score_changes.py
```

완료 기준:

```text
5-10경기 기준 OCR CSV 생성
raw OCR vs smoothed OCR 비교표 생성
Goal score_change recall 계산
실패 사례 정리
```

### P2. YOLO11s 자동 탐지

목표:

```text
scoreboard / overlay / replay_logo 3-class detector
YOLO11s 기본 모델 학습
YOLO11n 빠른 테스트 모델 학습
30경기 batch inference용 outputs/detections 생성
```

완료 기준:

```text
scoreboard detector 학습 완료
replay_logo 후보 라벨 반영 완료
scoreboard + replay_logo detector 재학습 완료
타겟 경기 scoreboard detection CSV 생성 완료
다음: scoreboard + replay_logo 전체 inference 결과 검증
```

### P2-2. PaddleOCR GPU OCR

목표:

```text
PaddleOCR PP-OCRv5 server 적용
PP-OCRv5 mobile 빠른 실험 옵션 유지
scoreboard/overlay detected crop 대상 OCR 실행
```

완료 기준:

```text
타겟 경기 OCR CSV 생성
score/clock 후보 컬럼 분리
30경기 batch OCR 실행 설계
```

### P3. Event Graph

목표:

```text
score_state
score_change
replay_overlay
label_nearby
highlight_candidate
```

완료 기준:

```text
경기별 event_graph.json 생성
candidate별 reasons 필드 생성
```

### P4. Highlight Generation

목표:

```text
후보 구간 생성
후보 병합
rule-based scoring
ffmpeg 클립 생성
설명 리포트 생성
```

완료 기준:

```text
outputs/candidates 생성
outputs/clips 생성
outputs/reports 생성
```

### P5. 논문 실험 패키지

목표:

```text
10-20경기 이상 실험
baseline 비교
ablation 실험
결과표 생성
사례 분석
한국어 논문 초안 작성
```

완료 기준:

```text
goal_recall_table.csv
ablation_table.csv
case_study.md
failure_analysis.md
paper_draft.md
```

## 5. 권장 개발 순서

바로 다음에 진행할 순서:

1. match-level Recall@30s 표 고정
2. 실패 사례와 OCR 오탐 원인 정리
3. `clip_plan` 설계 기준으로 하이라이트 영상 자동 생성 MVP 구현
4. 후보별 mp4 clip 생성 및 경기별 `highlight_top5.mp4` 병합
5. text cue 오탐/저랭크 후보 정리
6. 10경기 이상으로 batch 확장

## 6. 연구 로드맵

### Milestone 1. 데이터 수집

```text
5경기 라벨 다운로드
1-2경기 224p 영상 다운로드
다운로드 경로 검증
```

### Milestone 2. OCR MVP

```text
1fps 프레임 추출
수동 crop
PaddleOCR CSV
Premier League replay transition logo detection
OCR smoothing
```

### Milestone 3. Goal Detection

```text
score_change timestamp 추출
SoccerNet Goal label과 비교
Recall@5/10/30s 계산
```

### Milestone 4. Event Graph

```text
OCR event
label_nearby
replay_overlay
replay_transition_logo
replay_segment
highlight_candidate
reasons
```

### Milestone 5. Highlight Clip

```text
candidate scoring
clip cutting
explanation json
evaluation report
```

### Milestone 6. Paper Package

```text
architecture figure
event graph figure
result tables
case studies
failure analysis
논문 초안
```

## 7. 성공 기준

최소 성공:

```text
10경기 이상 실험
Goal detection 성능 표
OCR smoothing ablation
하이라이트 후보 JSON
설명 report 예시
```

강한 논문:

```text
30-50경기 실험
Goal + replay + card/substitution 일부 포함
Broadcast Graphic Event Graph 시각화
baseline 4개 이상 비교
실패 사례 분석
하이라이트 클립 데모
```

## 8. 위험 요소와 대응

| 위험 요소 | 영향 | 대응 |
|---|---|---|
| OCR 정확도 낮음 | score_change 탐지 실패 | crop 개선, smoothing, 경기별 config |
| 스코어보드 위치 다양 | 자동화 어려움 | MVP는 수동 crop, 이후 YOLO 확장 |
| 영상 용량 큼 | 처리 지연 | 초기 실험은 224p와 소수 경기로 제한 |
| GPU 환경 충돌 | 개발 지연 | 기존 Dockerfile 유지, GPU Dockerfile 분리 |
| 논문 기여 약화 | 연구성 부족 | Event Graph, ablation, explanation report 강조 |

## 9. 다음 행동

다음 작업은 하이라이트 영상 자동 생성 MVP입니다.

```text
match-level result table
-> clip_plan generation
-> clip extraction
-> highlight_top5.mp4 composition
-> text cue / score_change ranking improvement
```
