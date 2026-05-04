import os
import questionary
from SoccerNet.Downloader import SoccerNetDownloader, getListGames
from tqdm import tqdm
from pathlib import Path

def get_game_list(keyword):
    """모든 split을 뒤져서 키워드가 포함된 경기를 가져옵니다."""
    results = []
    for spl in ["train", "valid", "test", "challenge"]: #
        games = getListGames(split=spl, task="spotting") #
        for g in games:
            if keyword.lower() in g.lower():
                results.append({"name": f"[{spl}] {g}", "path": g, "split": spl})
    return results

def main():
    print("\n⚽ SoccerNet 대화형 다운로드 매니저\n")

    # 1. 검색 키워드 입력
    keyword = questionary.text("검색할 팀명이나 리그를 입력하세요 (예: Barcelona):").ask()
    if not keyword: return

    # 2. 경기 목록 조회
    matches = get_game_list(keyword)
    if not matches:
        print("❌ 일치하는 경기가 없습니다.")
        return

    # 3. 경기 선택 (체크박스)
    choices = [questionary.Choice(m["name"], value=m) for m in matches]
    selected_games = questionary.checkbox(
        f"다운로드할 경기를 선택하세요 ({len(choices)}개 발견):",
        choices=choices
    ).ask()

    if not selected_games: return

    # 4. 다운로드할 파일 종류 선택
    file_choices = [
        {"name": "라벨 데이터 (Labels-v2.json)", "value": "Labels-v2.json"},
        {"name": "전반전 고화질 (1_720p.mkv)", "value": "1_720p.mkv"},
        {"name": "후반전 고화질 (2_720p.mkv)", "value": "2_720p.mkv"},
        {"name": "저화질 테스트용 (1_224p.mkv)", "value": "1_224p.mkv"}
    ]
    selected_files = questionary.checkbox(
        "다운로드할 구성 요소를 선택하세요:",
        choices=[questionary.Choice(f["name"], value=f["value"]) for f in file_choices]
    ).ask()

    if not selected_files: return

    # 5. 다운로드 실행
    pw = os.getenv("SOCCERNET_PW", "s0cc3rn3t") #
    downloader = SoccerNetDownloader(LocalDirectory="data/spotting")
    downloader.password = pw

    print(f"\n🚀 총 {len(selected_games)}개의 경기 다운로드를 시작합니다.")
    
    for game_info in selected_games:
        print(f"\n📦 처리 중: {game_info['path']}")
        try:
            # 선택한 파일들 다운로드
            downloader.downloadGame(
                game=game_info['path'], 
                files=selected_files, 
                spl=game_info['split']
            )
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

    print("\n✅ 모든 작업이 완료되었습니다!")

if __name__ == "__main__":
    main()