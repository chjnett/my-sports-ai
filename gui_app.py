import os
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from SoccerNet.Downloader import SoccerNetDownloader, getListGames


SPLITS = ["train", "valid", "test", "challenge"]
LOCAL_DIR = Path("data") / "spotting"

FILE_OPTIONS = {
    "1_720p.mkv": "전반전 풀 영상 720p",
    "2_720p.mkv": "후반전 풀 영상 720p",
    "1_224p.mkv": "전반전 저해상도 영상 224p",
    "2_224p.mkv": "후반전 저해상도 영상 224p",
    "Labels-v2.json": "Action spotting 라벨 JSON",
}

DOWNLOAD_PRESETS = {
    "라벨 + 풀 경기 영상 720p": ["Labels-v2.json", "1_720p.mkv", "2_720p.mkv"],
    "풀 경기 영상 720p": ["1_720p.mkv", "2_720p.mkv"],
    "저해상도 영상 224p": ["1_224p.mkv", "2_224p.mkv"],
    "라벨 JSON만": ["Labels-v2.json"],
    "직접 선택": [],
}


@st.cache_data(show_spinner=False)
def load_games(split: str) -> list[str]:
    return getListGames(split=split, task="spotting")


def parse_match_date(match_name: str) -> date | None:
    match = re.match(r"(\d{4}-\d{2}-\d{2})", match_name)
    if not match:
        return None

    return datetime.strptime(match.group(1), "%Y-%m-%d").date()


def parse_match_teams(match_name: str) -> tuple[str, str] | None:
    title = re.sub(r"^\d{4}-\d{2}-\d{2} - \d{2}-\d{2} ", "", match_name)
    match = re.match(r"(.+?) \d+ - \d+ (.+)$", title)
    if not match:
        return None

    return match.group(1).strip(), match.group(2).strip()


def build_game_rows(selected_splits: list[str]) -> list[dict[str, str]]:
    rows = []

    for split in selected_splits:
        for game in load_games(split):
            parts = game.split("/")
            match_name = parts[-1]
            match_date = parse_match_date(match_name)
            rows.append(
                {
                    "download": False,
                    "split": split,
                    "league": parts[0] if len(parts) > 0 else "",
                    "season": parts[1] if len(parts) > 1 else "",
                    "date": match_date,
                    "match": match_name,
                    "path": game,
                }
            )

    return rows


def find_related_games(base_game: dict[str, object], all_games: pd.DataFrame) -> pd.DataFrame:
    exact = all_games[all_games["path"] == base_game["path"]]
    teams = parse_match_teams(str(base_game["match"]))

    if not teams:
        return exact

    team_a, team_b = teams
    same_context = all_games[
        (all_games["league"] == base_game["league"])
        & (all_games["season"] == base_game["season"])
    ].copy()
    match_text = same_context["match"].str.lower()
    related = same_context[
        match_text.str.contains(team_a.lower(), regex=False)
        | match_text.str.contains(team_b.lower(), regex=False)
    ]

    return (
        pd.concat([exact, related])
        .drop_duplicates(subset=["split", "path"])
        .sort_values(by=["split", "date", "match"], na_position="last")
    )


def filter_games(
    games: pd.DataFrame,
    keyword: str,
    leagues: list[str],
    seasons: list[str],
    date_range: tuple[date, date] | None,
) -> pd.DataFrame:
    filtered = games.copy()
    keyword = keyword.strip().lower()

    if keyword:
        searchable = (
            filtered["league"].astype(str)
            + " "
            + filtered["season"].astype(str)
            + " "
            + filtered["match"].astype(str)
            + " "
            + filtered["path"].astype(str)
        ).str.lower()
        filtered = filtered[searchable.str.contains(keyword, regex=False)]

    if leagues:
        filtered = filtered[filtered["league"].isin(leagues)]

    if seasons:
        filtered = filtered[filtered["season"].isin(seasons)]

    if date_range:
        start_date, end_date = date_range
        has_date = filtered["date"].notna()
        in_range = filtered["date"].between(start_date, end_date)
        filtered = filtered[has_date & in_range]

    return filtered


def download_games(games: list[dict[str, str]], files: list[str]) -> None:
    password = os.getenv("SOCCERNET_PW", "s0cc3rn3t")
    downloader = SoccerNetDownloader(LocalDirectory=str(LOCAL_DIR))
    downloader.password = password

    progress = st.progress(0)
    status = st.empty()
    log = st.container()

    for index, game in enumerate(games, start=1):
        status.write(f"Downloading {index}/{len(games)}: {game['path']}")

        try:
            downloader.downloadGame(game=game["path"], files=files, spl=game["split"])
            log.success(f"Done: [{game['split']}] {game['path']}")
        except Exception as exc:
            log.error(f"Failed: [{game['split']}] {game['path']} - {exc}")

        progress.progress(index / len(games))

    status.write("Download job finished.")


st.set_page_config(page_title="SoccerNet Downloader", layout="wide")

st.title("SoccerNet 영상 다운로드")
st.caption("경기 목록을 split별로 불러온 뒤, 조건으로 선별하고 정렬해서 받을 경기만 체크합니다.")

with st.sidebar:
    st.header("1. 데이터 split")
    selected_splits = st.multiselect(
        "받을 데이터 split을 선택하세요",
        SPLITS,
        default=SPLITS,
        help="SoccerNet의 train, valid, test, challenge 목록을 각각 불러옵니다.",
    )

    st.header("2. 다운로드 종류")
    download_mode = st.radio(
        "무엇을 받을까요?",
        options=list(DOWNLOAD_PRESETS.keys()),
        index=0,
        help="풀 경기 영상은 전반전과 후반전 mkv 파일을 함께 받습니다.",
    )

    if download_mode == "직접 선택":
        selected_files = st.multiselect(
            "다운로드할 파일",
            options=list(FILE_OPTIONS.keys()),
            default=["1_720p.mkv", "2_720p.mkv"],
            format_func=lambda value: f"{value} - {FILE_OPTIONS[value]}",
        )
    else:
        selected_files = DOWNLOAD_PRESETS[download_mode]
        st.write("선택된 파일")
        for file_name in selected_files:
            st.code(f"{file_name} - {FILE_OPTIONS[file_name]}", language=None)

    st.info(
        "720p 풀 영상 다운로드는 SoccerNet NDA 승인과 올바른 SOCCERNET_PW가 필요합니다.",
        icon=None,
    )

    if st.button("경기 목록 새로고침", width="stretch"):
        st.cache_data.clear()
        st.rerun()


if not selected_splits:
    st.info("왼쪽 사이드바에서 최소 1개의 split을 선택하세요.")
    st.stop()

with st.spinner("SoccerNet 경기 목록을 불러오는 중..."):
    rows = build_game_rows(selected_splits)

if not rows:
    st.warning("현재 조건에 맞는 경기가 없습니다.")
    st.stop()

all_games = pd.DataFrame(rows)

st.subheader("3. 선별 조건")

filter_left, filter_mid, filter_right = st.columns([1.2, 1, 1])
with filter_left:
    keyword = st.text_input(
        "팀/경기/리그 검색",
        placeholder="Barcelona, Chelsea, 2017, spain_laliga...",
    )
with filter_mid:
    available_leagues = sorted(all_games["league"].dropna().unique().tolist())
    selected_leagues = st.multiselect("리그", available_leagues)
with filter_right:
    available_seasons = sorted(all_games["season"].dropna().unique().tolist(), reverse=True)
    selected_seasons = st.multiselect("시즌", available_seasons)

dated_games = all_games[all_games["date"].notna()]
date_range = None
sort_left, sort_mid, sort_right = st.columns([1, 1, 1])
with sort_left:
    if not dated_games.empty:
        min_date = dated_games["date"].min()
        max_date = dated_games["date"].max()
        selected_date_range = st.date_input(
            "경기 날짜 범위",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
            date_range = selected_date_range
with sort_mid:
    sort_column = st.selectbox(
        "정렬 기준",
        ["date", "league", "season", "match", "split"],
        format_func={
            "date": "날짜",
            "league": "리그",
            "season": "시즌",
            "match": "경기명",
            "split": "Split",
        }.get,
    )
with sort_right:
    sort_ascending = st.radio("정렬 방향", ["오름차순", "내림차순"], horizontal=True) == "오름차순"

filtered_games = filter_games(
    all_games,
    keyword=keyword,
    leagues=selected_leagues,
    seasons=selected_seasons,
    date_range=date_range,
)

secondary_sort_columns = [column for column in ["league", "season", "match"] if column != sort_column]
sort_columns = [sort_column, *secondary_sort_columns]

filtered_games = filtered_games.sort_values(
    by=sort_columns,
    ascending=[sort_ascending, *([True] * len(secondary_sort_columns))],
    na_position="last",
)

result_left, result_mid, result_right = st.columns([1, 1, 1])
with result_left:
    st.metric("전체 경기", len(all_games))
with result_mid:
    st.metric("선별된 경기", len(filtered_games))
with result_right:
    max_rows = st.number_input(
        "화면에 표시할 개수",
        min_value=10,
        max_value=max(10, len(filtered_games)),
        value=min(100, max(10, len(filtered_games))),
        step=10,
    )

display_games = filtered_games.head(max_rows).copy()

bulk_left, bulk_right = st.columns([1, 4])
with bulk_left:
    select_all_visible = st.button("현재 목록 전체 선택", width="stretch")
with bulk_right:
    clear_selection = st.button("선택 초기화", width="content")

if select_all_visible:
    display_games["download"] = True
elif clear_selection:
    display_games["download"] = False

if display_games.empty:
    st.warning("선별 조건에 맞는 경기가 없습니다.")
    st.stop()

st.subheader("4. 경기 선택")
st.caption(f"현재 {len(display_games)}개를 표시 중입니다. 필요한 경기만 체크하세요.")

edited = st.data_editor(
    display_games,
    hide_index=True,
    width="stretch",
    disabled=["split", "league", "season", "date", "match", "path"],
    column_config={
        "download": st.column_config.CheckboxColumn("선택"),
        "split": st.column_config.TextColumn("Split", width="small"),
        "league": st.column_config.TextColumn("리그", width="medium"),
        "season": st.column_config.TextColumn("시즌", width="small"),
        "date": st.column_config.DateColumn("날짜", width="small"),
        "match": st.column_config.TextColumn("경기", width="large"),
        "path": st.column_config.TextColumn("SoccerNet 경로", width="large"),
    },
)

selected_games = edited[edited["download"]].to_dict("records")

st.subheader("5. 선택한 경기 기준으로 split 찾기")

with st.expander("선택한 경기 중 하나로 다른 split 후보 찾기", expanded=bool(selected_games)):
    st.caption(
        "아래 경기 선택 테이블에서 체크한 경기만 기준 경기 후보로 사용합니다. "
        "완전히 같은 영상은 SoccerNet 경로가 같은 항목이고, 없으면 같은 리그/시즌에서 팀명이 겹치는 후보를 같이 보여줍니다."
    )

    if not selected_games:
        st.info("먼저 위 경기 선택 테이블에서 기준으로 삼을 경기를 체크하세요.")
    else:
        base_game = st.selectbox(
            "기준 경기",
            selected_games,
            format_func=lambda game: (
                f"[{game['split']}] {game['league']} / {game['season']} / {game['match']}"
            ),
        )

        with st.spinner("전체 split에서 같은 경기 후보를 찾는 중..."):
            all_split_games = pd.DataFrame(build_game_rows(SPLITS))
            related_games = find_related_games(base_game, all_split_games)

        exact_matches = related_games[related_games["path"] == base_game["path"]]
        other_split_exact = exact_matches[exact_matches["split"] != base_game["split"]]

        if other_split_exact.empty:
            st.warning(
                "다른 split에서 완전히 동일한 SoccerNet 경로는 찾지 못했습니다. "
                "대부분의 데이터셋 split은 같은 경기가 겹치지 않게 나뉩니다."
            )
        else:
            st.success("다른 split에서 동일 경기를 찾았습니다.")

        st.dataframe(
            related_games[["split", "league", "season", "date", "match", "path"]],
            hide_index=True,
            width="stretch",
        )

left, right = st.columns([1, 3])
with left:
    start = st.button(
        f"선택한 {len(selected_games)}경기 다운로드",
        disabled=not selected_games or not selected_files,
        type="primary",
        width="stretch",
    )

with right:
    if selected_games:
        st.write(f"선택한 경기: {len(selected_games)}개")
        st.write(f"다운로드 파일: {', '.join(selected_files)}")
        with st.expander("선택한 경기 미리보기", expanded=False):
            st.dataframe(
                pd.DataFrame(selected_games)[["split", "league", "season", "date", "match"]],
                hide_index=True,
                width="stretch",
            )
    if not selected_files:
        st.warning("다운로드할 파일을 최소 1개 선택하세요.")

if start:
    download_games(selected_games, selected_files)
