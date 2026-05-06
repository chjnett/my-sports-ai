# Remote Access Guide

이 문서는 Mac에서 Windows RTX 3090 랩탑에 원격 접속하여 Docker 기반 모델 학습/추론을 실행하기 위한 설정 가이드입니다.

목표 구조:

```text
Mac = 조종기
Windows RTX 3090 랩탑 = 실제 작업 머신
Docker GPU 컨테이너 = 모델 실행 환경
```

즉, Mac에서 명령을 입력하더라도 실제 YOLO/PaddleOCR 학습과 추론은 Windows 랩탑의 RTX 3090에서 실행됩니다.

---

## 1. 현재 진행 상태

완료:

```text
Windows 랩탑에서 Chrome Remote Desktop 세팅 진행 완료
```

다음에 이어서 할 작업:

```text
Mac에서 Chrome Remote Desktop 접속 확인
Windows/Mac 양쪽에 Tailscale 설치
Windows OpenSSH Server 설정
Mac VS Code Remote SSH 연결
Docker GPU 명령 원격 실행 확인
```

---

## 2. 권장 운영 방식

원격 접속은 두 가지를 같이 쓰는 것을 권장합니다.

```text
Chrome Remote Desktop:
  - 화면 원격 조작
  - Docker Desktop 상태 확인
  - Windows GUI 조작
  - 초기 세팅/문제 확인용

Tailscale + SSH + VS Code Remote SSH:
  - 평소 개발
  - Mac VS Code에서 Windows 프로젝트 열기
  - Docker 학습/추론 명령 실행
  - 장기적으로 가장 편한 개발 환경
```

처음에는 Chrome Remote Desktop만 성공해도 충분합니다. 이후 Tailscale과 SSH를 붙이면 Mac에서 훨씬 가볍게 개발할 수 있습니다.

---

## 3. Windows 랩탑 기본 준비

Windows 랩탑은 모델을 실제로 돌리는 작업 머신입니다. 학습 중 절전으로 꺼지면 작업이 중단되므로 전원 설정을 먼저 정리합니다.

### 3.1 전원 연결

학습/추론 중에는 반드시 전원 어댑터를 연결합니다.

```text
RTX 3090 GPU 학습 중에는 배터리 사용 금지
```

### 3.2 절전 모드 끄기

Windows에서:

```text
설정
-> 시스템
-> 전원 및 배터리
-> 화면 및 절전
```

권장 설정:

```text
전원 연결 시 화면 끄기: 원하는 값
전원 연결 시 절전 모드: 안 함
```

가능하면 덮개 설정도 변경합니다.

```text
제어판
-> 전원 옵션
-> 덮개를 닫으면 수행되는 작업 선택
-> 전원 사용: 아무 작업 안 함
```

---

## 4. Chrome Remote Desktop 세팅

### 4.1 Windows 랩탑에서 설정

현재 완료한 단계입니다.

Windows 랩탑에서:

1. Chrome 실행
2. 아래 주소 접속

```text
remotedesktop.google.com/access
```

3. `원격 액세스 설정` 클릭
4. Chrome Remote Desktop Host 설치
5. 컴퓨터 이름 설정

예시:

```text
my-sports-ai-laptop
```

6. PIN 설정
7. 원격 접속 가능 상태 확인

### 4.2 Mac에서 접속 확인

Mac에서:

1. Chrome 실행
2. Windows에서 사용한 Google 계정과 같은 계정으로 로그인
3. 아래 주소 접속

```text
remotedesktop.google.com/access
```

4. Windows 랩탑 선택
5. PIN 입력
6. Windows 화면 접속 확인

성공 기준:

```text
Mac 화면에서 Windows 바탕화면이 보임
PowerShell 실행 가능
Docker Desktop 상태 확인 가능
```

---

## 5. Docker GPU 동작 확인

Chrome Remote Desktop으로 Windows에 접속한 뒤 PowerShell에서 실행합니다.

```powershell
cd C:\chun\workspace\my-sports-ai
```

GPU 컨테이너 확인:

```powershell
docker compose -f compose.gpu.yml run --rm vision-gpu nvidia-smi
```

성공 기준:

```text
NVIDIA GeForce RTX 3090 표시
CUDA 정보 표시
에러 없이 컨테이너 종료
```

---

## 6. Tailscale 설치

Tailscale은 Mac과 Windows 랩탑을 같은 사설망처럼 묶어주는 용도입니다. 외부 네트워크에서도 안정적으로 접속하기 위해 사용합니다.

### 6.1 Windows 랩탑

Windows에서:

1. Tailscale 설치
2. Google/Microsoft/Apple 계정으로 로그인
3. 작업표시줄 Tailscale 아이콘 확인
4. 가능하면 `Run Unattended` 켜기
5. Windows 랩탑의 Tailscale IP 확인

Tailscale IP 예시:

```text
100.x.x.x
```

### 6.2 Mac

Mac에서:

1. Tailscale 설치
2. Windows와 같은 계정으로 로그인
3. Tailscale 앱에서 Windows 랩탑이 보이는지 확인

성공 기준:

```text
Mac과 Windows가 같은 Tailscale 네트워크에 표시됨
Windows 랩탑의 100.x.x.x IP 확인 가능
```

---

## 7. Windows OpenSSH Server 설정

Mac VS Code Remote SSH로 Windows 프로젝트를 열려면 Windows에 OpenSSH Server를 켭니다.

Windows PowerShell을 관리자 권한으로 열고 실행합니다.

설치 여부 확인:

```powershell
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'
```

설치가 안 되어 있으면:

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
```

서비스 시작:

```powershell
Start-Service sshd
```

자동 시작 설정:

```powershell
Set-Service -Name sshd -StartupType Automatic
```

방화벽 허용:

```powershell
New-NetFirewallRule -Name sshd -DisplayName "OpenSSH Server" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

Windows 사용자명 확인:

```powershell
whoami
```

예시:

```text
DESKTOP-XXXX\uns
```

SSH 접속 사용자명은 보통 아래처럼 사용합니다.

```text
uns
```

---

## 8. Mac에서 SSH 접속 테스트

Mac 터미널에서 실행합니다.

```bash
ssh uns@100.x.x.x
```

여기서 `100.x.x.x`는 Windows 랩탑의 Tailscale IP입니다.

접속 후 Windows PowerShell 환경에서 아래 명령을 확인합니다.

```powershell
cd C:\chun\workspace\my-sports-ai
docker compose ps
```

성공 기준:

```text
Mac 터미널에서 Windows 랩탑에 SSH 접속됨
C:\chun\workspace\my-sports-ai 폴더로 이동 가능
docker compose 명령 실행 가능
```

---

## 9. VS Code Remote SSH 연결

Mac에서:

1. VS Code 설치
2. Extensions에서 `Remote - SSH` 설치
3. `Cmd + Shift + P`
4. `Remote-SSH: Connect to Host...` 선택
5. 아래 형식으로 입력

```text
uns@100.x.x.x
```

6. 접속 후 폴더 열기

```text
C:\chun\workspace\my-sports-ai
```

성공 기준:

```text
Mac VS Code에서 Windows 프로젝트 파일이 보임
VS Code 터미널이 Windows 랩탑에서 실행됨
Docker 명령을 실행하면 Windows RTX 3090 랩탑에서 처리됨
```

---

## 10. 원격 학습 실행

Mac에서 Chrome Remote Desktop 또는 VS Code Remote SSH로 Windows 랩탑에 접속한 상태에서 실행합니다.

```powershell
cd C:\chun\workspace\my-sports-ai
```

YOLO11s 학습 예시:

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

주의:

```text
명령을 Mac에서 입력해도 SSH/원격 화면의 대상이 Windows 랩탑이면 실제 실행은 Windows 랩탑에서 수행됨
GPU 연산도 Windows 랩탑의 RTX 3090에서 수행됨
```

---

## 11. 긴 학습 작업 운영 팁

장시간 학습할 때:

```text
Windows 랩탑 전원 연결
절전 모드 끄기
Docker Desktop 켜기
Tailscale 켜기
학습 중 Windows 재부팅 금지
```

SSH 터미널을 닫으면 실행 중인 명령이 끊길 수 있습니다. 긴 학습은 처음에는 Chrome Remote Desktop에서 PowerShell을 열고 실행하는 방식이 가장 단순합니다.

추후 필요하면 아래 방식으로 장기 실행을 개선합니다.

```text
PowerShell background job
Windows Terminal 유지
작업 로그 파일 저장
학습/추론 실행 스크립트화
```

---

## 12. 다음 체크리스트

- [x] Windows 랩탑 Chrome Remote Desktop 세팅
- [ ] Mac에서 Chrome Remote Desktop 접속 확인
- [ ] Windows 랩탑 Tailscale 설치
- [ ] Mac Tailscale 설치
- [ ] Windows OpenSSH Server 활성화
- [ ] Mac에서 SSH 접속 테스트
- [ ] Mac VS Code Remote SSH 연결
- [ ] 원격 터미널에서 `docker compose ps` 확인
- [ ] 원격 터미널에서 `nvidia-smi` 컨테이너 확인
- [ ] 원격 환경에서 모델 학습/추론 실행
