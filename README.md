# my-sports-ai

SoccerNet 풀 경기 영상을 다운로드하고, 중계 그래픽 OCR을 활용해 설명 가능한 축구 하이라이트 생성 연구를 진행하기 위한 프로젝트입니다.

현재 구현된 기능은 SoccerNet 경기 목록을 GUI에서 검색, 선별, 정렬하고 원하는 경기의 풀 영상 또는 라벨 파일을 다운로드하는 것입니다. 연구 목표는 이후 이 데이터를 이용해 **Broadcast Graphic OCR Event Graph** 기반 하이라이트 탐지 파이프라인을 구축하는 것입니다.

## 프로젝트 목표

이 프로젝트는 단순한 영상 다운로드 도구가 아니라, 국내 학회 논문을 목표로 한 연구 실험 환경입니다.

핵심 연구 질문은 다음과 같습니다.

```text
축구 중계 화면의 스코어보드, 점수 변화, 경기 시간, 리플레이/VAR/선수명 자막 같은 그래픽 OCR 정보는
설명 가능한 하이라이트 생성의 시간적 단서로 활용될 수 있는가?
```

## 주요 기능

- SoccerNet split별 경기 목록 조회
- `train`, `valid`, `test`, `challenge` 선택
- 리그, 시즌, 날짜, 검색어 기반 경기 선별
- 정렬 기준과 표시 개수 조절
- 풀 경기 영상 다운로드
  - `1_720p.mkv`
  - `2_720p.mkv`
- 저해상도 영상 다운로드
  - `1_224p.mkv`
  - `2_224p.mkv`
- Action spotting 라벨 다운로드
  - `Labels-v2.json`
- 선택한 경기를 기준으로 전체 split의 동일/유사 후보 탐색
- Streamlit 기반 GUI 실행

## 빠른 시작

Docker Desktop을 켠 뒤 프로젝트 루트에서 실행합니다.

```bash
docker compose up --build
```

브라우저에서 아래 주소를 엽니다.

```text
http://localhost:8501
```

이미 빌드가 끝난 뒤에는 다음 명령으로 실행할 수 있습니다.

```bash
docker compose up
```

## SoccerNet 비밀번호

SoccerNet 데이터 접근 비밀번호는 `.env` 파일에서 관리합니다.

```text
SOCCERNET_PW=
```

Broadcast video 다운로드는 SoccerNet NDA 승인과 올바른 비밀번호가 필요합니다.

## 다운로드 데이터 위치

다운로드된 데이터는 아래 폴더에 저장됩니다.

```text
data/spotting/
```

예상 구조는 다음과 같습니다.

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

## 문서 구조

| 문서 | 역할 |
|---|---|
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 최초 환경 세팅 |
| [RUN_GUIDE.md](RUN_GUIDE.md) | GUI 실행 및 다운로드 사용법 |
| [docs/RESEARCH_ARCHITECTURE.md](docs/RESEARCH_ARCHITECTURE.md) | 논문 연구 아키텍처와 실험 설계 |
| [docs/README.md](docs/README.md) | 연구 문서 인덱스 |

## 코드 구조

현재 주요 파일은 다음과 같습니다.

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
└── RUN_GUIDE.md
```

향후 연구 코드가 추가되면 아래 구조로 확장할 계획입니다.

```text
src/
  data/
  video/
  ocr/
  graph/
  highlight/
  evaluation/
outputs/
  frames/
  crops/
  ocr_csv/
  event_graphs/
  clips/
  reports/
```

## 연구 방향

논문 방향은 다음 주제로 정리합니다.

```text
축구 중계 영상의 그래픽 OCR 이벤트 그래프를 이용한 설명 가능한 하이라이트 생성
```

핵심 아이디어는 다음과 같습니다.

1. 풀 경기 영상에서 프레임을 샘플링합니다.
2. 스코어보드와 중계 자막 영역을 OCR로 읽습니다.
3. 점수 변화, 경기 시간 변화, 리플레이/VAR/이벤트 자막을 시간축 이벤트로 변환합니다.
4. 이 이벤트들을 Broadcast Graphic Event Graph로 구조화합니다.
5. 그래프 기반으로 하이라이트 후보를 생성하고, 선택 이유를 함께 출력합니다.

자세한 설계는 [docs/RESEARCH_ARCHITECTURE.md](docs/RESEARCH_ARCHITECTURE.md)를 참고하세요.

## 자주 쓰는 명령

```bash
# 빌드 후 GUI 실행
docker compose up --build

# 기존 이미지로 GUI 실행
docker compose up

# 백그라운드 실행
docker compose up -d

# 로그 확인
docker compose logs -f soccernet-app

# 컨테이너 종료
docker compose down

# SoccerNet 연결 검증
docker compose run --rm soccernet-app python verify_setup.py
```

## 주의사항

- 풀 영상은 용량이 큽니다. 처음에는 `Labels-v2.json` 또는 224p 영상으로 테스트하는 것을 권장합니다.
- SoccerNet split은 보통 서로 겹치지 않게 구성되어 있어 동일 경기가 다른 split에 없을 수 있습니다.
- `data/` 폴더에는 대용량 파일이 저장되므로 Git 추적 대상에서 제외합니다.
