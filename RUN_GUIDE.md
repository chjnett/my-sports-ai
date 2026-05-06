# 실행 가이드

이 문서는 SoccerNet GUI 다운로드 도구를 실행하고 사용하는 방법을 정리합니다.

## 1. 실행 전 확인

프로젝트 루트에서 실행합니다.

```bash
cd C:\chun\workspace\my-sports-ai
```

Docker Desktop이 켜져 있어야 하며, SoccerNet 비밀번호는 `.env` 파일에서 읽습니다.

```text
SOCCERNET_PW=
```

## 2. 처음 실행 또는 재빌드

처음 실행하거나 `requirements.txt`, `Dockerfile`, `docker-compose.yml`을 수정한 뒤에는 다음 명령을 사용합니다.

```bash
docker compose up --build
```

정상 실행되면 Streamlit 주소가 표시됩니다.

```text
http://localhost:8501
```

## 3. 일반 실행

이미 빌드가 끝난 상태라면 다음 명령만 사용합니다.

```bash
docker compose up
```

백그라운드 실행:

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

## 4. GUI 다운로드 흐름

1. `데이터 split`에서 `train`, `valid`, `test`, `challenge` 중 필요한 split을 선택합니다.
2. `다운로드 종류`에서 필요한 파일 종류를 선택합니다.
3. 검색어, 리그, 시즌, 날짜 범위로 경기 목록을 좁힙니다.
4. 정렬 기준과 표시 개수를 조절합니다.
5. 다운로드할 경기의 `선택` 체크박스를 켭니다.
6. 필요하면 선택 경기 기준으로 다른 split의 동일/유사 후보를 확인합니다.
7. `선택한 N경기 다운로드` 버튼을 누릅니다.

## 5. 다운로드 모드

GUI에서 선택할 수 있는 주요 파일 종류:

```text
Labels-v2.json : Action spotting 라벨
1_224p.mkv     : 전반전 저해상도 영상
2_224p.mkv     : 후반전 저해상도 영상
1_720p.mkv     : 전반전 720p 영상
2_720p.mkv     : 후반전 720p 영상
```

처음에는 `Labels-v2.json` 또는 224p 영상으로 연결과 경로를 확인하는 것을 권장합니다.

## 6. 데이터 저장 위치

다운로드된 데이터는 프로젝트의 `data/spotting` 폴더에 저장됩니다.

```text
C:\chun\workspace\my-sports-ai\data\spotting
```

예상 구조:

```text
data/
└── spotting/
    └── england_epl/
        └── 2014-2015/
            └── 2015-04-11 - 19-30 Burnley 0 - 1 Arsenal/
                ├── Labels-v2.json
                ├── 1_720p.mkv
                └── 2_720p.mkv
```

## 7. 검증 명령

SoccerNet 연결 검증:

```bash
docker compose run --rm soccernet-app python verify_setup.py
```

기존 터미널형 선택 도구 실행:

```bash
docker compose run --rm soccernet-app python interactive_cli.py
```

SoccerNet import만 확인:

```bash
docker compose run --rm soccernet-app python -c "import SoccerNet; print('SoccerNet OK')"
```

## 8. 자주 쓰는 명령

```bash
# GUI 앱 빌드 후 실행
docker compose up --build

# GUI 앱 실행
docker compose up

# GUI 앱 백그라운드 실행
docker compose up -d

# 로그 확인
docker compose logs -f soccernet-app

# 컨테이너 상태 확인
docker compose ps

# 앱 종료
docker compose down

# Compose 설정 확인
docker compose config
```

## 9. 문제 해결

### 브라우저에서 `localhost:8501`이 열리지 않는 경우

컨테이너 상태를 확인합니다.

```bash
docker compose ps
```

실행 중이 아니라면 다시 시작합니다.

```bash
docker compose up
```

### 패키지 import 에러가 나는 경우

이미지가 오래됐을 수 있습니다.

```bash
docker compose up --build
```

### 다운로드가 실패하는 경우

아래 항목을 확인합니다.

```text
.env의 SOCCERNET_PW 값
네트워크 연결 상태
SoccerNet 서버 접근 가능 여부
data 폴더 쓰기 권한
선택한 파일이 해당 split에서 제공되는지 여부
```

## 10. 다음 단계

데이터 다운로드가 안정화되면 [docs/PHASE_1_VISION_OCR_PIPELINE.md](docs/PHASE_1_VISION_OCR_PIPELINE.md)를 기준으로 OCR 파이프라인을 구현합니다.

Phase 1A 라벨 파싱과 프레임 샘플링은 Docker 안에서 실행합니다.

```bash
docker compose run --rm soccernet-app python -m src.phase1a \
  --match-dir "data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" \
  --data-root data/spotting \
  --fps 1 \
  --max-seconds 3
```

전체 영상을 처리할 때는 `--max-seconds`를 제거합니다.
