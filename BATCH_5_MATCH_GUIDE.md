# Batch 5 Match Test Guide

이 문서는 EPL 2014-2015 5경기 검증을 한 번에 실행하기 위한 가이드입니다.

현재 상태:

```text
2026-05-11 기준, 누락됐던 3경기의 Labels-v2.json과 720p 전후반 영상 다운로드가 완료되었습니다.
5경기 batch는 정상 완료되었습니다.
candidate 대표 timestamp는 score_change를 우선하고, 평가는 candidate interval 기준으로 수행합니다.
review contact sheet는 -10/0/+10/+30초 프레임을 표시합니다.
```

## 1. 대상 경기

설정 파일:

```text
configs/batch_5_matches.yml
```

현재 5경기:

```text
chelsea_burnley_2015_02_21
crystal_palace_arsenal_2015_02_21
swansea_manchester_united_2015_02_21
southampton_liverpool_2015_02_22
burnley_arsenal_2015_04_11
```

## 2. 다운로드 완료 확인

프로젝트 루트:

```powershell
cd C:\chun\workspace\my-sports-ai
```

각 경기 폴더에 `Labels-v2.json`과 전후반 영상이 있는지 확인합니다.

```powershell
Get-ChildItem "data\spotting\england_epl\2014-2015" -Directory |
  Where-Object {
    $_.Name -in @(
      "2015-02-21 - 18-00 Chelsea 1 - 1 Burnley",
      "2015-02-21 - 18-00 Crystal Palace 1 - 2 Arsenal",
      "2015-02-21 - 18-00 Swansea 2 - 1 Manchester United",
      "2015-02-22 - 19-15 Southampton 0 - 2 Liverpool",
      "2015-04-11 - 19-30 Burnley 0 - 1 Arsenal"
    )
  } |
  ForEach-Object {
    [PSCustomObject]@{
      Match = $_.Name
      Labels = Test-Path (Join-Path $_.FullName "Labels-v2.json")
      Half1_720p = Test-Path (Join-Path $_.FullName "1_720p.mkv")
      Half2_720p = Test-Path (Join-Path $_.FullName "2_720p.mkv")
      Half1_224p = Test-Path (Join-Path $_.FullName "1_224p.mkv")
      Half2_224p = Test-Path (Join-Path $_.FullName "2_224p.mkv")
    }
  } |
  Format-Table -AutoSize
```

`720p`가 없더라도 `224p`가 있으면 frame sampling은 fallback으로 진행됩니다.

## 3. Dry Run

명령이 올바르게 만들어지는지 먼저 확인합니다.

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --dry-run `
  --limit-matches 1
```

특정 stage만 확인:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --stages frames,detect `
  --dry-run `
  --limit-matches 1
```

## 4. 전체 실행

다운로드가 끝난 뒤 전체 pipeline을 실행합니다.

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --skip-existing `
  --continue-on-error
```

장시간 실행할 때는 백그라운드 컨테이너로 실행합니다.

```powershell
docker compose -f compose.gpu.yml run -d --name my_sports_ai_batch5 vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --skip-existing `
  --continue-on-error
```

이미 같은 이름의 컨테이너가 있으면 먼저 상태를 확인합니다.

```powershell
docker ps -a --filter "name=my_sports_ai_batch5" --format "table {{.Names}}\t{{.Status}}\t{{.ID}}"
```

`Up` 상태면 새로 실행하지 말고 로그만 봅니다.

```powershell
docker logs -f --tail 100 my_sports_ai_batch5
```

`Exited` 상태이고 새로 실행해야 한다면 제거 후 다시 실행합니다.

```powershell
docker rm my_sports_ai_batch5
```

실행 stage:

```text
frames
detect
replay
crops
ocr
reparse
smooth
text
fuse
rank
eval
review
```

평가 방식:

```text
point timestamp만 보지 않고 candidate start/end interval을 함께 봅니다.
score_change가 포함된 candidate는 대표 timestamp를 score_change 시각으로 둡니다.
```

## 5. 이어서 실행하기

중간에 멈추면 같은 명령을 다시 실행합니다.

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --skip-existing `
  --continue-on-error
```

`phase1a_events.csv`가 없다는 에러가 나면 같은 명령을 다시 실행하면 됩니다.
현재 batch runner는 batch용 label CSV가 없을 때 `frames` stage를 다시 실행해서 라벨 CSV를 생성합니다.
이미 프레임이 있으면 기존 프레임은 대부분 skip되므로 오래 걸리지 않습니다.
아직 다운로드가 덜 된 경기는 `skipped_missing_labels` 또는 `skipped_missing_videos` 상태로 summary에 남기고 다음 경기로 넘어갑니다.

특정 stage부터 다시 돌리고 싶으면:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --stages ocr,reparse,smooth,text,fuse,rank,eval,review `
  --skip-existing
```

## 6. 결과 확인

전체 summary:

```powershell
Get-Content outputs\batch_5\batch_summary.csv
```

보기 좋게:

```powershell
Import-Csv outputs\batch_5\batch_summary.csv |
  Select-Object match_id,status,ocr_rows,score_events,text_events,candidates,ranked_candidates,top5_recall_at_30s,review_sheet |
  Format-Table -AutoSize
```

각 경기 contact sheet:

```text
outputs/batch_5/matches/{match_id}/reviews/highlight_top5/contact_sheet.jpg
```

예:

```powershell
Invoke-Item outputs\batch_5\matches\chelsea_burnley_2015_02_21\reviews\highlight_top5\contact_sheet.jpg
```

5경기 contact sheet를 한 번에 찾기:

```powershell
Get-ChildItem outputs\batch_5\matches -Recurse -Filter contact_sheet.jpg |
  Select-Object FullName
```

완료 후 우선 확인할 표:

```powershell
Import-Csv outputs\batch_5\batch_summary.csv |
  Select-Object match_id,status,candidates,ranked_candidates,top5_recall_at_30s |
  Format-Table -AutoSize
```

## 7. 예상 소요 시간

RTX 3090 기준 대략:

```text
frame sampling: 경기당 5-15분
YOLO detection: 경기당 2-5분
scoreboard crop: 경기당 1분 내외
PaddleOCR: 경기당 2-8분
나머지 CSV 처리: 경기당 1분 내외
```

5경기 전체:

```text
빠르면 45-60분
넉넉히 1-2시간
```

다운로드가 224p만 되어 있으면 더 빠르고, 720p 기준이면 frame sampling과 detection 시간이 늘어납니다.

## 8. 성공 기준

1차 목표:

```text
5경기 모두 batch_summary.csv에 row 생성
각 경기 review contact_sheet.jpg 생성
Goal이 있는 경기에서 Top-5 Recall@30s 확인
```

현재 5경기 결과:

```text
Chelsea-Burnley              Top-5 Recall@30s = 1.000
Crystal Palace-Arsenal       Top-5 Recall@30s = 1.000
Swansea-Man United           Top-5 Recall@30s = 1.000
Southampton-Liverpool        Top-5 Recall@30s = 1.000
Burnley-Arsenal              Top-5 Recall@30s = 1.000

Total: 11/11 = 1.000
```

다음 판단:

```text
Top-5 Recall@30s가 낮은 경기 -> 현재 5경기 기준 없음
후보가 너무 많은 경기 -> ranking/stopword 조정
OCR이 약한 경기 -> crop/OCR 설정 조정
```

참고:

```text
Swansea-Man United 첫 골 누락 원인:
이전 OCR window에 남아 있던 잘못된 1-0 후보가 현재 프레임에서 다시 관측되지 않았는데도 score_change로 확정됨.

수정:
score smoothing 단계에서 현재 row의 observed_score가 candidate와 같을 때만 새 score_change를 확정하도록 변경.
```

상세 트러블슈팅 기록은 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)를 참고합니다.

## 9. 내가 해야 할 체크리스트

- [ ] batch 실행 중에는 노트북 전원 연결 유지
- [ ] 절전 모드 진입 방지
- [ ] `docker logs -f --tail 100 my_sports_ai_batch5`로 현재 stage 확인
- [ ] 완료 후 `batch_summary.csv` 확인
- [ ] `completed`가 아닌 경기 이름 기록
- [x] Top-5 Recall@30s가 낮은 경기 이름 기록
- [ ] 각 경기 contact sheet를 영상과 비교해서 실제 골 장면 포함 여부 확인
- [x] 실패 경기의 `highlight_topk_eval_details.csv`를 확인해 가장 가까운 후보 시간 차이 기록
