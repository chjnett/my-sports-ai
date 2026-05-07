# Scoreboard OCR Test Guide

이 문서는 현재 타겟 경기에서 `scoreboard` crop을 PaddleOCR로 읽고, 점수 OCR을 시간축으로 안정화한 뒤, SoccerNet Goal label과 비교하는 절차를 정리합니다.

## 1. 현재 전제

프로젝트 루트:

```powershell
cd C:\chun\workspace\my-sports-ai
```

타겟 경기:

```text
data/spotting/england_epl/2014-2015/2015-02-21 - 18-00 Chelsea 1 - 1 Burnley
```

이미 완료된 산출물:

```text
outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv
outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv
models/yolo/broadcast_graphics_yolo11s_scoreboard_replay.pt
```

## 2. Scoreboard Crop 생성

이미 생성했다면 건너뛰어도 됩니다.

```powershell
docker compose run --rm soccernet-app python -m src.vision.crop_detections `
  --detections outputs/detections/chelsea_burnley_2015_scoreboard_replay_full.csv `
  --output-root outputs/crops/chelsea_burnley_2015_detector `
  --summary outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv `
  --class-name scoreboard `
  --min-conf 0.70 `
  --padding 8 `
  --best-per-frame
```

정상 기준:

```text
rows/crops written: 약 5200개 이상
```

## 3. OCR Smoke Test

처음에는 20장만 읽어서 OCR 출력 구조와 파싱 상태를 확인합니다.

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.ocr.run_scoreboard_ocr `
  --crops outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv `
  --output outputs/ocr_csv/chelsea_burnley_2015_scoreboard_smoke.csv `
  --limit 20 `
  --device gpu
```

결과 확인:

```powershell
Get-Content outputs\ocr_csv\chelsea_burnley_2015_scoreboard_smoke.csv -First 25
```

좋은 예:

```text
CHE 0-0 BUR 00:13
CHE 0-0 BUR 00:14
CHE 0-0 BUR 00:15
```

주의할 점:

```text
전환 그래픽, 해시태그, 흐림 프레임에서는 CHE BUR #CHEBUR 같은 노이즈가 섞일 수 있습니다.
이 노이즈는 다음 smoothing 단계에서 안정 점수로 보정합니다.
```

## 4. 전체 OCR 실행

Smoke 결과가 좋으면 전체 scoreboard crop에 OCR을 실행합니다.

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.ocr.run_scoreboard_ocr `
  --crops outputs/reports/chelsea_burnley_2015_scoreboard_crops.csv `
  --output outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full.csv `
  --device gpu
```

예상 소요:

```text
RTX 3090 기준 대략 수 분에서 10분대
최초 실행 시 PaddleOCR 모델 다운로드 때문에 더 오래 걸릴 수 있음
```

## 5. OCR Smoothing

원시 OCR 결과에서 같은 점수가 최근 몇 초 안에 반복될 때만 안정 점수로 인정합니다.

이미 OCR을 끝낸 뒤 파서만 개선한 경우에는 OCR을 다시 돌리지 말고 `raw_text`를 재파싱합니다.

```powershell
docker compose run --rm soccernet-app python -m src.ocr.reparse_scoreboard_ocr `
  --input outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full.csv `
  --output outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full_reparsed.csv
```

재파싱 규칙:

```text
score는 1-0, 1 - 1처럼 하이픈(-)이 있는 값만 인정
80:30 같은 clock 값은 score로 인정하지 않음
기본 score 범위는 0-20
```

```powershell
docker compose run --rm soccernet-app python -m src.ocr.smooth_scoreboard_ocr `
  --ocr outputs/ocr_csv/chelsea_burnley_2015_scoreboard_full_reparsed.csv `
  --output outputs/ocr_csv/chelsea_burnley_2015_scoreboard_smoothed_reparsed.csv `
  --events-output outputs/events/chelsea_burnley_2015_score_change_events_reparsed.csv `
  --window-sec 8 `
  --min-votes 3
```

출력:

```text
outputs/ocr_csv/chelsea_burnley_2015_scoreboard_smoothed_reparsed.csv
outputs/events/chelsea_burnley_2015_score_change_events_reparsed.csv
```

확인 명령:

```powershell
Get-Content outputs\events\chelsea_burnley_2015_score_change_events.csv
```

정상 기대:

```text
Chelsea 1 - 1 Burnley 경기이므로 score_change 이벤트가 2개 근처로 나오는지 확인합니다.
득점 직후 스코어보드 갱신 지연이 있으므로 SoccerNet Goal label과 몇 초 차이가 날 수 있습니다.
```

## 6. Goal Label 평가

Score change 이벤트가 SoccerNet Goal label 근처에 잡히는지 Recall@5/10/30s로 확인합니다.

```powershell
docker compose run --rm soccernet-app python -m src.evaluation.evaluate_score_changes `
  --labels outputs/reports/phase1a_events.csv `
  --score-events outputs/events/chelsea_burnley_2015_score_change_events_reparsed.csv `
  --output outputs/reports/chelsea_burnley_2015_score_change_eval_reparsed.csv `
  --tolerances 5,10,30
```

출력 예:

```text
goals: 2
score-change events: 2
Recall@5s: ...
Recall@10s: ...
Recall@30s: ...
```

## 7. 다음 판단 기준

좋은 결과:

```text
score_change 이벤트 수가 실제 Goal 수와 비슷함
Recall@30s가 높음
raw OCR 노이즈가 smoothed OCR에서 안정적으로 보정됨
```

나쁜 결과:

```text
score_change가 너무 많이 나옴 -> --min-votes를 4 또는 5로 증가
득점 이벤트를 놓침 -> --window-sec를 10 또는 12로 증가
OCR 자체가 점수를 못 읽음 -> crop padding 또는 OCR 전처리 개선
```

현재 Chelsea 1 - 1 Burnley 기준 재파싱 후 확인된 점:

```text
첫 골: Goal label 13:10, score_change 13:21, delta 11초
두 번째 골: 후반 80:21 근처 scoreboard OCR이 1-1을 안정적으로 읽지 못함
후반 80:31 근처 raw_text에 VOKES가 보임
따라서 두 번째 골은 scoreboard 단독보다 overlay/scorer OCR 후보와 결합해야 함
```
