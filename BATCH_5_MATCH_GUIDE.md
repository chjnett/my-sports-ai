# Batch 5 Match Test Guide

이 문서는 EPL 2014-2015 5경기 검증을 한 번에 실행하기 위한 가이드입니다.

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
  --skip-existing
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

## 5. 이어서 실행하기

중간에 멈추면 같은 명령을 다시 실행합니다.

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --skip-existing
```

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
  Select-Object match_id,ocr_rows,score_events,text_events,candidates,ranked_candidates,top5_recall_at_30s,review_sheet |
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

다음 판단:

```text
Top-5 Recall@30s가 낮은 경기 -> 실패 사례 수집
후보가 너무 많은 경기 -> ranking/stopword 조정
OCR이 약한 경기 -> crop/OCR 설정 조정
```
