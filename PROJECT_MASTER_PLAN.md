# my-sports-ai 통합 가이드 및 개발 로드맵

이 문서는 `my-sports-ai` 프로젝트의 전체 목적, 실행 방법, 세팅 절차, 개발 우선순위, 연구 로드맵을 하나로 묶은 통합 문서입니다.

기존 문서인 `README.md`, `SETUP_GUIDE.md`, `RUN_GUIDE.md`, `docs/RESEARCH_ARCHITECTURE.md`는 그대로 유지하고, 이 문서는 전체 흐름을 한 번에 파악하기 위한 마스터 문서로 사용합니다.

## 1. 프로젝트 한 줄 요약

SoccerNet 풀 경기 영상과 라벨 데이터를 기반으로, 축구 중계 화면의 스코어보드와 자막 OCR 정보를 활용해 설명 가능한 하이라이트 생성 파이프라인을 만드는 프로젝트입니다.

## 2. 프로젝트 목표

이 프로젝트는 단순한 영상 다운로드 도구가 아니라, 국내 학회 논문을 목표로 한 연구 실험 환경입니다.

핵심 연구 질문은 다음과 같습니다.

```text
축구 중계 화면의 스코어보드, 점수 변화, 경기 시간, 리플레이/VAR/선수명 자막 같은 그래픽 OCR 정보는
설명 가능한 하이라이트 생성의 시간적 단서로 활용될 수 있는가?
```

최종 목표는 다음과 같습니다.

```text
축구 중계 영상의 그래픽 OCR 이벤트 그래프를 이용한 설명 가능한 하이라이트 생성
```

## 3. 현재 구현 상태

현재 프로젝트는 SoccerNet 데이터를 GUI에서 탐색하고 다운로드하는 기반 기능까지 구현된 상태입니다.

구현된 기능:

* Streamlit 기반 GUI 실행
* SoccerNet split별 경기 목록 조회
* `train`, `valid`, `test`, `challenge` 선택
* 리그, 시즌, 날짜, 검색어 기반 경기 필터링
* 정렬 기준과 표시 개수 조절
* 선택 경기 다운로드
  * `Labels-v2.json`
  * `1_224p.mkv`, `2_224p.mkv`
  * `1_720p.mkv`, `2_720p.mkv`
* 선택 경기 기준 동일/유사 split 후보 탐색
* Docker 기반 실행 환경
* SoccerNet 연결 검증 스크립트

아직 구현 전인 핵심 연구 기능:

* 프레임 추출
* 스코어보드 crop 설정
* OCR 실행
* OCR 결과 smoothing
* 점수 변화 탐지
* Broadcast Graphic Event Graph 생성
* 하이라이트 후보 생성
* 클립 생성
* 평가 리포트 생성

## 4. 전체 프로젝트 구조

현재 주요 구조는 다음과 같습니다.

```text
my-sports-ai/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── gui_app.py
├── verify_setup.py
├── interactive_cli.py
├── find_my_game.py
├── download_config.json
├── data/
├── docs/
│   ├── README.md
│   └── RESEARCH_ARCHITECTURE.md
├── README.md
├── SETUP_GUIDE.md
├── RUN_GUIDE.md
└── PROJECT_MASTER_PLAN.md
```

향후 연구 코드가 추가되면 다음 구조로 확장합니다.

```text
src/
  data/
    soccernet_paths.py
    labels.py
  video/
    frame_sampler.py
    clipper.py
    audio_features.py
    scene_features.py
  ocr/
    crop_config.py
    run_ocr.py
    clean_ocr.py
    smoothing.py
  graph/
    event_graph.py
    graph_schema.py
  highlight/
    candidate_generator.py
    scorer.py
    explainer.py
  evaluation/
    metrics.py
    report.py
  app/
    gui.py

outputs/
  frames/
  crops/
  ocr_csv/
  event_graphs/
  candidates/
  clips/
  reports/
```

## 5. 최초 세팅 가이드

### 5.1 사전 준비

아래 도구가 필요합니다.

```text
Docker Desktop
Docker Compose
Git
SoccerNet 데이터 접근 비밀번호
```

Docker가 정상 설치되었는지 확인합니다.

```bash
docker --version
docker compose version
```

### 5.2 프로젝트 폴더 이동

```bash
cd C:\chun\workspace\my-sports-ai
```

### 5.3 환경 변수 설정

SoccerNet 비밀번호는 `.env` 파일에서 관리합니다.

```text
SOCCERNET_PW=s0cc3rn3t
```

메일로 받은 실제 비밀번호가 있으면 `s0cc3rn3t` 값을 교체합니다.

### 5.4 Docker 이미지 빌드

처음 실행하거나 의존성을 바꾼 뒤에는 다음 명령을 실행합니다.

```bash
docker compose up --build
```

정상 실행되면 Streamlit GUI 서버가 실행됩니다.

```text
http://localhost:8501
```

### 5.5 SoccerNet 연결 검증

GUI와 별개로 SoccerNet 라이브러리 및 라벨 다운로드를 확인하려면 다음 명령을 실행합니다.

```bash
docker compose run --rm soccernet-app python verify_setup.py
```

성공 메시지:

```text
✅ SoccerNet 라이브러리가 성공적으로 로드되었습니다.
✅ API 연결 및 데이터 다운로드 테스트 성공!
```

## 6. 실행 가이드

### 6.1 GUI 실행

```bash
docker compose up
```

브라우저에서 접속합니다.

```text
http://localhost:8501
```

### 6.2 백그라운드 실행

```bash
docker compose up -d
```

로그 확인:

```bash
docker compose logs -f soccernet-app
```

종료:

```bash
docker compose down
```

### 6.3 자주 쓰는 명령

```bash
# GUI 앱 빌드 후 실행
docker compose up --build

# 기존 이미지로 GUI 실행
docker compose up

# 백그라운드 실행
docker compose up -d

# 로그 확인
docker compose logs -f soccernet-app

# 컨테이너 상태 확인
docker compose ps

# 컨테이너 종료
docker compose down

# SoccerNet 연결 검증
docker compose run --rm soccernet-app python verify_setup.py

# 기존 CLI 실행
docker compose run --rm soccernet-app python interactive_cli.py
```

## 7. GUI 사용 흐름

GUI에서 SoccerNet 경기 영상을 다운로드하는 기본 흐름은 다음과 같습니다.

1. `데이터 split`에서 `train`, `valid`, `test`, `challenge` 중 필요한 split을 선택합니다.
2. `다운로드 종류`에서 라벨, 224p 영상, 720p 영상 중 하나를 선택합니다.
3. 리그, 시즌, 날짜, 검색어로 경기 목록을 좁힙니다.
4. 정렬 기준과 표시 개수를 조절합니다.
5. 다운로드할 경기를 체크합니다.
6. 필요하면 선택 경기 기준으로 다른 split의 동일/유사 후보를 확인합니다.
7. `선택한 N경기 다운로드` 버튼을 누릅니다.

처음에는 영상 대신 `Labels-v2.json`만 받아 연결과 경로를 확인하는 것을 권장합니다.

## 8. 데이터 저장 위치

다운로드된 SoccerNet 데이터는 아래 폴더에 저장됩니다.

```text
data/spotting/
```

예상 구조:

```text
data/
└── spotting/
    └── spain_laliga/
        └── 2016-2017/
            └── 2017-02-11 - 18-15 Alaves 0 - 6 Barcelona/
                ├── Labels-v2.json
                ├── 1_720p.mkv
                └── 2_720p.mkv
```

`data/` 폴더는 대용량 파일 저장소이므로 Git 추적 대상에서 제외합니다.

## 9. 연구 아키텍처 요약

전체 연구 파이프라인은 다음 단계로 구성합니다.

```text
SoccerNet 영상/라벨 다운로드
-> 프레임 샘플링
-> 스코어보드 및 자막 영역 crop
-> OCR 실행
-> OCR 결과 정제 및 시간축 smoothing
-> Broadcast Graphic Event Graph 생성
-> 하이라이트 후보 생성
-> 후보 점수화
-> 클립 생성
-> 설명 리포트 및 평가표 생성
```

핵심 이벤트 신호:

```text
score_change
clock_state
replay_overlay
var_overlay
player_name_overlay
audio_peak
camera_cut_density
label_nearby
highlight_candidate
```

하이라이트 후보 생성 규칙 예시:

```text
Goal: timestamp - 20s ~ timestamp + 25s
Card: timestamp - 10s ~ timestamp + 15s
Substitution: timestamp - 10s ~ timestamp + 20s
Replay: replay 시작 전후 실제 event timestamp 중심
```

## 10. 개발 우선순위

### P0. 안정적인 데이터 수집 기반 유지

가장 먼저 유지해야 하는 기반입니다.

목표:

* GUI에서 원하는 경기와 파일을 안정적으로 다운로드
* `.env` 기반 SoccerNet 비밀번호 관리
* 다운로드 경로 일관성 유지
* 라벨 JSON과 영상 파일 존재 여부 검증

완료 기준:

```text
GUI로 3개 이상 경기 라벨 다운로드 성공
GUI로 1개 이상 224p 영상 다운로드 성공
선택 경기의 저장 경로가 일관됨
verify_setup.py 통과
```

### P1. Frame Sampler 구현

OCR 실험의 첫 입력을 만드는 단계입니다.

목표:

* `1_224p.mkv` 또는 `1_720p.mkv`에서 1fps 프레임 추출
* 경기별/전후반별 output 경로 생성
* 샘플링 로그 저장

권장 산출물:

```text
src/video/frame_sampler.py
outputs/frames/{match_id}/{half}/{timestamp}.jpg
outputs/reports/frame_sampling_summary.md
```

완료 기준:

```text
5경기 기준 프레임 추출 성공
프레임 timestamp와 영상 시간이 매칭됨
GUI 또는 CLI에서 실행 가능
```

### P2. Scoreboard Crop 설정

OCR 정확도는 crop 품질에 크게 좌우됩니다.

목표:

* 대표 프레임에서 scoreboard 영역 지정
* crop 좌표를 JSON으로 저장
* 같은 경기의 전체 프레임에 crop 적용

권장 산출물:

```text
src/ocr/crop_config.py
configs/crop_config.json
outputs/crops/{match_id}/{half}/{timestamp}.jpg
```

완료 기준:

```text
5경기 이상 scoreboard crop 이미지 생성
수동 확인 시 경기 시간/점수 영역이 포함됨
```

### P3. OCR Pipeline 구현

그래픽 정보를 구조화 데이터로 바꾸는 핵심 단계입니다.

목표:

* EasyOCR 또는 PaddleOCR 적용
* 시간, 점수, 팀명, 리플레이/VAR/자막 텍스트 추출
* OCR 결과를 CSV로 저장

권장 산출물:

```text
src/ocr/run_ocr.py
outputs/ocr_csv/{match_id}.csv
```

완료 기준:

```text
5경기 기준 OCR CSV 생성
score/clock 후보 컬럼 분리
OCR confidence 저장
```

### P4. OCR Cleaning 및 Temporal Smoothing

raw OCR은 오류가 많기 때문에 논문 기여를 만들기 좋은 단계입니다.

목표:

* 흔한 OCR 오류 보정
* 점수는 다수결 window로 안정화
* 경기 시간은 단조 증가하도록 보정
* 불가능한 점수 감소 제거

권장 산출물:

```text
src/ocr/clean_ocr.py
src/ocr/smoothing.py
outputs/ocr_csv/{match_id}_smoothed.csv
```

완료 기준:

```text
raw OCR 대비 score_change false positive 감소
Goal label 근처 score_change recall 측정 가능
```

### P5. Event Graph 및 Highlight Candidate 생성

연구의 핵심 차별점입니다.

목표:

* OCR, 라벨, 오디오/장면 신호를 시간축 이벤트로 통합
* Broadcast Graphic Event Graph JSON 생성
* 하이라이트 후보 timestamp 생성

권장 산출물:

```text
src/graph/event_graph.py
src/highlight/candidate_generator.py
outputs/event_graphs/{match_id}.json
outputs/candidates/{match_id}.json
```

완료 기준:

```text
score_change 기반 후보 생성
label_nearby 연결
후보별 reasons 필드 생성
```

### P6. 평가 및 논문용 리포트 생성

결과를 논문 표와 사례 분석으로 연결하는 단계입니다.

목표:

* Recall@5s, Recall@10s, Recall@30s 계산
* Precision, F1 계산
* baseline 및 ablation 결과표 생성
* 후보별 설명 리포트 생성

권장 산출물:

```text
src/evaluation/metrics.py
src/evaluation/report.py
outputs/reports/{match_id}_evaluation.md
outputs/reports/summary_table.csv
```

완료 기준:

```text
10경기 이상 평가표 생성
raw OCR vs smoothed OCR 비교
label-only baseline과 비교
실패 사례 3개 이상 정리
```

## 11. 개발 로드맵

### Milestone 1. 데이터 수집 안정화

목표 기간:

```text
1차 개발
```

작업:

* GUI 다운로드 흐름 점검
* 라벨 JSON 다운로드 안정화
* 224p 영상 다운로드 테스트
* 다운로드 메타데이터 저장

완료 산출물:

```text
5경기 라벨
1-2경기 224p 영상
다운로드 로그
```

### Milestone 2. OCR 실험 최소 버전

목표 기간:

```text
2차 개발
```

작업:

* 프레임 샘플러 구현
* 수동 scoreboard crop 구현
* OCR 엔진 1개 선택
* OCR CSV 저장

완료 산출물:

```text
outputs/frames/
outputs/crops/
outputs/ocr_csv/
```

### Milestone 3. Score Change Detection

목표 기간:

```text
3차 개발
```

작업:

* OCR cleaning 규칙 구현
* temporal smoothing 구현
* score_change timestamp 추출
* SoccerNet Goal label과 비교

완료 산출물:

```text
score_change_candidates.json
goal_recall_table.csv
raw_vs_smoothed_comparison.md
```

### Milestone 4. Broadcast Graphic Event Graph

목표 기간:

```text
4차 개발
```

작업:

* 이벤트 노드 스키마 정의
* OCR 이벤트와 라벨 이벤트 연결
* replay_overlay, var_overlay, event_text 노드 추가
* 후보별 support reason 저장

완료 산출물:

```text
outputs/event_graphs/
event_graph_schema.md
candidate_reason_examples.md
```

### Milestone 5. Highlight Generation

목표 기간:

```text
5차 개발
```

작업:

* 후보 구간 생성
* 가까운 후보 병합
* rule-based scoring
* ffmpeg 기반 클립 생성
* 후보별 explanation JSON 생성

완료 산출물:

```text
outputs/candidates/
outputs/clips/
outputs/reports/
```

### Milestone 6. 논문 실험 패키지

목표 기간:

```text
6차 개발
```

작업:

* 10-20경기 이상 평가
* baseline 비교
* ablation 실험
* 결과표 생성
* 사례 분석
* 한국어 논문 초안 작성

완료 산출물:

```text
summary_table.csv
ablation_table.csv
case_study.md
failure_analysis.md
paper_draft.md
```

## 12. 추천 개발 순서

지금 시점에서 바로 진행하기 좋은 순서는 다음과 같습니다.

1. `src/` 기본 구조 생성
2. `src/data/labels.py`로 `Labels-v2.json` 파서 구현
3. `src/video/frame_sampler.py`로 1fps 프레임 추출 구현
4. `configs/crop_config.json` 설계
5. `src/ocr/run_ocr.py` 최소 OCR 실행 구현
6. `src/ocr/smoothing.py`로 score smoothing 구현
7. `src/highlight/candidate_generator.py`로 Goal 후보 생성
8. `src/evaluation/metrics.py`로 Recall@k 평가
9. GUI에 `OCR 실험 실행` 버튼 추가
10. 결과 리포트 자동 생성

가장 먼저 만들 파일:

```text
src/data/labels.py
src/video/frame_sampler.py
src/ocr/crop_config.py
src/ocr/run_ocr.py
src/evaluation/metrics.py
```

## 13. 논문 실험 우선순위

논문 가능성을 빠르게 확인하려면 처음부터 모든 이벤트를 다루지 말고 Goal 중심으로 시작합니다.

### 13.1 최소 성공 실험

데이터:

```text
5-10경기
Labels-v2.json
224p 또는 720p 영상
```

실험:

```text
scoreboard OCR -> score_change 탐지 -> SoccerNet Goal label과 비교
```

평가:

```text
Recall@5s
Recall@10s
Recall@30s
False positive per match
```

### 13.2 확장 실험

추가 신호:

```text
replay_overlay
VAR text
event subtitle
audio_peak
camera_cut_density
```

비교:

```text
Raw OCR
Smoothed OCR
Label-only
OCR + replay
OCR + replay + audio
Broadcast Graphic Event Graph
```

## 14. 성공 기준

### 최소 성공 기준

```text
10경기 이상 실험
Goal detection 성능 표
OCR smoothing ablation
하이라이트 후보 JSON
설명 report 예시
```

### 강한 논문 기준

```text
30-50경기 실험
Goal + replay + card/substitution 일부 포함
Broadcast Graphic Event Graph 시각화
baseline 4개 이상 비교
실패 사례 분석
mini benchmark 정리
하이라이트 클립 데모
```

## 15. 위험 요소와 대응

| 위험 요소 | 영향 | 대응 |
|---|---|---|
| OCR 정확도 낮음 | score_change 탐지 실패 | crop 품질 개선, temporal smoothing, 경기별 crop config |
| 스코어보드 위치가 경기마다 다름 | 자동화 어려움 | 초기에는 수동 crop, 이후 template/profile 방식 |
| 720p 영상 용량이 큼 | 다운로드/처리 시간 증가 | 초기 실험은 224p 또는 소수 경기로 제한 |
| SoccerNet 비밀번호/권한 문제 | 영상 다운로드 실패 | 라벨 JSON으로 먼저 실험, 권한 확인 후 영상 확장 |
| Goal 외 이벤트 OCR 신호 약함 | Card/Substitution 성능 낮음 | 1차 논문은 Goal 중심, 확장 실험으로 처리 |
| 논문 기여가 단순 규칙으로 보일 수 있음 | 연구성 약화 | Event Graph, smoothing ablation, explanation report 강조 |

## 16. 문서 사용법

각 문서의 역할은 다음과 같습니다.

| 문서 | 역할 |
|---|---|
| `README.md` | 프로젝트 소개와 빠른 시작 |
| `SETUP_GUIDE.md` | 최초 세팅 절차 |
| `RUN_GUIDE.md` | GUI 실행과 다운로드 사용법 |
| `docs/RESEARCH_ARCHITECTURE.md` | 연구 아키텍처와 실험 설계 상세 |
| `PROJECT_MASTER_PLAN.md` | 전체 통합 가이드, 개발 우선순위, 로드맵 |

앞으로 개발 중 방향을 잃으면 이 문서의 `개발 우선순위`와 `개발 로드맵`을 기준으로 다음 작업을 결정합니다.
