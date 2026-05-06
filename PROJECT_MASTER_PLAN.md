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

완료:

```text
Streamlit GUI
SoccerNet 경기 목록 조회
split/리그/시즌/날짜/검색어 필터
Labels-v2.json, 224p, 720p 다운로드
Docker 실행 환경
SoccerNet 검증 스크립트
```

다음 구현 대상:

```text
Labels-v2.json parser
Frame sampler
Phase 1A Docker entrypoint
Manual crop config
YOLO11s detector dataset
YOLO11s detector training
OCR CSV
Replay logo boundary detection
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
100장 이상 YOLO 학습 데이터 구성
models/yolo/broadcast_graphics_yolo11s.pt 생성
타겟 경기 detection CSV 생성
수동 crop 결과와 detector bbox 비교
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

1. `src/` 기본 구조 생성
2. `src/data/labels.py` 구현
3. `src/video/frame_sampler.py` 구현
4. `src/phase1a.py` Docker 실행 검증
5. `configs/crop_config.json` 설계
6. `src/ocr/crop_config.py` 구현
7. `scoreboard`, `overlay`, `replay_logo` crop 생성 검증
8. `datasets/yolo_broadcast_graphics` 구조 생성
9. 라벨링용 대표 프레임 100장 추출
10. YOLO 3-class bbox 라벨링
11. `src/vision/train_detector.py` 구현
12. YOLO11s 학습
13. `src/vision/detect_graphics.py` 구현
14. detection 결과로 PaddleOCR 실행
15. `src/ocr/run_ocr.py` 구현
16. `src/ocr/clean_ocr.py` 구현
17. `src/ocr/smoothing.py` 구현
18. `src/evaluation/metrics.py` 구현
19. `outputs/reports/phase1_goal_recall_table.csv` 생성
20. GUI에 `OCR 실험 실행` 버튼 추가

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

다음 작업은 `docs/PHASE_1_VISION_OCR_PIPELINE.md`의 MVP 범위부터 시작합니다.

```text
Frame sampling
-> Manual crop config
-> PaddleOCR CSV
-> OCR smoothing
-> Goal label evaluation
```
