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
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 최초 환경 세팅 |
| [RUN_GUIDE.md](RUN_GUIDE.md) | GUI 실행과 다운로드 사용법 |
| [YOLO_DATASET_TEST_GUIDE.md](YOLO_DATASET_TEST_GUIDE.md) | YOLO 데이터셋 준비/라벨링/학습 테스트 |
| [docs/README.md](docs/README.md) | 연구 문서 인덱스 |
| [docs/RESEARCH_ARCHITECTURE.md](docs/RESEARCH_ARCHITECTURE.md) | 전체 연구 아키텍처 |
| [docs/PHASE_1_VISION_OCR_PIPELINE.md](docs/PHASE_1_VISION_OCR_PIPELINE.md) | 1순위 OCR 파이프라인 실행 명세 |
| [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md) | GPU/모델/인프라 기술 사양 |

## 3. 현재 구현 상태

전체 아키텍처 기준 현재 완성도 판단:

```text
전체 프로젝트 기준: 약 35%
Phase 1 Vision/OCR 기준: 약 55%
Vision detector 기준: 약 75%
```

요약:

```text
프레임 추출, scoreboard 탐지, replay_logo 후보 추출/검출, replay event CSV 생성까지 완료.
이제 OCR 실행과 score_change 검증으로 넘어갈 수 있는 상태.
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
replay_logo 검출 결과 review 이미지 생성
replay_segment 후보 실제 영상 구간 검증
scoreboard/replay_logo detection 기반 crop 생성
OCR CSV
OCR smoothing
Score change detection
Goal label evaluation
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

1. replay_logo detection review 이미지 생성
2. replay_segment 후보 실제 영상 구간 검증
3. scoreboard bbox crop 생성
4. PaddleOCR scoreboard OCR 실행
5. score/clock parsing 및 smoothing
6. SoccerNet Goal label 대비 score_change 검증
7. overlay 후보 추출/라벨링 전략 결정
8. 5경기 이상으로 확장

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

다음 작업은 replay_logo 이벤트 검증과 OCR 입력 생성입니다.

```text
replay_logo event review
-> replay_segment validation
-> detection crop generation
-> PaddleOCR CSV
-> OCR smoothing
-> Goal label evaluation
```
