import os
import json
from pathlib import Path
from datetime import datetime
from SoccerNet.Downloader import SoccerNetDownloader, getListGames

from dotenv import load_dotenv # requirements.txt에 추가됨

# .env 파일의 내용을 환경 변수로 로드합니다.
load_dotenv()

# 이제 os.getenv를 통해 안전하게 가져옵니다.
pw = os.getenv("SOCCERNET_PW")

def log(msg, level="INFO"):
    symbol = {"INFO": "💡", "SUCCESS": "✅", "WARN": "⚠️", "ERROR": "❌"}
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {symbol.get(level, '·')} {msg}")

def find_full_path_auto(partial_path):
    """경기 이름만 있어도 전체 경로(리그/시즌/경기)를 찾아냅니다."""
    for spl in ["train", "valid", "test", "challenge"]:
        # 모든 경기의 전체 경로 리스트를 가져옴
        all_games = getListGames(split=spl, task="spotting")
        for full_path in all_games:
            # 사용자가 입력한 문자열이 전체 경로의 끝부분과 일치하는지 확인
            if full_path.endswith(partial_path):
                return full_path, spl
    return None, None

def smart_download():
    log("SoccerNet 경로 자동 최적화 엔진 기동", "INFO")
    
    with open("download_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    # 문자열/리스트 형식 자동 대응
    games_raw = config.get("games") or []
    games_list = [games_raw] if isinstance(games_raw, str) else games_raw

    downloader = SoccerNetDownloader(LocalDirectory="data/spotting")
    downloader.password = os.getenv("SOCCERNET_PW", "s0cc3rn3t")

    for i, item in enumerate(games_list, 1):
        print("-" * 60)
        input_path = item.strip() if isinstance(item, str) else f"{item['league']}/{item['season']}/{item['game']}"
        
        log(f"[{i}/{len(games_list)}] 입력값 확인: {input_path}")

        # 1. 자동 경로 검색
        full_path, split = find_full_path_auto(input_path)
        
        if not full_path:
            log(f"데이터셋에서 '{input_path}'와 일치하는 항목을 찾을 수 없습니다.", "ERROR")
            log("팁: 'spain_laliga/2016-2017/...' 처럼 리그와 시즌을 포함해 보세요.", "INFO")
            continue
            
        log(f"정식 경로 발견: {full_path} (세트: {split})", "SUCCESS")

        # 2. 다운로드 실행
        target_files = config.get("settings", {}).get("default_files", ["Labels-v2.json", "1_720p.mkv"])
        for f in target_files:
            log(f"다운로드 중: {f}")
            try:
                downloader.downloadGame(game=full_path, files=[f], spl=split)
                log(f"완료: {f}", "SUCCESS")
            except Exception as e:
                log(f"에러: {e}", "ERROR")

if __name__ == "__main__":
    smart_download()