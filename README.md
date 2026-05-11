# my-sports-ai

SoccerNet 축구 중계 영상을 내려받고, 스코어보드와 중계 그래픽 OCR을 이용해 설명 가능한 하이라이트 생성 연구를 진행하는 프로젝트입니다.

## 핵심 목표

```text
축구 중계 화면의 스코어보드, 점수 변화, 경기 시간, 리플레이/VAR/선수명 자막 같은 그래픽 OCR 정보는
설명 가능한 하이라이트 생성의 시간적 단서로 활용될 수 있는가?
```

최종 연구 주제:

```text
축구 중계 영상의 그래픽 OCR 이벤트 그래프를 이용한 설명 가능한 하이라이트 생성
```

## 현재 구현 상태

현재는 연구 데이터 수집을 위한 Streamlit GUI가 구현되어 있습니다.

주요 기능:

* SoccerNet split별 경기 목록 조회
* 리그, 시즌, 날짜, 검색어 기반 경기 필터링
* `Labels-v2.json`, 224p 영상, 720p 영상 다운로드
* 선택한 경기 기준 동일/유사 split 후보 탐색
* Docker 기반 실행
* SoccerNet 연결 검증 스크립트

## 빠른 시작

Docker Desktop을 실행한 뒤 프로젝트 루트에서 실행합니다.

```bash
docker compose up --build
```

브라우저에서 접속합니다.

```text
http://localhost:8501
```

이미 빌드가 끝난 뒤에는 다음 명령으로 실행합니다.

```bash
docker compose up
```

## 환경 변수

SoccerNet 비밀번호는 `.env` 파일에서 관리합니다.

```text
SOCCERNET_PW=
```

메일로 받은 실제 SoccerNet 비밀번호를 입력하세요. Broadcast video 다운로드는 SoccerNet NDA 승인과 올바른 비밀번호가 필요합니다.

## 데이터 저장 위치

다운로드된 데이터는 `data/spotting/` 아래에 저장됩니다.

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

## 문서 구조

| 문서 | 역할 |
|---|---|
| [PROJECT_MASTER_PLAN.md](PROJECT_MASTER_PLAN.md) | 전체 개발 우선순위와 로드맵 |
| [MDGUIDE.md](MDGUIDE.md) | 현재 상황을 이해하기 위한 문서 읽기 순서 |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 최초 환경 세팅 |
| [RUN_GUIDE.md](RUN_GUIDE.md) | GUI 실행과 다운로드 사용법 |
| [YOLO_DATASET_TEST_GUIDE.md](YOLO_DATASET_TEST_GUIDE.md) | YOLO 데이터셋 준비/라벨링/학습 테스트 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 실제 문제 원인과 해결 기록 |
| [docs/README.md](docs/README.md) | 연구 문서 인덱스 |
| [docs/RESEARCH_ARCHITECTURE.md](docs/RESEARCH_ARCHITECTURE.md) | 전체 연구 아키텍처 |
| [docs/PHASE_1_VISION_OCR_PIPELINE.md](docs/PHASE_1_VISION_OCR_PIPELINE.md) | 1순위 OCR 파이프라인 실행 명세 |
| [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md) | GPU/모델/기술 스택 사양 |

## 자주 쓰는 명령

```bash
# GUI 실행
docker compose up

# 빌드 후 GUI 실행
docker compose up --build

# 백그라운드 실행
docker compose up -d

# 로그 확인
docker compose logs -f soccernet-app

# 종료
docker compose down

# SoccerNet 연결 검증
docker compose run --rm soccernet-app python verify_setup.py
```

## 다음 개발 우선순위

다음 단계는 `docs/PHASE_1_VISION_OCR_PIPELINE.md` 기준으로 진행합니다.

```text
Frame sampling
-> Manual crop config
-> OCR CSV
-> OCR smoothing
-> Score change detection
-> Goal label evaluation
```

Phase 1A는 Docker에서 바로 실행할 수 있습니다.

```bash
docker compose run --rm soccernet-app python -m src.phase1a \
  --match-dir "data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" \
  --data-root data/spotting \
  --fps 1 \
  --max-seconds 3
```
