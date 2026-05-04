from SoccerNet.Downloader import getListGames

def find_exact_names():
    print("🔍 SoccerNet 데이터베이스에서 일치하는 경기를 찾는 중...")
    
    # 검색하고 싶은 키워드 (예: 팀 이름)
    keywords = ["Alaves", "Barcelona", "Chelsea", "Manchester"]
    
    found_any = False
    for spl in ["train", "valid", "test", "challenge"]:
        # spotting 태스크의 전체 목록 로드
        all_games = getListGames(split=spl, task="spotting")
        
        for game_path in all_games:
            # 키워드 중 하나라도 포함되어 있으면 출력
            if any(k.lower() in game_path.lower() for k in keywords):
                print(f"📍 [{spl}] {game_path}")
                found_any = True
                
    if not found_any:
        print("❌ 검색된 경기가 없습니다. 키워드를 변경해 보세요.")

if __name__ == "__main__":
    find_exact_names()