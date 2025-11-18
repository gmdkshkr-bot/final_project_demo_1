import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Game Explorer", layout="wide")

# ------------------------------------------------------
# Helper functions
# ------------------------------------------------------

def search_games(api_key, query):
    url = f"https://api.rawg.io/api/games"
    params = {
        "key": api_key,
        "search": query,
        "page_size": 10
    }
    res = requests.get(url, params=params)
    return res.json()


def get_game_details(api_key, game_id):
    url = f"https://api.rawg.io/api/games/{game_id}"
    params = {"key": api_key}
    res = requests.get(url, params=params)
    return res.json()


def get_screenshots(api_key, game_id):
    url = f"https://api.rawg.io/api/games/{game_id}/screenshots"
    params = {"key": api_key}
    res = requests.get(url, params=params)
    return res.json()


def get_trailers(api_key, game_id):
    url = f"https://api.rawg.io/api/games/{game_id}/movies"
    params = {"key": api_key}
    res = requests.get(url, params=params)
    return res.json()


def get_recommended(api_key, game_slug):
    url = f"https://api.rawg.io/api/games/{game_slug}/suggested"
    params = {"key": api_key}
    res = requests.get(url, params=params)
    return res.json()


# ------------------------------------------------------
# Sidebar
# ------------------------------------------------------

st.sidebar.header("🔑 API 설정")
api_key = st.sidebar.text_input("RAWG API Key 입력", type="password")

if not api_key:
    st.sidebar.warning("API 키를 입력해야 검색 기능을 사용할 수 있습니다.")
else:
    st.sidebar.success("API 키가 등록되었습니다!")

if "favorites" not in st.session_state:
    st.session_state.favorites = []


st.sidebar.subheader("⭐ 즐겨찾기")
if st.session_state.favorites:
    for fav in st.session_state.favorites:
        st.sidebar.write(f"- {fav}")
else:
    st.sidebar.write("아직 즐겨찾기가 없습니다.")


# ------------------------------------------------------
# Main Title
# ------------------------------------------------------

st.title("🎮 Game Explorer")
st.write("RAWG API를 이용한 게임 검색 및 상세 정보 탐색 앱")

query = st.text_input("게임 제목 검색")

# ------------------------------------------------------
# Search Results
# ------------------------------------------------------

if api_key and query:
    data = search_games(api_key, query)

    if "results" in data:
        for game in data["results"]:
            cols = st.columns([1, 3])

            with cols[0]:
                if game.get("background_image"):
                    st.image(game["background_image"], width=150)
                else:
                    st.write("No Image")

            with cols[1]:
                st.subheader(game["name"])
                st.write("출시일:", game.get("released", "정보 없음"))
                st.write("평점:", game.get("rating", "N/A"))

                details_btn = st.button(f"자세히 보기 - {game['id']}", key=f"detail_{game['id']}")

                if details_btn:
                    st.session_state["selected_game_id"] = game["id"]
                    st.session_state["selected_game_slug"] = game["slug"]

# ------------------------------------------------------
# Game Details Page
# ------------------------------------------------------

if api_key and "selected_game_id" in st.session_state:
    game_id = st.session_state["selected_game_id"]
    game_slug = st.session_state["selected_game_slug"]

    st.markdown("---")
    st.header("🎯 게임 상세 정보")

    details = get_game_details(api_key, game_id)

    st.subheader(details["name"])

    top_cols = st.columns([2, 3])

    with top_cols[0]:
        st.image(details.get("background_image"), width=350)

        if st.button("⭐ 즐겨찾기 추가"):
            st.session_state.favorites.append(details["name"])
            st.success(f"{details['name']} 추가됨!")

    with top_cols[1]:
        st.write("**출시일:**", details.get("released", "N/A"))
        st.write("**평점:**", details.get("rating"))
        st.write("**메타크리틱:**", details.get("metacritic", "N/A"))
        st.write("**플랫폼:**", ", ".join([p["platform"]["name"] for p in details["platforms"]]))
        st.write("**장르:**", ", ".join([g["name"] for g in details["genres"]]))

    st.markdown("### 📘 게임 설명")
    st.write(details.get("description_raw", "설명 없음"))

    # ------------------------------
    # Screenshots
    # ------------------------------
    st.markdown("### 🖼️ 스크린샷")

    screenshots = get_screenshots(api_key, game_id)
    if "results" in screenshots:
        img_cols = st.columns(3)
        for i, ss in enumerate(screenshots["results"][:3]):
            img_cols[i].image(ss["image"])
    else:
        st.write("스크린샷 없음")

    # ------------------------------
    # Trailer
    # ------------------------------
    st.markdown("### 🎬 트레일러")
    trailers = get_trailers(api_key, game_id)

    if "results" in trailers and len(trailers["results"]) > 0:
        trailer = trailers["results"][0]["data"]["480"]
        st.video(trailer)
    else:
        st.write("트레일러 없음")

    # ------------------------------
    # Recommended games
    # ------------------------------

    st.markdown("### 🎮 비슷한 게임 추천")
    rec = get_recommended(api_key, game_slug)

    if "results" in rec:
        rec_cols = st.columns(3)
        for i, r in enumerate(rec["results"][:3]):
            with rec_cols[i]:
                st.image(r.get("background_image"), width=200)
                st.write(r["name"])
    else:
        st.write("추천 게임 없음")

