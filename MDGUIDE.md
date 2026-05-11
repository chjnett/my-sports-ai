# MD Guide: 프로젝트 상황 파악 순서

이 문서는 영상을 생성하기 전에 현재 프로젝트가 어디까지 진행됐는지 빠르게 이해하기 위한 문서 읽기 가이드입니다.

## 1. 지금 프로젝트 한 줄 요약

SoccerNet 축구 중계 영상에서 scoreboard, replay logo, OCR text cue를 추출하고, 이를 시간축으로 결합해 설명 가능한 하이라이트 후보를 만드는 프로젝트입니다.

현재는 5경기 batch 기준으로 Goal 하이라이트 후보 검출이 안정화된 상태입니다.

```text
5경기 Top-5 Recall@30s = 11/11 = 1.000
다음 큰 작업 = 하이라이트 mp4 자동 생성
```

## 2. 문서를 읽는 추천 순서

처음 전체 상황을 볼 때는 아래 순서로 읽으면 됩니다.

| 순서 | 문서 | 읽는 이유 |
|---:|---|---|
| 1 | [README.md](README.md) | 프로젝트 목적과 빠른 시작 확인 |
| 2 | [PROJECT_MASTER_PLAN.md](PROJECT_MASTER_PLAN.md) | 전체 로드맵, 현재 완성도, 다음 우선순위 확인 |
| 3 | [TODO.md](TODO.md) | 완료된 작업과 바로 해야 할 작업 확인 |
| 4 | [BATCH_5_MATCH_GUIDE.md](BATCH_5_MATCH_GUIDE.md) | 5경기 batch 실험 결과와 검증 방법 확인 |
| 5 | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 실제로 발생했던 문제와 해결 기록 확인 |
| 6 | [HIGHLIGHT_VIDEO_AUTOMATION_DESIGN.md](HIGHLIGHT_VIDEO_AUTOMATION_DESIGN.md) | 다음 단계인 영상 자동 생성 설계 확인 |

세팅이나 원격 실행이 필요할 때만 아래 문서를 추가로 봅니다.

| 문서 | 용도 |
|---|---|
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | 최초 환경 세팅 |
| [RUN_GUIDE.md](RUN_GUIDE.md) | GUI 실행, 다운로드, 기본 실행 방법 |
| [REMOTE_ACCESS_GUIDE.md](REMOTE_ACCESS_GUIDE.md) | Mac에서 Windows RTX 3090 랩탑을 원격 작업 머신으로 쓰는 방법 |
| [YOLO_DATASET_TEST_GUIDE.md](YOLO_DATASET_TEST_GUIDE.md) | YOLO detector 데이터셋/학습 테스트 |
| [OCR_SCOREBOARD_TEST_GUIDE.md](OCR_SCOREBOARD_TEST_GUIDE.md) | scoreboard OCR, smoothing, Goal 평가 |

연구/논문 방향을 볼 때는 `docs/` 문서를 읽습니다.

| 문서 | 용도 |
|---|---|
| [docs/README.md](docs/README.md) | 연구 문서 인덱스 |
| [docs/RESEARCH_ARCHITECTURE.md](docs/RESEARCH_ARCHITECTURE.md) | 연구 질문, 전체 아키텍처 |
| [docs/PHASE_1_VISION_OCR_PIPELINE.md](docs/PHASE_1_VISION_OCR_PIPELINE.md) | Vision/OCR 파이프라인 상세 명세 |
| [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md) | GPU, 모델, Docker 기술 스택 |

## 3. 현재 구현된 핵심 파이프라인

현재 batch pipeline은 아래 흐름으로 동작합니다.

```text
SoccerNet match files
-> frame sampling
-> YOLO scoreboard/replay_logo detection
-> replay event extraction
-> scoreboard crop
-> PaddleOCR
-> strict score reparse
-> OCR smoothing
-> score_change event
-> text cue event
-> highlight candidate fusion
-> candidate ranking
-> Top-K evaluation
-> review contact sheet
```

주요 엔트리:

```text
src/pipeline/run_batch.py
```

5경기 설정:

```text
configs/batch_5_matches.yml
```

## 4. 현재 검증된 5경기

```text
chelsea_burnley_2015_02_21
crystal_palace_arsenal_2015_02_21
swansea_manchester_united_2015_02_21
southampton_liverpool_2015_02_22
burnley_arsenal_2015_04_11
```

현재 결과:

```text
Chelsea-Burnley              Top-5 Recall@30s = 1.000
Crystal Palace-Arsenal       Top-5 Recall@30s = 1.000
Swansea-Man United           Top-5 Recall@30s = 1.000
Southampton-Liverpool        Top-5 Recall@30s = 1.000
Burnley-Arsenal              Top-5 Recall@30s = 1.000

Total: 11/11 = 1.000
```

## 5. 최근 해결한 중요한 문제

최근에 해결한 핵심 문제는 Swansea-Man United 첫 골 누락입니다.

원인:

```text
이전 OCR window에 남아 있던 잘못된 score 후보가
현재 프레임에서 다시 관측되지 않았는데도 score_change로 확정됨
```

수정:

```text
현재 row의 observed_score가 candidate와 같을 때만
새 score_change를 확정하도록 smoothing 조건 강화
```

관련 파일:

```text
src/ocr/smooth_scoreboard_ocr.py
src/events/fuse_highlight_candidates.py
src/evaluation/evaluate_topk_candidates.py
src/pipeline/run_batch.py
```

상세 기록:

```text
TROUBLESHOOTING.md
```

## 6. 현재 결과물을 확인하는 방법

5경기 요약:

```powershell
Import-Csv outputs\batch_5\batch_summary.csv |
  Select-Object match_id,status,top5_recall_at_30s,review_sheet |
  Format-Table -AutoSize
```

특정 경기 Top-K 평가:

```powershell
Import-Csv outputs\batch_5\matches\swansea_manchester_united_2015_02_21\reports\highlight_topk_eval.csv |
  Format-Table -AutoSize
```

특정 경기 상세 매칭:

```powershell
Import-Csv outputs\batch_5\matches\swansea_manchester_united_2015_02_21\reports\highlight_topk_eval_details.csv |
  Where-Object {$_.top_k -eq "5"} |
  Format-Table -AutoSize
```

review contact sheet 열기:

```powershell
Invoke-Item "outputs\batch_5\matches\swansea_manchester_united_2015_02_21\reviews\highlight_top5\contact_sheet.jpg"
```

## 7. 다음 단계: 하이라이트 영상 자동 생성

현재 영상 자동 생성 MVP는 구현되어 있습니다. 핵심 원칙은 아래와 같습니다.

```text
Top-K 후보 선정: rank 기준
최종 highlight_top5.mp4 재생 순서: 경기 타임라인 순서
```

즉, rank가 높아도 경기 시간 순서를 바꾸지 않습니다.
rank는 어떤 장면을 포함할지 고르는 기준이고, 최종 영상은 `half -> clip_start_sec` 순서로 병합됩니다.

현재 후보 소스:

```text
score_change
text_cue
replay_transition_logo
replay_segment
Red card / Yellow card / Substitution SoccerNet label
```

리플레이 후보는 리플레이가 끝난 뒤가 아니라, 리플레이 로고/구간이 나오기 직전 실제 플레이 장면을 우선 보여주도록 clip window를 잡습니다.

예상 구현 순서:

```text
1. src/video/build_clip_plan.py 구현 완료
2. src/video/extract_highlight_clips.py 구현 완료
3. src/video/compose_highlight_video.py 구현 완료
4. run_batch.py에 clip_plan, clips, compose stage 연결 완료
5. Swansea 1경기 생성 테스트
6. 5경기 전체 highlight_top5.mp4 생성
7. 사용자가 mp4를 직접 열어 품질 확인
```

기준 설계 문서:

```text
HIGHLIGHT_VIDEO_AUTOMATION_DESIGN.md
```

영상 생성 stage만 실행:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu python3 -m src.pipeline.run_batch `
  --config configs/batch_5_matches.yml `
  --stages clip_plan,clips,compose `
  --skip-existing `
  --continue-on-error
```

## 8. Git에 올리지 않는 것

아래 파일/폴더는 대용량이거나 재생성 가능한 산출물이므로 Git에 올리지 않습니다.

```text
data/
outputs/
datasets/
models/
runs/
*.pt
*.mkv
*.mp4
*.avi
*.mov
*.log
```

코드, config, 문서만 Git에 남기는 것이 기본 원칙입니다.
