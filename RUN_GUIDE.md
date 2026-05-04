# SoccerNet 프로젝트 실행 가이드

이 문서는 세팅이 끝난 뒤 프로젝트를 빌드, 실행, 검증, 재실행하는 방법을 정리합니다.

## 1. 기본 실행

프로젝트 루트에서 실행합니다.

```bash
docker compose up
```

코드나 Dockerfile 변경 후 새로 빌드하려면 다음 명령을 사용합니다.

```bash
docker compose up --build
```

정상 실행 시 아래와 비슷한 로그가 출력됩니다.

```text
--- [1/2] 라이브러리 로드 테스트 ---
✅ SoccerNet 라이브러리가 성공적으로 로드되었습니다.

--- [2/2] 데이터 접근 테스트 ---
✅ API 연결 및 데이터 다운로드 테스트 성공!
이제 프로젝트를 시작할 준비가 되었습니다.
```

## 2. 컨테이너만 다시 실행

이미 빌드가 끝난 상태라면 다음 명령으로 검증 스크립트만 다시 실행할 수 있습니다.

```bash
docker compose up
```

컨테이너가 종료된 뒤 다시 깨끗하게 실행하고 싶다면 다음 순서로 실행합니다.

```bash
docker compose down
docker compose up
```

## 3. 일회성 명령 실행

컨테이너 안에서 Python 명령을 한 번만 실행하려면 다음 형식을 사용합니다.

```bash
docker compose run --rm soccernet-app python verify_setup.py
```

SoccerNet 라이브러리 import만 확인하려면 다음 명령을 사용할 수 있습니다.

```bash
docker compose run --rm soccernet-app python -c "import SoccerNet; print('SoccerNet OK')"
```

## 4. 데이터 저장 위치

다운로드된 데이터는 호스트의 `data` 폴더에 저장됩니다.

```text
data/
└── spotting/
    └── england_epl/
        └── ...
            └── Labels-v2.json
```

컨테이너 내부에서는 같은 데이터가 `/app/data` 경로로 보입니다.

```text
/app/data
```

## 5. 비밀번호 변경

SoccerNet 비밀번호를 바꾸려면 `docker-compose.yml`의 `SOCCERNET_PW` 값을 수정합니다.

```yaml
environment:
  - SOCCERNET_PW=여기에_받은_비밀번호
```

수정 후 다시 실행합니다.

```bash
docker compose up
```

## 6. 자주 쓰는 명령

```bash
# 설정 파일 확인
docker compose config

# 빌드 후 실행
docker compose up --build

# 기존 이미지로 실행
docker compose up

# 컨테이너 정리
docker compose down

# 일회성 검증 실행
docker compose run --rm soccernet-app python verify_setup.py

# 실행 중인 컨테이너 확인
docker ps

# 모든 컨테이너 확인
docker ps -a
```

## 7. 문제 해결

### Docker가 실행되지 않는 경우

Docker Desktop을 먼저 실행한 뒤 다시 명령을 실행하세요.

```bash
docker compose up
```

### `ModuleNotFoundError: No module named 'SoccerNet.Downloader'`

이미지가 오래됐거나 패키지 설치가 실패했을 수 있습니다. 다시 빌드하세요.

```bash
docker compose up --build
```

### `ERROR Unknown task: action-spotting`

현재 검증 스크립트는 `action-spotting` 대신 SoccerNet 라이브러리에서 지원하는 `spotting` 태스크를 사용합니다. 오래된 스크립트를 실행 중이라면 최신 `verify_setup.py`를 확인하세요.

### 라벨 다운로드가 실패하는 경우

아래 항목을 확인하세요.

* 네트워크 연결 상태
* `SOCCERNET_PW` 값
* SoccerNet 서버 접근 가능 여부
* `data` 폴더 쓰기 권한

## 8. 다음 단계

기초 검증이 끝나면 `verify_setup.py`를 별도 실험 스크립트로 확장하거나, `src` 폴더를 만들어 하이라이트 추출 로직을 분리해 개발하면 됩니다.
