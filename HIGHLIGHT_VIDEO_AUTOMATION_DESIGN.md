# Highlight Video Automation Design

이 문서는 현재 `highlight_candidate` 파이프라인을 기반으로, 나중에 실제 하이라이트 영상을 자동 생성하기 위한 설계를 정리합니다.

현재 목표는 바로 영상을 자르는 것이 아니라, 먼저 **왜 이 구간을 잘라야 하는지 설명 가능한 clip plan**을 만들고, 그 plan을 기준으로 clip 추출과 하이라이트 영상 병합까지 자동화하는 것입니다.

## 1. 목표

입력:

```text
SoccerNet 원본 경기 영상
ranked highlight candidate CSV
score_change / text_cue / replay event evidence
```

출력:

```text
후보별 mp4 clip
경기별 highlight compilation mp4
clip_plan.csv
clip extraction log
review contact sheet
```

최종 흐름:

```text
ranked highlight candidates
-> clip plan 생성
-> 원본 영상에서 후보별 clip 추출
-> clip 중복/겹침 정리
-> 경기별 highlight mp4 병합
-> 리뷰 리포트 생성
```

## 2. 현재 파이프라인과 연결

현재 완료된 Phase 1 흐름:

```text
frames
-> detect
-> replay
-> crops
-> ocr
-> reparse
-> smooth
-> text
-> fuse
-> rank
-> eval
-> review
```

영상 자동 생성은 이 뒤에 붙습니다.

```text
clip_plan
-> clips
-> compose
```

최종 batch stage:

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
clip_plan
clips
compose
```

## 3. 출력 구조

경기별 산출물 위치:

```text
outputs/batch_5/matches/{match_id}/
  clips/
    clip_plan.csv
    rank_001__candidate_0004__13m21s.mp4
    rank_004__candidate_0047__80m31s.mp4
  highlights/
    highlight_top5.mp4
  reports/
    clip_extraction_report.csv
  reviews/
    highlight_top5/
      contact_sheet.jpg
```

## 4. Clip Plan 설계

새 스크립트:

```text
src/video/build_clip_plan.py
```

역할:

```text
ranked highlight candidate CSV를 읽고 실제로 잘라낼 영상 구간을 계산합니다.
```

입력:

```text
outputs/batch_5/matches/{match_id}/events/highlight_candidates_ranked.csv
outputs/batch_5/matches/{match_id}/events/replay_events.csv
data/spotting/{league}/{season}/{match}/1_720p.mkv
data/spotting/{league}/{season}/{match}/2_720p.mkv
```

출력:

```text
outputs/batch_5/matches/{match_id}/clips/clip_plan.csv
```

컬럼:

```text
match_id
candidate_id
rank
rank_score
half
candidate_video_sec
candidate_match_clock
clip_start_sec
clip_end_sec
clip_duration_sec
source_video
output_clip
evidence_types
score_signal
cue_texts
clip_reason
```

## 5. Clip 구간 계산 규칙

### 5.1 기본 규칙

```text
score_change 포함 후보:
  start = candidate_time - 25초
  end   = candidate_time + 35초

text_cue only 후보:
  start = candidate_time - 20초
  end   = candidate_time + 30초

replay_segment 포함 후보:
  replay segment start/end를 우선 사용
  start = replay_start - 5초
  end   = replay_end + 5초
```

### 5.2 제한

```text
최소 길이: 20초
권장 길이: 45-60초
최대 길이: 75초
half 영상 범위를 넘어가면 0초 또는 영상 끝으로 clamp
```

### 5.3 중복 후보 병합

같은 half에서 clip 구간이 크게 겹치면 병합합니다.

```text
겹침 기준:
  overlap >= 50%
  또는 start/end 차이가 30초 이내

병합 방식:
  더 높은 rank 후보를 대표 candidate로 사용
  clip_start = min(start)
  clip_end = max(end)
  evidence는 합침
```

## 6. Clip 추출 설계

새 스크립트:

```text
src/video/extract_highlight_clips.py
```

역할:

```text
clip_plan.csv를 읽고 ffmpeg로 원본 영상에서 mp4 clip을 추출합니다.
```

기본 ffmpeg:

```bash
ffmpeg -y \
  -ss {clip_start_sec} \
  -to {clip_end_sec} \
  -i {source_video} \
  -c:v libx264 \
  -preset veryfast \
  -crf 23 \
  -c:a aac \
  -b:a 128k \
  {output_clip}
```

초기에는 안정성을 위해 재인코딩합니다.
속도 최적화가 필요하면 나중에 `-c copy`를 옵션으로 추가합니다.

## 7. Highlight 영상 병합 설계

새 스크립트:

```text
src/video/compose_highlight_video.py
```

역할:

```text
Top-K clip을 하나의 경기별 하이라이트 영상으로 병합합니다.
```

입력:

```text
clip_plan.csv
후보별 mp4 clip
```

출력:

```text
outputs/batch_5/matches/{match_id}/highlights/highlight_top5.mp4
```

초기 MVP:

```text
rank 순서대로 concat
별도 인트로/자막 없음
```

후속 개선:

```text
clip 시작 전에 1초 title card 삽입
rank/evidence/score/cue_text 표시
간단한 fade transition 추가
경기명/스코어/날짜 표시
```

## 8. Review 리포트

영상 생성 후 검증용 리포트를 남깁니다.

```text
outputs/batch_5/matches/{match_id}/reports/clip_extraction_report.csv
```

컬럼:

```text
candidate_id
rank
source_video
clip_start_sec
clip_end_sec
output_clip
exists
file_size_mb
duration_sec
status
error
```

검증 기준:

```text
clip 파일 존재
파일 크기 0보다 큼
duration이 plan과 크게 다르지 않음
Top-K 후보 수만큼 clip 생성
highlight_top5.mp4 생성
```

## 9. Batch Runner 통합

`src/pipeline/run_batch.py`에 stage를 추가합니다.

```text
clip_plan
clips
compose
```

예상 명령:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --stages clip_plan,clips,compose `
  --skip-existing `
  --continue-on-error
```

전체 실행:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --skip-existing `
  --continue-on-error
```

## 10. 구현 우선순위

### Step 1. Clip Plan

```text
src/video/build_clip_plan.py 구현
Chelsea-Burnley 1경기에서 clip_plan.csv 생성
Top-5 후보의 start/end가 자연스러운지 확인
```

### Step 2. Clip Extraction

```text
src/video/extract_highlight_clips.py 구현
Top-5 후보별 mp4 clip 생성
clip_extraction_report.csv 생성
```

### Step 3. Composition

```text
src/video/compose_highlight_video.py 구현
highlight_top5.mp4 생성
```

### Step 4. Batch Integration

```text
run_batch.py에 clip_plan/clips/compose stage 추가
5경기 batch에 적용
```

### Step 5. 품질 개선

```text
clip 길이 튜닝
겹치는 clip 병합
Top-K 대신 rank_score threshold 실험
title card / evidence overlay 추가
```

## 11. 초기 성공 기준

1경기 MVP:

```text
Chelsea-Burnley Top-5 후보에서 mp4 clip 5개 생성
highlight_top5.mp4 생성
실제 2골이 영상 안에 포함됨
```

5경기 기준:

```text
각 경기 highlight_top5.mp4 생성
batch_summary.csv에 highlight_video 경로 추가
Goal이 있는 경기에서 Top-5 clip Recall@30s 확인
```

## 12. 주의할 점

```text
candidate timestamp는 half 내부 시간입니다.
원본 영상도 1_720p.mkv, 2_720p.mkv로 half가 분리되어 있으므로 ffmpeg에는 half 내부 시간을 넣습니다.
리뷰 표시에는 90분 기준 match clock을 같이 보여줍니다.
```

예:

```text
half 1, candidate_video_sec=801  -> match clock 13:21
half 2, candidate_video_sec=2133 -> match clock 80:33
```

