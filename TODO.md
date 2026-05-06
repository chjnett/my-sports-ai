# TODO

이 문서는 `my-sports-ai` 프로젝트의 완료 작업과 다음 작업을 체크리스트로 관리하기 위한 문서입니다.

## 1. 완료한 작업

### 프로젝트 기본 세팅

- [x] Git 저장소 초기화
- [x] Docker 기반 실행 환경 구성
- [x] `Dockerfile` 작성
- [x] `docker-compose.yml` 작성
- [x] `.env` 기반 SoccerNet 비밀번호 로드 구성
- [x] `.gitignore`로 `data/`, `outputs/`, `.env`, 캐시 파일 제외
- [x] `.dockerignore`로 Docker build context 정리
- [x] `data/.gitkeep` 추가

### SoccerNet 다운로드/검증

- [x] `verify_setup.py` 구성
- [x] SoccerNet 라이브러리 import 검증
- [x] `Labels-v2.json` 테스트 다운로드 검증
- [x] Streamlit GUI 기반 경기 검색/다운로드 흐름 구성
- [x] 라벨, 224p, 720p 다운로드 모드 구성
- [x] `data/spotting/` 저장 구조 확인

### 문서 정리

- [x] `README.md` 정리
- [x] `SETUP_GUIDE.md` 정리
- [x] `RUN_GUIDE.md` 정리
- [x] `PROJECT_MASTER_PLAN.md` 작성
- [x] `docs/README.md` 작성
- [x] `docs/RESEARCH_ARCHITECTURE.md` 정리
- [x] `docs/PHASE_1_VISION_OCR_PIPELINE.md` 작성
- [x] `docs/TECHNICAL_SPEC.md` 작성
- [x] 기존 `docs/spec.md`를 `docs/TECHNICAL_SPEC.md`로 대체

### Phase 1A: 라벨 파서 + 프레임 샘플러

- [x] `src/` 기본 패키지 구조 생성
- [x] `src/data/labels.py` 구현
- [x] SoccerNet `Labels-v2.json` 파싱
- [x] Goal, Yellow card, Red card, Substitution 이벤트 추출
- [x] 이벤트 CSV 저장 기능 구현
- [x] `src/video/frame_sampler.py` 구현
- [x] 경기 폴더에서 전반/후반 영상 자동 탐색
- [x] 1fps 프레임 샘플링 구현
- [x] 샘플링 summary CSV 저장 기능 구현
- [x] `src/phase1a.py` 통합 실행 엔트리 구현
- [x] Docker 컨테이너 안에서 라벨 파서 검증
- [x] Docker 컨테이너 안에서 프레임 샘플러 검증
- [x] Docker 컨테이너 안에서 Phase 1A 통합 실행 검증

검증 명령:

```bash
docker compose run --rm soccernet-app python -m src.phase1a \
  --match-dir "data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" \
  --data-root data/spotting \
  --fps 1 \
  --max-seconds 3
```

검증 결과:

```text
Events: outputs/reports/phase1a_events.csv (10 target events)
Frame summary: outputs/reports/phase1a_frame_sampling_summary.csv
```

## 2. 바로 다음 작업

### Phase 1B: 수동 Crop Config + Crop 적용기

- [ ] `configs/crop_config.json` 스키마 설계
- [ ] 기본 scoreboard crop 좌표 작성
- [ ] 기본 overlay crop 좌표 작성
- [ ] `src/ocr/crop_config.py` 구현
- [ ] 프레임 폴더에서 crop 이미지 생성
- [ ] `outputs/crops/{match_id}/half_{n}/` 저장 구조 생성
- [ ] crop summary CSV 저장
- [ ] Docker 컨테이너에서 crop 적용 검증
- [ ] `docs/PHASE_1_VISION_OCR_PIPELINE.md`에 crop 실행 명령 추가

예상 실행 명령:

```bash
docker compose run --rm soccernet-app python -m src.ocr.crop_config \
  --frames-root "outputs/frames/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" \
  --config configs/crop_config.json \
  --output-root outputs/crops
```

완료 기준:

```text
대표 경기 1개에서 scoreboard crop 이미지 생성
수동 확인 시 경기 시간/점수 영역이 crop 안에 포함됨
crop summary CSV 생성
```

## 3. Phase 1C 이후 작업

### Phase 1C: OCR 실행

- [ ] OCR 엔진 선택
- [ ] PaddleOCR CPU 버전 MVP 적용
- [ ] GPU 버전은 별도 Dockerfile로 분리 검토
- [ ] `src/ocr/run_ocr.py` 구현
- [ ] crop 이미지에서 OCR 실행
- [ ] OCR raw 결과 CSV 저장
- [ ] 컬럼 정의
  - [ ] `match_id`
  - [ ] `half`
  - [ ] `timestamp_sec`
  - [ ] `crop_type`
  - [ ] `raw_text`
  - [ ] `confidence`
  - [ ] `parsed_clock`
  - [ ] `parsed_home_score`
  - [ ] `parsed_away_score`
  - [ ] `event_keyword`
- [ ] Docker 컨테이너에서 OCR 실행 검증

완료 기준:

```text
5경기 기준 OCR CSV 생성
score/clock 후보 컬럼 분리
OCR confidence 저장
```

### Phase 1D: OCR Cleaning

- [ ] `src/ocr/clean_ocr.py` 구현
- [ ] 숫자/문자 혼동 보정 규칙 작성
- [ ] 점수 문자열 파싱
- [ ] 경기 시간 문자열 파싱
- [ ] 이벤트 키워드 파싱
- [ ] 불가능한 점수 감소 제거

대표 보정 규칙:

```text
I-0 -> 1-0
O-0 -> 0-0
l -> 1
S8:12 -> 58:12
0O -> 00
```

### Phase 1E: Temporal Smoothing

- [ ] `src/ocr/smoothing.py` 구현
- [ ] 5초 window 기반 점수 다수결
- [ ] 경기 시간 단조 증가 보정
- [ ] 단발 score change 제거
- [ ] smoothed OCR CSV 저장

완료 기준:

```text
raw OCR 대비 false score_change 감소
smoothed score timeline 생성
```

### Phase 1F: Goal Label Evaluation

- [ ] `src/evaluation/metrics.py` 구현
- [ ] OCR 기반 score_change timestamp 추출
- [ ] SoccerNet Goal label timestamp 추출
- [ ] Recall@5s 계산
- [ ] Recall@10s 계산
- [ ] Recall@30s 계산
- [ ] false positive per match 계산
- [ ] raw OCR vs smoothed OCR 비교표 생성

출력:

```text
outputs/reports/phase1_goal_recall_table.csv
outputs/reports/phase1_ocr_ablation.md
```

## 4. Phase 1.5 확장 작업

### 자동 영역 탐지

- [ ] YOLO11n 적용 여부 확정
- [ ] scoreboard/overlay detection 라벨링 방식 설계
- [ ] 학습용 crop annotation 포맷 정의
- [ ] `models/yolo_scoreboard.pt` 관리 방식 결정
- [ ] 자동 crop 결과와 수동 crop 결과 비교

### GPU OCR/디코딩

- [ ] `Dockerfile.gpu` 작성
- [ ] `compose.gpu.yml` 작성
- [ ] CUDA/PaddleOCR 호환 버전 확정
- [ ] GPU PaddleOCR batch inference 테스트
- [ ] NVIDIA DALI 적용 필요성 평가

## 5. Phase 2 이후 연구 작업

### Event Graph

- [ ] `src/graph/event_graph.py` 구현
- [ ] `src/graph/graph_schema.py` 구현
- [ ] `score_state` 노드 생성
- [ ] `score_change` 노드 생성
- [ ] `replay_overlay` 노드 생성
- [ ] `label_nearby` 노드 생성
- [ ] `highlight_candidate` 노드 생성
- [ ] 이벤트 그래프 JSON 저장

### Highlight Generation

- [ ] `src/highlight/candidate_generator.py` 구현
- [ ] Goal 후보 구간 생성
- [ ] Card 후보 구간 생성
- [ ] Substitution 후보 구간 생성
- [ ] 가까운 후보 병합
- [ ] rule-based scoring 구현
- [ ] `src/video/clipper.py` 구현
- [ ] ffmpeg 기반 클립 생성
- [ ] 후보별 explanation JSON 생성

### 논문 실험 패키지

- [ ] 10경기 이상 실험
- [ ] 30경기 이상 확장 실험
- [ ] baseline 비교
- [ ] ablation 실험
- [ ] 실패 사례 분석
- [ ] 결과표 생성
- [ ] case study 작성
- [ ] 한국어 논문 초안 작성

## 6. 운영 규칙

- [ ] 모든 실행은 Docker 기반으로 수행
- [ ] 로컬 Python 환경에 의존하지 않기
- [ ] 대용량 데이터는 Git에 올리지 않기
- [ ] `data/`, `outputs/`, `paper/`는 Git 추적 제외 유지
- [ ] 구현 후 실행 명령은 관련 문서에 반영
- [ ] 각 Phase는 Docker 명령으로 재현 가능해야 함

## 7. 참고 문서

| 문서 | 역할 |
|---|---|
| [README.md](README.md) | 프로젝트 소개와 빠른 시작 |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 최초 세팅 |
| [RUN_GUIDE.md](RUN_GUIDE.md) | GUI 실행과 다운로드 사용법 |
| [PROJECT_MASTER_PLAN.md](PROJECT_MASTER_PLAN.md) | 개발 우선순위와 로드맵 |
| [docs/RESEARCH_ARCHITECTURE.md](docs/RESEARCH_ARCHITECTURE.md) | 연구 아키텍처 |
| [docs/PHASE_1_VISION_OCR_PIPELINE.md](docs/PHASE_1_VISION_OCR_PIPELINE.md) | Phase 1 실행 명세 |
| [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md) | 기술 사양 |
