# YOLO Dataset Test Guide

이 문서는 `scoreboard`, `overlay`, `replay_logo` 자동 탐지 모델을 만들기 위한 학습 데이터셋 준비와 테스트 절차를 정리합니다.

목표는 30경기 batch 분석을 위한 로컬 detector를 만드는 것입니다.

## 1. 선택 모델

```text
기본 detector: YOLO11s
빠른 테스트 detector: YOLO11n
OCR 기본 모델: PaddleOCR PP-OCRv5 server
OCR 빠른 테스트: PaddleOCR PP-OCRv5 mobile
```

탐지 클래스:

```text
0 scoreboard
1 overlay
2 replay_logo
```

## 2. 현재 타겟 경기

우선 아래 경기로 데이터셋 준비와 테스트를 시작합니다.

```text
data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley
```

프레임 위치:

```text
outputs/frames/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley/
```

## 3. 프레임 생성 확인

PowerShell에서 프로젝트 루트로 이동합니다.

```powershell
cd C:\chun\workspace\my-sports-ai
```

전반/후반 프레임 수를 확인합니다.

```powershell
(Get-ChildItem "outputs\frames\england_epl\2014-2015\2015-02-21 - 18-00 Chelsea 1 - 1 Burnley\half_1" -Filter *.jpg).Count
(Get-ChildItem "outputs\frames\england_epl\2014-2015\2015-02-21 - 18-00 Chelsea 1 - 1 Burnley\half_2" -Filter *.jpg).Count
```

정상 기준:

```text
half_1: 약 2700장
half_2: 약 2700장
```

프레임이 부족하면 전체 샘플링을 다시 실행합니다.

```powershell
docker compose run --rm soccernet-app python -m src.phase1a `
  --match-dir "data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" `
  --data-root data/spotting `
  --fps 1
```

## 4. 데이터셋 폴더 구조

YOLO 데이터셋은 아래 구조를 사용합니다.

```text
datasets/
  yolo_broadcast_graphics/
    images/
      train/
      val/
    labels/
      train/
      val/
    data.yaml
```

모델 산출물은 아래에 저장합니다.

```text
models/
  yolo/
    broadcast_graphics_yolo11n.pt
    broadcast_graphics_yolo11s.pt
```

## 5. data.yaml 작성

`datasets/yolo_broadcast_graphics/data.yaml` 내용:

```yaml
path: /app/datasets/yolo_broadcast_graphics
train: images/train
val: images/val
names:
  0: scoreboard
  1: overlay
  2: replay_logo
```

## 6. 라벨링용 대표 프레임 고르기

최소 목표:

```text
5경기 x 20프레임 = 100장
```

현재는 타겟 경기 1개로 먼저 시작합니다.

타겟 경기에서 추천하는 프레임 종류:

```text
일반 라이브 플레이 화면
스코어보드가 잘 보이는 화면
하단 선수명/이벤트 자막이 뜬 화면
프리미어리그 중앙 전환 마크가 뜬 화면
리플레이 장면
전반/후반 각각 여러 시점
```

처음 1경기에서 최소 30장을 뽑습니다.

```text
scoreboard가 보이는 프레임 20장 이상
overlay가 보이는 프레임 5장 이상
replay_logo가 보이는 프레임 5장 이상
```

구현된 준비 스크립트로 일정 간격 프레임을 복사합니다.

```powershell
docker compose run --rm soccernet-app python -m src.vision.prepare_yolo_dataset `
  --frames-root "outputs/frames/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" `
  --dataset-root datasets/yolo_broadcast_graphics `
  --limit 100 `
  --stride 60 `
  --val-every 5
```

출력 확인:

```powershell
(Get-ChildItem "datasets\yolo_broadcast_graphics\images\train" -Filter *.jpg).Count
(Get-ChildItem "datasets\yolo_broadcast_graphics\images\val" -Filter *.jpg).Count
```

## 7. 자동 라벨 초안 생성

수동 라벨링 전에 휴리스틱 기반 자동 라벨 초안을 먼저 생성합니다.

현재 자동화 범위:

```text
scoreboard: 자동 생성 가능
overlay: 아직 수동/후순위
replay_logo: 오탐 위험 때문에 기본 자동 생성 제외
```

실행 명령:

```powershell
docker compose run --rm soccernet-app python -m src.vision.auto_label_graphics `
  --dataset-root datasets/yolo_broadcast_graphics `
  --overwrite
```

현재 타겟 경기 기준 생성 결과 예시:

```text
total images: 91
scoreboard labels: 88
empty labels: 3
replay_logo labels: 0
```

리뷰 이미지는 아래 경로에 생성됩니다.

```text
outputs/auto_labels/yolo_broadcast_graphics/train
outputs/auto_labels/yolo_broadcast_graphics/val
```

리뷰할 때 확인할 것:

```text
스코어보드가 없는 초반 프레임은 빈 라벨인가?
스코어보드 박스가 팀명, 점수, 시간을 모두 포함하는가?
선수나 광고판이 scoreboard로 잘못 잡히지 않았는가?
```

리플레이 로고 후보까지 강제로 생성하려면 아래 옵션을 붙일 수 있습니다.
다만 현재는 일반 플레이의 선수를 로고로 오탐할 수 있어 추천하지 않습니다.

```powershell
docker compose run --rm soccernet-app python -m src.vision.auto_label_graphics `
  --dataset-root datasets/yolo_broadcast_graphics `
  --overwrite `
  --include-replay-logo-candidates
```

## 8. 라벨링 규칙

### scoreboard

포함:

```text
경기 시간
팀명
점수
스코어보드 박스 전체
```

bbox는 텍스트만 타이트하게 잡지 말고 스코어보드 그래픽 전체를 약간 여유 있게 잡습니다.

### overlay

포함:

```text
선수명 자막
카드/교체 자막
VAR 문구
이벤트 설명 자막
하단 또는 중앙 하단 그래픽
```

화면에 overlay가 없으면 라벨링하지 않습니다.

### replay_logo

포함:

```text
프리미어리그 중앙 전환 마크
리플레이 시작/종료 시 중앙에 뜨는 그래픽
```

마크 주변을 약간 여유 있게 잡습니다. 리플레이 장면 자체가 아니라 전환 로고만 잡습니다.

## 9. 라벨링 도구

추천 도구:

```text
CVAT
Label Studio
Roboflow
```

편한 도구로 bbox를 그리고 YOLO format으로 export하면 됩니다.

YOLO label 형식:

```text
class_id x_center y_center width height
```

좌표는 이미지 크기 기준 0-1로 정규화됩니다.

예시:

```text
0 0.1720 0.0550 0.3100 0.0800
2 0.5000 0.4200 0.2800 0.3000
```

## 10. train/val 분리

처음에는 간단히 80:20으로 나눕니다.

```text
train: 80장
val: 20장
```

파일명은 이미지와 라벨이 같아야 합니다.

```text
images/train/frame_0001.jpg
labels/train/frame_0001.txt
```

## 11. Docker GPU 환경 준비

이미 추가된 파일:

```text
Dockerfile.gpu
compose.gpu.yml
requirements-gpu.txt
```

필요 패키지:

```text
ultralytics
torch
opencv-python
paddleocr
paddlepaddle-gpu
```

GPU 이미지 빌드:

```powershell
docker compose -f compose.gpu.yml build
```

GPU 확인:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu nvidia-smi
```

Python GPU 확인:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -c "import torch; print(torch.cuda.is_available()); import paddle; print(paddle.__version__)"
```

## 12. YOLO11n Smoke Training

데이터셋이 준비되면 먼저 가벼운 YOLO11n으로 학습 파이프라인만 검증합니다.

실행 명령:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.vision.train_detector `
  --model yolo11n.pt `
  --data datasets/yolo_broadcast_graphics/data.yaml `
  --epochs 10 `
  --imgsz 1280 `
  --batch 8 `
  --project models/yolo/runs `
  --name broadcast_graphics_yolo11n_smoke `
  --device 0
```

성공 기준:

```text
학습이 에러 없이 완료됨
val 이미지에서 scoreboard가 일부라도 잡힘
runs 결과 폴더 생성
```

현재 타겟 경기 smoke training 완료 결과:

```text
epochs: 10
model: YOLO11n
class: scoreboard
validation images: 18
validation instances: 16
precision: 0.986
recall: 1.000
mAP50: 0.995
mAP50-95: 0.900
saved model: models/yolo/broadcast_graphics_yolo11n.pt
```

주의:

```text
현재 val set도 자동 라벨 초안 기반이라 지표가 실제 일반화 성능보다 높게 나올 수 있습니다.
따라서 다음 단계는 훈련 지표가 아니라 실제 타겟 경기 프레임 inference 결과를 확인하는 것입니다.
```

## 13. YOLO11n Smoke Inference

학습된 YOLO11n 모델로 타겟 경기 일부 프레임에 먼저 inference를 실행합니다.

실행 명령:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.vision.detect_graphics `
  --model models/yolo/broadcast_graphics_yolo11n.pt `
  --frames-root "outputs/frames/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" `
  --output outputs/detections/chelsea_burnley_2015_yolo11n_smoke.csv `
  --limit 300
```

CSV 앞부분 확인:

```powershell
Get-Content outputs\detections\chelsea_burnley_2015_yolo11n_smoke.csv -First 20
```

확인할 것:

```text
scoreboard confidence가 대부분 0.7 이상인가?
스코어보드가 없는 초반/전환 프레임에서 검출이 과하게 나오지 않는가?
좌표 x1,y1,x2,y2가 실제 좌상단 스코어보드 근처인가?
```

현재 타겟 경기 smoke inference 결과:

```text
input limit: 300 frames
detections: 287
class: scoreboard
confidence min: 0.319
confidence avg: 0.649
confidence max: 0.872
confidence >= 0.50: 266
confidence >= 0.70: 87
```

해석:

```text
좌표는 x 약 110-368, y 약 38-104로 좌상단 스코어보드 위치에 안정적으로 모임.
confidence 0.70 이상은 안전한 pseudo-label 후보로 사용.
confidence 0.50-0.70은 추가 확장 후보지만 먼저 리뷰 이미지 확인 후 사용.
```

## 14. Pseudo-Label 확장 전략

30경기 전체를 수동 라벨링하지 않기 위해 아래 흐름으로 자동 확장합니다.

```text
1. 자동 라벨 초안으로 YOLO11n smoke model 학습
2. YOLO11n으로 더 많은 프레임 inference
3. confidence 0.7 이상 scoreboard는 pseudo-label 후보로 채택
4. confidence 낮은 프레임과 미검출 프레임만 리뷰 대상으로 분리
5. 수정된 pseudo-label로 YOLO11s main training
6. YOLO11s로 30경기 batch inference
```

현재 구현된 pseudo-label 생성 명령:

```powershell
docker compose run --rm soccernet-app python -m src.vision.pseudo_label_graphics `
  --detections outputs/detections/chelsea_burnley_2015_yolo11n_smoke.csv `
  --output-root datasets/yolo_broadcast_graphics_pseudo `
  --min-conf 0.70 `
  --copy-images
```

생성 결과:

```text
accepted images: 87
labels: datasets/yolo_broadcast_graphics_pseudo/labels/train
images: datasets/yolo_broadcast_graphics_pseudo/images/train
review images: outputs/pseudo_labels/review
```

다음 리뷰 경로:

```text
outputs/pseudo_labels/review
```

0.50 이상 후보까지 확장하려면 아래 명령을 사용합니다.

```powershell
docker compose run --rm soccernet-app python -m src.vision.pseudo_label_graphics `
  --detections outputs/detections/chelsea_burnley_2015_yolo11n_smoke.csv `
  --output-root datasets/yolo_broadcast_graphics_pseudo_050 `
  --min-conf 0.50 `
  --copy-images
```

현재 생성 결과:

```text
accepted images: 266
dataset: datasets/yolo_broadcast_graphics_pseudo_050
```

원본 자동 라벨셋과 pseudo-label셋을 병합합니다.

```powershell
docker compose run --rm soccernet-app python -m src.vision.merge_yolo_datasets `
  --sources datasets/yolo_broadcast_graphics datasets/yolo_broadcast_graphics_pseudo_050 `
  --output-root datasets/yolo_broadcast_graphics_merged `
  --pseudo-to-train-only `
  --overwrite
```

현재 병합 결과:

```text
original train images: 73
original val images: 18
pseudo train images: 266
merged total images: 357
merged data yaml: datasets/yolo_broadcast_graphics_merged/data.yaml
```

클래스별 자동화 전략:

```text
scoreboard:
  자동 라벨 + pseudo-label로 확장

overlay:
  SoccerNet 이벤트 시간 주변 프레임에서 후보를 뽑은 뒤 별도 라벨링

replay_logo:
  전체 프레임 탐지보다 replay transition 후보 프레임을 먼저 추출
  중앙 PL 로고 후보만 별도 라벨링/학습
```

## 15. YOLO11s Main Training

smoke test가 통과하면 YOLO11s로 학습합니다.

실행 명령:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.vision.train_detector `
  --model yolo11s.pt `
  --data datasets/yolo_broadcast_graphics_merged/data.yaml `
  --epochs 50 `
  --imgsz 1280 `
  --batch 8 `
  --project models/yolo/runs `
  --name broadcast_graphics_yolo11s `
  --device 0 `
  --output-model models/yolo/broadcast_graphics_yolo11s.pt
```

`--output-model`을 지정했기 때문에 학습 완료 후 best model이 아래 경로로 복사됩니다.

```text
models/yolo/broadcast_graphics_yolo11s.pt
```

현재 YOLO11s main training 완료 결과:

```text
epochs: 50
model: YOLO11s
train images: 339
validation images: 18
validation instances: 16
precision: 0.997
recall: 1.000
mAP50: 0.995
mAP50-95: 0.972
saved model: models/yolo/broadcast_graphics_yolo11s.pt
```

## 16. 타겟 경기 추론

학습된 모델로 타겟 경기 프레임에 대해 inference를 실행합니다.

실행 명령:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.vision.detect_graphics `
  --model models/yolo/broadcast_graphics_yolo11s.pt `
  --frames-root "outputs/frames/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" `
  --output outputs/detections/chelsea_burnley_2015.csv
```

빠른 추론 테스트만 하려면 `--limit`을 붙입니다.

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.vision.detect_graphics `
  --model models/yolo/broadcast_graphics_yolo11s.pt `
  --frames-root "outputs/frames/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley" `
  --output outputs/detections/chelsea_burnley_2015_smoke.csv `
  --limit 100
```

출력 CSV 컬럼:

```text
match_id
half
timestamp_sec
class_name
confidence
x1
y1
x2
y2
image_path
```

현재 전체 추론 완료 결과:

```text
model: models/yolo/broadcast_graphics_yolo11s.pt
input frames: 5400
detections: 5401
unique detected frames: 5377
class: scoreboard
confidence avg: 0.931
confidence >= 0.70: 5348
confidence >= 0.85: 5295
output: outputs/detections/chelsea_burnley_2015_yolo11s_full.csv
```

해석:

```text
scoreboard detector는 실사용 가능한 수준으로 안정화됨.
이 경기에서는 scoreboard가 대부분 프레임에서 유지되므로 replay detection은 scoreboard disappearance 방식으로 처리하지 않음.
다음 단계는 Premier League center transition logo 후보 프레임 추출.
```

## 17. 결과 검증

확인할 것:

```text
scoreboard가 대부분 프레임에서 잡히는가?
overlay 없는 프레임에서 overlay 오탐이 심하지 않은가?
replay_logo가 전환 마크 장면에서 잡히는가?
일반 리플레이 장면과 전환 로고를 혼동하지 않는가?
```

CSV 확인:

```powershell
Get-Content outputs\detections\chelsea_burnley_2015.csv -First 20
```

클래스별 개수 확인은 추후 helper 스크립트로 자동화합니다.

## 18. 성공 기준

1경기 테스트 성공 기준:

```text
scoreboard detection이 대부분 정상
replay_logo 후보가 실제 전환 마크 근처에서 검출
overlay는 오탐이 있어도 CSV로 분석 가능
outputs/detections CSV 생성
```

30경기 확장 전 기준:

```text
최소 5경기에서 validation
scoreboard class 안정화
replay_logo class 검출 가능
overlay class는 후순위로 개선
```

## 19. 다음 구현 대상

```text
src/vision/prepare_yolo_dataset.py
src/vision/auto_label_graphics.py
Dockerfile.gpu
compose.gpu.yml
src/vision/train_detector.py
src/vision/detect_graphics.py
src/vision/pseudo_label_graphics.py
src/vision/extract_replay_logo_candidates.py
```
