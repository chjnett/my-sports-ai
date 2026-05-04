# SoccerNet GUI 다운로드 실행 가이드

이 문서는 SoccerNet 경기 풀 영상을 GUI에서 검색하고 선택해 다운로드하는 방법을 정리합니다.

## 1. 준비 확인

프로젝트 루트 폴더에서 실행합니다.

```bash
cd C:\chun\workspace\my-sports-ai
```

Docker Desktop이 켜져 있어야 합니다.

SoccerNet 비밀번호는 `.env` 파일에서 읽습니다.

```text
SOCCERNET_PW=s0cc3rn3t
```

비밀번호를 새로 받았다면 `.env`의 값을 바꾸면 됩니다.

## 2. 처음 실행 또는 다시 빌드

처음 실행하거나 `requirements.txt`, `Dockerfile`, `docker-compose.yml`을 바꾼 뒤에는 빌드와 실행을 같이 합니다.

```bash
docker compose up --build
```

정상 실행되면 로그에 Streamlit 주소가 표시됩니다.

```text
Local URL: http://localhost:8501
```

브라우저에서 아래 주소를 엽니다.

```text
http://localhost:8501
```

## 3. 이미 빌드된 상태에서 실행

이미 한 번 빌드가 끝났다면 다음 명령만 사용해도 됩니다.

```bash
docker compose up
```

터미널을 계속 차지하지 않게 백그라운드로 실행하려면 다음 명령을 사용합니다.

```bash
docker compose up -d
```

백그라운드 실행 후 로그를 보려면 다음 명령을 사용합니다.

```bash
docker compose logs -f soccernet-app
```

## 4. GUI에서 풀 영상 다운로드하는 방법

1. 왼쪽 사이드바의 `1. 데이터 split`에서 `train`, `valid`, `test`, `challenge` 중 필요한 항목을 선택합니다.
2. 왼쪽 사이드바의 `2. 다운로드 종류`에서 `풀 경기 영상 720p`를 선택합니다.
3. 본문 `3. 선별 조건`에서 검색어, 리그, 시즌, 날짜 범위로 목록을 줄입니다.
4. `정렬 기준`과 `정렬 방향`으로 원하는 순서로 정렬합니다.
5. `화면에 표시할 개수`를 조절해서 한 번에 볼 경기 수를 정합니다.
6. 중앙 테이블에서 다운로드할 경기의 `선택` 체크박스를 켭니다.
7. 필요하면 `5. 선택한 경기 기준으로 split 찾기`에서 체크한 경기 중 하나를 기준으로 다른 split의 동일/유사 후보를 확인합니다.
8. 아래쪽의 `선택한 N경기 다운로드` 버튼을 누릅니다.

`풀 경기 영상 720p`는 아래 두 파일을 같이 다운로드합니다.

```text
1_720p.mkv : 전반전 풀 영상
2_720p.mkv : 후반전 풀 영상
```

SoccerNet의 broadcast video는 NDA 승인과 올바른 `SOCCERNET_PW`가 필요합니다.

## 5. 선별과 정렬 팁

데이터가 많을 때는 아래 순서로 줄이면 편합니다.

```text
1. split을 먼저 좁히기
2. 리그 선택
3. 시즌 선택
4. 팀 이름이나 날짜를 검색어로 입력
5. 날짜 또는 경기명 기준으로 정렬
```

현재 표시된 목록을 한 번에 모두 고르려면 `현재 목록 전체 선택`을 누릅니다.

선택을 다시 시작하려면 `선택 초기화`를 누릅니다.

## 6. 동일 경기 split 찾기

`5. 선택한 경기 기준으로 split 찾기`는 위 경기 선택 테이블에서 체크한 경기 중 하나를 기준으로 전체 split에서 관련 후보를 찾는 도구입니다.

```text
1. 검색/리그/시즌/날짜 필터로 기준 경기를 먼저 좁힙니다.
2. `4. 경기 선택` 테이블에서 기준으로 삼을 경기를 체크합니다.
3. `선택한 경기 중 하나로 다른 split 후보 찾기`를 엽니다.
4. `기준 경기` 드롭다운에서 체크한 경기 중 하나를 고릅니다.
5. 아래 표에서 전체 split의 동일 경기 또는 유사 후보를 확인합니다.
```

완전히 같은 영상은 SoccerNet 경로가 같은 항목입니다.

다른 split에 완전히 동일한 경로가 없다면, 앱은 같은 리그/시즌에서 팀명이 겹치는 후보를 같이 보여줍니다.

참고로 `train`, `valid`, `test`, `challenge`는 보통 서로 겹치지 않게 나누기 때문에 동일 영상이 다른 split에 없을 수 있습니다.

## 7. 다른 데이터 다운로드 모드

파일 종류 예시는 다음과 같습니다.

```text
1_720p.mkv     : 전반전 720p 영상
2_720p.mkv     : 후반전 720p 영상
1_224p.mkv     : 전반전 저해상도 미리보기
2_224p.mkv     : 후반전 저해상도 미리보기
Labels-v2.json : Action spotting 라벨 JSON
```

GUI의 `다운로드 종류`에서 다음 모드를 고를 수 있습니다.

```text
풀 경기 영상 720p  : 1_720p.mkv, 2_720p.mkv
저해상도 영상 224p : 1_224p.mkv, 2_224p.mkv
라벨 JSON만        : Labels-v2.json
직접 선택          : 원하는 파일을 직접 체크
```

영상 파일은 용량이 큽니다. 처음 연결만 확인하고 싶을 때는 `라벨 JSON만`으로 테스트한 뒤 풀 영상을 받으면 됩니다.

## 8. 다운로드 저장 위치

다운로드된 데이터는 프로젝트의 `data/spotting` 폴더에 저장됩니다.

```text
C:\chun\workspace\my-sports-ai\data\spotting
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

## 9. 종료와 재시작

실행 중인 앱을 종료하려면 다음 명령을 사용합니다.

```bash
docker compose down
```

다시 실행하려면 다음 명령을 사용합니다.

```bash
docker compose up
```

현재 컨테이너 상태를 확인하려면 다음 명령을 사용합니다.

```bash
docker compose ps
```

## 10. 검증 명령

SoccerNet 라이브러리와 다운로드 연결을 확인하려면 다음 명령을 실행합니다.

```bash
docker compose run --rm soccernet-app python verify_setup.py
```

기존 터미널형 선택 도구를 실행하려면 다음 명령을 사용합니다.

```bash
docker compose run --rm soccernet-app python interactive_cli.py
```

SoccerNet 라이브러리 import만 확인하려면 다음 명령을 사용할 수 있습니다.

```bash
docker compose run --rm soccernet-app python -c "import SoccerNet; print('SoccerNet OK')"
```

## 11. 자주 쓰는 명령

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

# Docker Compose 설정 확인
docker compose config
```

## 12. 문제 해결

### 브라우저에서 `localhost:8501`이 열리지 않는 경우

컨테이너가 실행 중인지 확인합니다.

```bash
docker compose ps
```

실행 중이 아니라면 다시 시작합니다.

```bash
docker compose up
```

### 패키지 import 에러가 나는 경우

이미지가 오래됐을 수 있습니다. 다시 빌드합니다.

```bash
docker compose up --build
```

### 다운로드가 실패하는 경우

아래 항목을 확인합니다.

```text
1. .env의 SOCCERNET_PW 값
2. 네트워크 연결 상태
3. SoccerNet 서버 접근 가능 여부
4. data 폴더 쓰기 권한
5. 선택한 파일이 해당 경기 split에서 제공되는지 여부
```

### 경기 목록이 너무 많이 나오는 경우

검색어를 더 구체적으로 입력합니다.

```text
Barcelona
Chelsea
2016-2017
spain_laliga
2017-02-11
```
