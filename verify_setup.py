import os
from pathlib import Path

from SoccerNet.Downloader import SoccerNetDownloader, getListGames


def check_setup():
    print("--- [1/2] 라이브러리 로드 테스트 ---")
    try:
        import SoccerNet
        print("✅ SoccerNet 라이브러리가 성공적으로 로드되었습니다.")
    except ImportError:
        print("❌ 라이브러리 로드 실패.")
        return

    print("\n--- [2/2] 데이터 접근 테스트 ---")
    pw = os.getenv("SOCCERNET_PW", "s0cc3rn3t")

    # 저장 경로를 data 폴더로 지정하여 다운로더 초기화
    local_dir = Path("data") / "spotting"
    downloader = SoccerNetDownloader(LocalDirectory=str(local_dir))
    downloader.password = pw

    try:
        # valid split의 첫 경기 라벨 하나만 다운로드하여 연결 확인
        game = getListGames(split="valid", task="spotting")[0]
        label_file = local_dir / game / "Labels-v2.json"

        downloader.downloadGame(game=game, files=["Labels-v2.json"], spl="valid")

        if not label_file.exists() or label_file.stat().st_size == 0:
            raise RuntimeError(f"라벨 파일 다운로드 확인 실패: {label_file}")

        print("\n✅ API 연결 및 데이터 다운로드 테스트 성공!")
        print("이제 프로젝트를 시작할 준비가 되었습니다.")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        print("네트워크 상태나 비밀번호(SOCCERNET_PW)를 확인하세요.")


if __name__ == "__main__":
    check_setup()
