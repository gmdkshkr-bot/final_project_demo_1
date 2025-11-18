# app.py
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from textwrap import shorten

# ---------------------------
# 설정
# ---------------------------
# RAWG API 키는 환경변수나 Streamlit secrets에 저장하는 걸 권장합니다.
# 예) st.secrets["RAWG_API_KEY"] 또는 환경변수 RAWG_API_KEY
RAWG_API_KEY = st.secrets.get("RAWG_API_KEY", None) or st.experimental_get_query_params().get("rawg_api_key", [None])[0]

BASE_URL = "https://api.rawg.io/api"

HEADERS = {
    "User-Agent": "Game-Explorer-App/1.0 (+https://your-app-url.example)"  # RAWG 권장: User-Agent 지정
}

# ---------------------------
# 헬퍼 함수: RAWG 요청
# ---------------------------
def rawg_get(endpoint: str, params: dict = None):
    """GET 요청 래퍼: endpoint는 '/games' 같은 경로(앞의 / 포함 가능)"""
    if params is None:
        params = {}
    if RAWG_API_KEY:
        params["key"] = RAWG_API_KEY
    url = endpoint if endpoint.startswith("http") else f"{BASE_URL}{endpoint}"
    res = requests.get(url, params=params, headers=HEADERS, timeout=15)
    try:
        res.raise_for_status()
    except Exception as e:
        st.error(f"API 요청 실패: {e} (status={res.status_code})")
        return None
    return res.json()

# ---------------------------
# 기능: 검색, 상세조회, 추천, 스크린샷
# ---------------------------
def search_games(query: str, page_size: int = 12):
    params = {"search": query, "page_size": page_size}
    return rawg_get("/games", params)

def get_game_details(slug_or_id):
    # RAWG supports slug or id in games/{slug}
    return rawg_get(f"/games/{slug_or_id}")

def get_screenshots(slug_or_id):
    return rawg_get(f"/games/{slug_or_id}/screenshots")

def get_suggested(slug_or_id, page_size: int = 5):
    return rawg_get(f"/games/{slug_or_id}/suggested", params={"page_size": page_size})

# ---------------------------
# UI 헬퍼: 카드 렌더링
# ---------------------------
def render_game_card(game, key_prefix=""):
    """검색 결과 가운데 카드형 UI로 표시"""
    img = game.get("background_image")
    name = game.get("name")
    released = game.get("released") or "N/A"
    rating = game.get("rating") or 0
    rating_count = game.get("ratings_count") or 0
    col1, col2 = st.columns([1, 3])
    with col1:
        if img:
            st.image(img, use_column_width=True, caption=None)
        else:
            st.write("No image")
    with col2:
        st.subheader(name)
        st.write(f"출시일: {released}")
        st.write(f"RAWG 평점: {rating} ({rating_count}명)")
        if st.button("자세히 보기", key=f"detail_{key_prefix}{game.get('slug') or game.get('id')}"):
            st.session_state.selected_game = game.get("slug") or game.get("id")

# ---------------------------
# 분석용: 평점 분포 차트
# ---------------------------
def plot_ratings_distribution(ratings):
    # RAWG 'ratings' 예시: [{"id":5,"title":"exceptional","count":123,"percent":56.78}, ...]
    if not ratings:
        st.write("평점 데이터가 없습니다.")
        return
    df = pd.DataFrame(ratings)
    # 그래프 간단히 matplotlib로 그리기
    fig, ax = plt.subplots(figsize=(6,3))
    ax.bar(df["title"], df["percent"])
    ax.set_ylabel("Percent (%)")
    ax.set_title("Ratings distribution (RAWG)")
    st.pyplot(fig)

# ---------------------------
# 즐겨찾기 관리
# ---------------------------
if "favorites" not in st.session_state:
    st.session_state.favorites = []

if "selected_game" not in st.session_state:
    st.session_state.selected_game = None

# ---------------------------
# Streamlit 레이아웃
# ---------------------------
st.set_page_config(page_title="Game Explorer", page_icon=":video_game:", layout="wide")
st.title("🎮 Game Explorer — 게임 검색 & 상세 분석")

# 사이드바: 검색 옵션, favorites
with st.sidebar:
    st.header("설정 & 즐겨찾기")
    if not RAWG_API_KEY:
        st.warning("RAWG API 키가 설정되어 있지 않습니다. 검색을 사용하려면 RAWG_API_KEY를 설정하세요. (README 참고)")
    platform_filter = st.selectbox("플랫폼 필터 (선택)", options=["All","pc","playstation5","xbox-series-x"], index=0)
    genre_filter = st.selectbox("장르 필터 (선택)", options=["All","Action","Adventure","RPG","Indie"], index=0)

    st.markdown("---")
    st.subheader("즐겨찾기")
    if st.session_state.favorites:
        for fav in st.session_state.favorites:
            st.write(f"- {fav.get('name')} ({fav.get('released','N/A')})")
        if st.button("즐겨찾기 전체 해제"):
            st.session_state.favorites = []
    else:
        st.write("아직 즐겨찾기가 없습니다.")

# 메인: 검색창
col_search, col_empty = st.columns([4,1])
with col_search:
    query = st.text_input("게임 제목으로 검색", placeholder="예: Elden Ring, Zelda, Stardew Valley")
    if st.button("검색") and query:
        st.session_state.selected_game = None
        st.session_state.search_query = query

# 검색 결과 표시
if st.session_state.get("search_query"):
    st.markdown("### 검색 결과")
    data = search_games(st.session_state.search_query, page_size=12)
    if data and data.get("results"):
        games = data["results"]
        # 카드 그리기: 3열
        cols = st.columns(3)
        for i, g in enumerate(games):
            with cols[i % 3]:
                render_game_card(g, key_prefix="search_")
    else:
        st.write("검색 결과가 없습니다.")

# 상세 페이지: selected_game가 설정된 경우
if st.session_state.selected_game:
    st.markdown("---")
    st.markdown("### 게임 상세 정보")
    details = get_game_details(st.session_state.selected_game)
    if details:
        left, right = st.columns([2,3])
        with left:
            if details.get("background_image"):
                st.image(details.get("background_image"), use_column_width=True)
            st.markdown("**기본 정보**")
            st.write(f"이름: {details.get('name')}")
            st.write(f"출시일: {details.get('released')}")
            st.write(f"개발사: {', '.join([d.get('name') for d in details.get('developers',[])]) if details.get('developers') else 'N/A'}")
            st.write(f"플랫폼: {', '.join([p.get('platform',{}).get('name') for p in details.get('platforms',[])]) if details.get('platforms') else 'N/A'}")
            st.write(f"장르: {', '.join([g.get('name') for g in details.get('genres',[])]) if details.get('genres') else 'N/A'}")
            # 즐겨찾기 버튼
            if st.button("💾 즐겨찾기 추가"):
                # 간단히 필요한 정보만 저장
                st.session_state.favorites.append({
                    "id": details.get("id"),
                    "slug": details.get("slug"),
                    "name": details.get("name"),
                    "released": details.get("released"),
                    "background_image": details.get("background_image"),
                })
                st.success("즐겨찾기에 추가했습니다.")
            if st.button("← 검색으로 돌아가기"):
                st.session_state.selected_game = None

        with right:
            st.markdown("**설명(요약)**")
            desc = details.get("description_raw") or details.get("description") or "설명 없음"
            st.write(shorten(desc, width=800, placeholder="..."))

            st.markdown("**평점 / 통계**")
            st.write(f"RAWG 평점: {details.get('rating')}  (ratings_count: {details.get('ratings_count')})")
            # ratings distribution (RAWG 제공)
            ratings = details.get("ratings")
            plot_ratings_distribution(ratings)

            # 메타크리틱(있는 경우)
            metacritic = details.get("metacritic")
            if metacritic:
                st.write(f"Metacritic: {metacritic}")
            else:
                st.write("Metacritic 점수 없음")

            # 스크린샷
            st.markdown("**스크린샷**")
            shots = get_screenshots(details.get("slug") or details.get("id"))
            if shots and shots.get("results"):
                shot_imgs = [s.get("image") for s in shots.get("results")][:6]
                st.image(shot_imgs, width=200)
            else:
                st.write("스크린샷 없음")

            # 추천 게임
            st.markdown("**추천 게임**")
            suggested = get_suggested(details.get("slug") or details.get("id"))
            if suggested and suggested.get("results"):
                sug_cols = st.columns(len(suggested["results"]))
                for i, sg in enumerate(suggested["results"][:5]):
                    with sug_cols[i]:
                        st.image(sg.get("background_image"), width=120)
                        st.write(sg.get("name"))
                        if st.button("자세히", key=f"suggest_{sg.get('slug')}"):
                            st.session_state.selected_game = sg.get("slug")
            else:
                st.write("추천 게임 데이터 없음")

# footer
st.markdown("---")
st.caption("데이터 출처: RAWG Video Games Database API. (앱에서 검색/상세/추천 API를 사용합니다.)")
