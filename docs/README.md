# 연구 문서 인덱스

이 폴더는 논문과 연구 개발에 필요한 문서를 보관합니다.

루트 문서 [YOLO_DATASET_TEST_GUIDE.md](../YOLO_DATASET_TEST_GUIDE.md)는 YOLO 데이터셋 준비, 라벨링, 학습 테스트 절차를 담당합니다.
루트 문서 [OCR_SCOREBOARD_TEST_GUIDE.md](../OCR_SCOREBOARD_TEST_GUIDE.md)는 scoreboard OCR, smoothing, Goal 평가 절차를 담당합니다.

## 문서 목록

| 문서 | 내용 |
|---|---|
| [RESEARCH_ARCHITECTURE.md](RESEARCH_ARCHITECTURE.md) | 전체 연구 질문, 아키텍처, 실험 설계 |
| [PHASE_1_VISION_OCR_PIPELINE.md](PHASE_1_VISION_OCR_PIPELINE.md) | 1순위 실행 대상인 Vision/OCR 파이프라인 상세 |
| [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) | GPU, 모델, 라이브러리, 인프라 기술 사양 |

## 현재 연구 방향

```text
축구 중계 영상의 그래픽 OCR 이벤트 그래프를 이용한 설명 가능한 하이라이트 생성
```

핵심 키워드:

```text
SoccerNet
Broadcast Video
Scoreboard OCR
Broadcast Graphic Event Graph
Explainable Highlight Generation
Action Spotting
Replay Grounding
```

## 현재 완성도

2026-05-07 기준:

```text
전체 프로젝트: 약 43%
Phase 1 Vision/OCR: 약 75%
Vision detector: 약 75%
OCR MVP: 약 65%
```

현재 완료된 핵심:

```text
1fps frame sampling
scoreboard YOLO11s detector
replay_logo strict candidate extraction
scoreboard + replay_logo YOLO11s fine-tuning
replay_transition_logo / replay_segment event CSV
scoreboard crop generation
PaddleOCR smoke test
OCR smoothing smoke test
score_change evaluation smoke test
PaddleOCR full OCR
strict score parser
OCR CSV re-parsing
text cue extraction
highlight candidate fusion
```

다음 핵심:

```text
highlight candidate false-positive reduction
text cue normalization
candidate ranking
5-match evaluation
```

## 문서 작성 원칙

* `README.md`는 프로젝트 소개와 빠른 시작을 담당합니다.
* `SETUP_GUIDE.md`는 최초 환경 세팅을 담당합니다.
* `RUN_GUIDE.md`는 GUI 실행과 다운로드 사용법을 담당합니다.
* `PROJECT_MASTER_PLAN.md`는 전체 개발 우선순위와 로드맵을 담당합니다.
* `docs/RESEARCH_ARCHITECTURE.md`는 연구 설계를 담당합니다.
* `docs/PHASE_1_VISION_OCR_PIPELINE.md`는 바로 구현할 OCR 파이프라인을 담당합니다.
* `docs/TECHNICAL_SPEC.md`는 최종 기술 스택과 GPU 환경을 담당합니다.
