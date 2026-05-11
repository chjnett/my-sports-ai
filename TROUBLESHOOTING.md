# Troubleshooting Log

이 문서는 SoccerNet 하이라이트 추출 파이프라인을 구현하면서 실제로 발생한 문제와 해결 방법을 기록합니다.

## 1. PowerShell profile 실행 정책 경고

### 증상

PowerShell 명령 실행 시 아래 경고가 반복 출력됩니다.

```text
File C:\Users\uns\Documents\WindowsPowerShell\profile.ps1 cannot be loaded because running scripts is disabled on this system.
PSSecurityException
```

### 원인

Windows PowerShell 실행 정책 때문에 사용자 profile script를 로드하지 못하는 문제입니다.

### 영향

일반적인 `docker`, `git`, `Get-Content`, `Import-Csv` 명령 실행에는 큰 영향이 없습니다.

### 대응

현재 프로젝트 작업에서는 무시해도 됩니다. 명령 결과가 정상 출력되고 exit code가 0이면 pipeline 문제로 보지 않습니다.

## 2. Docker container name conflict

### 증상

같은 이름으로 batch container를 다시 실행하면 아래 오류가 발생합니다.

```text
Conflict. The container name "/my_sports_ai_batch5" is already in use
```

### 원인

이전 batch container가 종료됐지만 Docker에 이름이 남아 있어서 같은 이름을 재사용하지 못합니다.

### 확인

```powershell
docker ps -a --filter "name=my_sports_ai_batch5"
```

### 대응

기존 컨테이너 로그가 더 필요 없으면 삭제 후 다시 실행합니다.

```powershell
docker rm my_sports_ai_batch5
```

또는 새 이름으로 실행합니다.

```powershell
docker compose -f compose.gpu.yml run -d --name my_sports_ai_batch5_retry vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --skip-existing `
  --continue-on-error
```

## 3. Labels-v2.json 누락으로 batch stage 중단

### 증상

프레임 추출 단계에서 아래 오류가 발생합니다.

```text
Labels-v2.json not found
```

### 원인

SoccerNet 경기 폴더에 라벨 파일이 내려받아지지 않은 상태에서 batch를 실행했습니다.

### 확인

```powershell
Test-Path "data\spotting\england_epl\2014-2015\<match_name>\Labels-v2.json"
```

### 대응

GUI에서 다운로드 종류를 `라벨 + 풀 경기 영상 720p`로 선택한 뒤 누락 경기를 다시 다운로드합니다.

필수 파일:

```text
Labels-v2.json
1_720p.mkv
2_720p.mkv
```

## 4. contact_sheet.jpg를 PowerShell에서 바로 실행한 문제

### 증상

이미지 경로를 그대로 입력하면 아래 오류가 발생합니다.

```text
contact_sheet.jpg : 용어가 cmdlet, 함수, 스크립트 파일 또는 실행할 수 있는 프로그램 이름으로 인식되지 않습니다.
```

### 원인

PowerShell은 파일 경로만 입력하면 이미지를 여는 명령으로 처리하지 않습니다.

### 대응

Windows 기본 앱으로 열 때는 `Invoke-Item`을 사용합니다.

```powershell
Invoke-Item "outputs\batch_5\matches\swansea_manchester_united_2015_02_21\reviews\highlight_top5\contact_sheet.jpg"
```

## 5. 후보 대표 timestamp가 골 장면 밖으로 밀린 문제

### 증상

리뷰 이미지나 평가에서 후보가 실제 골 장면을 포함하는데도 대표 시간이 골 시점과 멀게 보였습니다.

예시:

```text
Burnley-Arsenal: 사용자가 확인한 골 시점은 11:03 근처인데 대표 timestamp가 다른 프레임을 가리킴
Swansea-Man United: 후보 구간은 골을 포함하지만 대표 timestamp 기준 평가에서 불리하게 계산됨
```

### 원인

`score_change` 후보에 `text_cue` 또는 `replay_transition_logo`가 병합될 때 candidate의 대표 `timestamp_sec`가 후보 구간의 시작 시점으로 다시 덮였습니다.

### 수정

`src/events/fuse_highlight_candidates.py`에서 score signal이 있는 후보는 대표 timestamp를 score_change 시점으로 유지하도록 변경했습니다.

핵심 규칙:

```text
score_change가 있으면 timestamp_sec는 score_change 시점 유지
score_change가 없는 후보만 start_timestamp_sec를 대표 timestamp로 사용
```

### 검증

`render_ranked_candidates` 리뷰 시트에 `-10, 0, +10, +30초` 프레임을 함께 표시하도록 바꿔 실제 골 장면 포함 여부를 사람이 확인할 수 있게 했습니다.

## 6. 점수 변화 후보 interval 평가 누락

### 증상

후보가 `start_timestamp_sec`부터 `end_timestamp_sec` 사이에 실제 골을 포함하는데도 `timestamp_sec` 한 점만 기준으로 평가되어 miss로 계산될 수 있었습니다.

### 원인

기존 Top-K 평가는 후보 대표 timestamp와 goal label timestamp의 절대 차이만 계산했습니다.

### 수정

`src/evaluation/evaluate_topk_candidates.py`에 `--matching interval` 옵션을 추가했습니다.

판정 규칙:

```text
goal timestamp가 candidate start/end interval 안에 있으면 delta = 0
interval 밖이면 start/end/timestamp 중 가장 가까운 거리 사용
```

`src/pipeline/run_batch.py`는 기본적으로 interval 평가를 사용합니다.

### 검증

5경기 batch 평가에서 interval 기반 `Top-5 Recall@30s`를 확인했습니다.

```text
Chelsea-Burnley              1.000
Crystal Palace-Arsenal       1.000
Swansea-Man United           1.000
Southampton-Liverpool        1.000
Burnley-Arsenal              1.000

Total: 11/11 = 1.000
```

## 7. Swansea-Man United 첫 골 누락

### 증상

Swansea-Man United 경기에서 사용자가 실제 영상을 확인한 전반 27:36 골이 Top-5 후보에 안정적으로 들어오지 않았습니다.

기존 결과:

```text
Swansea-Man United Top-5 Recall@30s = 0.667
5경기 전체 Top-5 Recall@30s = 10/11 = 0.909
```

### 원인

scoreboard OCR smoothing 단계에서 이전 OCR window에 남아 있던 잘못된 점수 후보가 현재 프레임에서 다시 관측되지 않았는데도 score_change로 확정됐습니다.

구체적으로는 unrelated overlay/replay OCR 노이즈가 `1-0`처럼 파싱되었고, 이 stale candidate가 먼저 안정 점수로 확정되었습니다. 이후 실제 `0-1` 변화는 backward transition처럼 보이면서 거부되었습니다.

### 수정

`src/ocr/smooth_scoreboard_ocr.py`에서 새 score_change 확정 조건을 강화했습니다.

변경 전 개념:

```text
최근 window 안에서 candidate vote가 충분하고 forward change이면 score_change 확정
```

변경 후 개념:

```text
최근 window 안에서 candidate vote가 충분하고
현재 row의 observed_score도 candidate와 같고
forward change일 때만 score_change 확정
```

즉, 과거 window에만 남은 stale score 후보는 현재 프레임에서 재관측되지 않으면 점수 변화로 확정하지 않습니다.

### 재실행

수정 후 아래 stage를 다시 실행했습니다.

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --stages smooth,fuse,rank,eval,review `
  --continue-on-error
```

### 검증

Swansea-Man United 첫 골이 Top-5 안에 들어왔습니다.

```text
goal: 전반 27:36
nearest rank: 2
candidate: candidate_0014
candidate timestamp: 1669.0초
candidate interval start: 1645.0초
hit_at_30s: 1
```

최종 5경기 결과:

```text
5경기 Top-5 Recall@30s = 11/11 = 1.000
Swansea-Man United Top-5 Recall@30s = 3/3 = 1.000
```

### 재발 방지 체크

- `score_change_events.csv`에 경기 초반 이상한 점수 변화가 생기면 OCR raw text를 먼저 확인합니다.
- `highlight_topk_eval_details.csv`에서 miss가 나면 `nearest_start_sec`, `nearest_end_sec`, `matching` 컬럼을 함께 봅니다.
- 후보가 실제 골을 포함하는데 miss라면 point 평가가 아니라 interval 평가인지 확인합니다.
- scoreboard OCR이 불안정한 경기는 `review/highlight_top5/contact_sheet.jpg`를 영상과 직접 비교합니다.
