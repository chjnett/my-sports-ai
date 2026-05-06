# Specification: 축구 중계 영상 그래픽 OCR 기반 설명 가능한 하이라이트 생성 시스템

본 문서는 RTX 3090(24GB) 환경을 기반으로 축구 중계 영상에서 그래픽 OCR 및 멀티모달 데이터를 추출하고, 이를 이벤트 그래프로 구조화하여 설명 가능한 하이라이트를 생성하는 시스템 사양을 정의합니다.

---

## 1. 하드웨어 사양 (Hardware Target)

* **GPU:** NVIDIA GeForce RTX 3090 (VRAM 24GB)
* **Optimization:** FP16 Mixed Precision, TensorRT 가속, DALI GPU 디코딩
* **목표 성능:** 90분 풀 경기 기준 분석 시간 10분 이내 (1fps 처리 기준)

---

## 2. 개발 로드맵 및 단계별 모델 선정

### Phase 1: Vision & OCR Pipeline (데이터 정형화)
중계 화면 내의 구조적 정보를 추출하는 단계입니다.

| 구분 | 선정 모델 / 라이브러리 | 상세 사양 및 선정 이유 |
| :--- | :--- | :--- |
| **Video Decoding** | **NVIDIA DALI** | CPU 병목 제거를 위한 GPU 기반 비디오 디코딩 |
| **Object Detection** | **YOLO11n** | 스코어보드, 자막(Overlay) 영역의 실시간 탐지 및 추적 |
| **Text Recognition** | **PaddleOCR v4** | 3090 배치 처리에 최적화된 고속 OCR. 한글/숫자 인식 우수 |
| **Smoothing** | **HMM / Heuristic** | "점수 역행 불가" 등 도메인 규칙 기반 OCR 오인식 보정 |

### Phase 2: Multi-modal Feature Extraction (단서 추출)
시각 정보 외에 하이라이트 판단을 돕는 보조 지표를 생성합니다.

| 구분 | 선정 모델 / 라이브러리 | 상세 사양 및 선정 이유 |
| :--- | :--- | :--- |
| **Audio Event** | **PANNs (CNN14)** | 함성, 휘슬 등 주요 사운드 이벤트를 벡터화 |
| **Action Spotting** | **VideoMAE v2** | SoccerNet 벤치마크 최적화된 영상 특징 추출 모델 |
| **Scene Detection** | **PySceneDetect** | 장면 전환(Cut) 및 리플레이 그래픽 시작/종료 탐지 |

### Phase 3: Event Graph & Reasoning (하이라이트 로직)
추출된 정보를 연결하여 하이라이트 점수를 계산하고 근거를 생성합니다.

| 구분 | 선정 모델 / 라이브러리 | 상세 사양 및 선정 이유 |
| :--- | :--- | :--- |
| **Graph Framework** | **PyTorch Geometric** | 노드(이벤트)와 엣지(시간적 관계) 기반 그래프 구축 |
| **Scoring Model** | **Graph Attention Net** | 이벤트 간 인과관계 가중치 학습을 통한 점수 산출 |
| **XAI Generator** | **Llama 3.1-8B (Local)** | 생성된 그래프 데이터를 기반으로 자연어 설명 리포트 작성 |

---

## 3. 핵심 기술 사양 (Technical Core)

### 3.1 하이라이트 스코어링 알고리즘
하이라이트 후보 구간 $t$에 대한 최종 점수 $S(t)$는 다음과 같은 하이브리드 가중치 합산으로 결정됩니다.

$$S_{highlight}(t) = w_1 \cdot O_{score}(t) + w_2 \cdot G_{replay}(t) + w_3 \cdot A_{peak}(t) + \dots$$

* $O_{score}(t)$: OCR 기반 점수 변화 여부
* $G_{replay}(t)$: 리플레이 그래픽 노출 시간 및 빈도
* $A_{peak}(t)$: 오디오 피크(함성) 정규화 수치

### 3.2 Event Graph Schema
* **Nodes:** `score_state`, `replay_overlay`, `audio_peak`, `action_spotting_label`
* **Edges:** `near_to(t)`, `leads_to(event)`, `contradicts(logic)`

---

## 4. 데이터 아키텍처 및 디렉토리 구조

```text
/project_root
├── data/
│   └── SoccerNet/              # 원천 데이터 (Video, Labels)
├── src/
│   ├── modules/
│   │   ├── vision_ocr.py       # YOLO + PaddleOCR 파이프라인
│   │   ├── audio_engine.py     # PANNs 기반 오디오 분석
│   │   └── graph_builder.py    # PyG 기반 이벤트 그래프 구축
│   └── inference/
│       ├── scorer.py           # 하이라이트 점수 산출 로직
│       └── explainer.py        # Llama 3.1 기반 설명 생성
├── outputs/
│   ├── event_graphs/           # 경기별 분석 결과 (JSON)
│   ├── highlight_clips/        # 최종 하이라이트 (MP4)
│   └── reports/                # 설명 가능한 리포트 (Markdown)
└── spec.md                     # 시스템 기술 사양서
