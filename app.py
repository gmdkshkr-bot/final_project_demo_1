# app.py
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import json
from textwrap import shorten
from urllib.parse import quote_plus

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="Game Explorer Pro", page_icon="🎮", layout="wide")
st.title("🎮 Video Game Library")
st.markdown("게임 검색 · 상세정보 · 평가 분석 · 추천 · 즐겨찾기(Import/Export) — RAWG API 기반")

# ---------------------------
# Helpers: RAWG requests
# ---------------------------
RAWG_BASE = "https://api.rawg.io/api"

def rawg_get(path, api_key, params=None):
    if not api_key:
        return {"error": "no_api_key"}
    if params is None:
        params = {}
    params["key"] = api_key
    url = f"{RAWG_BASE}{path}"
    try:
        res = requests.get(url, params=params, timeout=12)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e), "status_code": getattr(e, 'response', None).status_code if hasattr(e, 'response') and e.response is not None else None}

# ---------------------------
# Sidebar: API key + filters + Top lists + Favorites I/O
# ---------------------------
with st.sidebar:
    st.header("🔑 API 설정")
    api_key = st.text_input("RAWG API Key 입력", type="password", help="RAWG에서 발급받은 API 키를 입력하세요.")
    st.markdown("---")

    # Filters
    st.subheader("검색 필터")
    platform_filter = st.selectbox("플랫폼", options=["All", "pc", "playstation5", "xbox-series-x", "nintendo-switch"])
    genre_filter = st.selectbox("장르", options=["All","Action","Adventure","RPG","Indie","Strategy","Shooter","Puzzle"])
    sort_option = st.selectbox("정렬 기준 (검색 결과)", options=["relevance","-rating","-added","-released"])
    st.markdown("---")

    # Popular Top list
    st.subheader("🔥 인기 게임 TOP")
    top_mode = st.selectbox("Top 기준", options=["최근 인기(added)","평점(rating)"])
    top_n = st.slider("몇 개 표시할까?", 3, 12, 6)
    if api_key:
        # try to fetch top list; best-effort, fallback on error
        ordering = "-added" if top_mode == "최근 인기(added)" else "-rating"
        top_resp = rawg_get("/games", api_key, params={"page_size": top_n, "ordering": ordering})
        if "results" in top_resp:
            for g in top_resp["results"]:
                st.write(f"• {g.get('name')} ({g.get('released','N/A')}) — ⭐ {g.get('rating')}")
        else:
            st.write("Top 리스트 로드 실패 — API 키 또는 연결 확인")
    else:
        st.write("API 키를 입력하면 Top 리스트가 표시됩니다.")

    st.markdown("---")
    st.subheader("⭐ 즐겨찾기")
    # ensure favorites exists
    if "favorites" not in st.session_state:
        st.session_state.favorites = []
    if st.session_state.favorites:
        for fav in st.session_state.favorites:
            st.write(f"- {fav.get('name')}")
    else:
        st.write("즐겨찾기 비어있음")

    # Export favorites
    st.markdown("**즐겨찾기 저장/불러오기**")
    if st.session_state.favorites:
        fav_json = json.dumps(st.session_state.favorites, ensure_ascii=False, indent=2)
        st.download_button("다운로드 (JSON)", fav_json, file_name="favorites.json", mime="application/json")
    uploaded = st.file_uploader("즐겨찾기 업로드 (.json)", type=["json"])
    if uploaded:
        try:
            loaded = json.load(uploaded)
            if isinstance(loaded, list):
                st.session_state.favorites = loaded
                st.success("즐겨찾기 불러오기 완료")
            else:
                st.error("JSON 포맷이 리스트 형식이 아닙니다.")
        except Exception as e:
            st.error(f"불러오기 실패: {e}")

# ---------------------------
# Main: Search Input
# ---------------------------
search_col1, search_col2 = st.columns([4,1])
with search_col1:
    query = st.text_input("게임 제목 검색", placeholder="예: Elden Ring, Stardew Valley, Zelda")
with search_col2:
    if st.button("검색") and not query:
        st.warning("검색어를 입력하세요.")

# Helper to build search params from filters
def build_search_params(query, platform, genre, ordering):
    params = {"search": query, "page_size": 24, "ordering": ordering}
    if platform and platform != "All":
        # RAWG expects platform id or slug; we will try slug
        params["platforms"] = platform
    if genre and genre != "All":
        params["genres"] = genre.lower()
    return params

# ---------------------------
# Search & Card Grid UI
# ---------------------------
if api_key and query:
    params = build_search_params(query, platform_filter, genre_filter, sort_option)
    resp = rawg_get("/games", api_key, params=params)
    if "error" in resp:
        st.error("검색 실패: " + str(resp.get("error")))
    else:
        results = resp.get("results", [])
        if not results:
            st.info("검색 결과가 없습니다.")
        else:
            st.markdown("### 🔎 검색 결과")
            # Render as card grid (3 columns)
            cols_per_row = 3
            rows = (len(results) + cols_per_row - 1) // cols_per_row
            for r in range(rows):
                cols = st.columns(cols_per_row)
                for c in range(cols_per_row):
                    idx = r*cols_per_row + c
                    if idx >= len(results):
                        continue
                    g = results[idx]
                    with cols[c]:
                        # Card container styling via markdown + unsafe HTML
                        st.markdown(
                            f"""
                            <div style="border:1px solid #ddd; border-radius:10px; padding:8px; box-shadow: 1px 1px 4px rgba(0,0,0,0.04);">
                              <img src="{g.get('background_image') or ''}" style="width:100%; height:140px; object-fit:cover; border-radius:6px;" />
                              <h4 style="margin:6px 0 0 0;">{g.get('name')}</h4>
                              <p style="margin:2px 0 6px 0; font-size:0.9em; color:#555;">출시: {g.get('released','N/A')}</p>
                              <p style="margin:0; font-weight:600;">⭐ {g.get('rating')}  <span style="color:#888; font-weight:400;">({g.get('ratings_count',0)})</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                        # Buttons below each card
                        btn_col1, btn_col2 = st.columns([2,1])
                        with btn_col1:
                            if st.button("자세히 보기", key=f"detail_{g['id']}"):
                                st.session_state.selected_game = {"id": g["id"], "slug": g["slug"]}
                        with btn_col2:
                            if st.button("⭐ 즐겨찾기", key=f"fav_{g['id']}"):
                                fav_item = {
                                    "id": g.get("id"),
                                    "slug": g.get("slug"),
                                    "name": g.get("name"),
                                    "released": g.get("released"),
                                    "rating": g.get("rating"),
                                    "background_image": g.get("background_image")
                                }
                                # avoid duplicates
                                if not any(f.get("id")==fav_item["id"] for f in st.session_state.favorites):
                                    st.session_state.favorites.append(fav_item)
                                    st.success(f"{g.get('name')} 즐겨찾기 추가")
                                else:
                                    st.info("이미 즐겨찾기에 있습니다.")

# ---------------------------
# Detail view (Tabs) when selected
# ---------------------------
if "selected_game" in st.session_state and st.session_state.get("selected_game"):
    sel = st.session_state.selected_game
    details = rawg_get(f"/games/{sel.get('id')}", api_key)
    if "error" in details:
        st.error("상세정보 로드 실패: " + str(details.get("error")))
    else:
        st.markdown("---")
        st.header(f"🎯 {details.get('name')}")

        # Top area: poster + basic info (two columns)
        left, right = st.columns([2,3])
        with left:
            if details.get("background_image"):
                st.image(details.get("background_image"), use_column_width=True)
            # quick actions
            if st.button("← 검색으로 돌아가기"):
                st.session_state.selected_game = None
            if st.button("⭐ 즐겨찾기 추가 (상세)"):
                fav_item = {
                    "id": details.get("id"),
                    "slug": details.get("slug"),
                    "name": details.get("name"),
                    "released": details.get("released"),
                    "rating": details.get("rating"),
                    "background_image": details.get("background_image")
                }
                if not any(f.get("id")==fav_item["id"] for f in st.session_state.favorites):
                    st.session_state.favorites.append(fav_item)
                    st.success("즐겨찾기에 추가되었습니다.")
                else:
                    st.info("이미 즐겨찾기에 있습니다.")

        with right:
            st.subheader("기본 정보")
            st.write(f"**출시일:** {details.get('released','N/A')}")
            st.write(f"**개발사:** {', '.join([d.get('name') for d in details.get('developers',[])]) if details.get('developers') else 'N/A'}")
            st.write(f"**플랫폼:** {', '.join([p['platform']['name'] for p in details.get('platforms',[])]) if details.get('platforms') else 'N/A'}")
            st.write(f"**장르:** {', '.join([g['name'] for g in details.get('genres',[])]) if details.get('genres') else 'N/A'}")
            st.write(f"**RAWG 평점:** {details.get('rating')} (ratings_count: {details.get('ratings_count')})")
            st.write(f"**Metacritic:** {details.get('metacritic','N/A')}")
            desc = details.get("description_raw") or details.get("description") or "설명 없음"
            st.markdown("**설명 (요약)**")
            st.write(shorten(desc, 900, placeholder="..."))

        # Tabs: Screenshots / Trailer / Ratings / Recommendations
        tab_screens, tab_trailer, tab_ratings, tab_reco = st.tabs(["🖼 Screenshots","🎬 Trailer","📊 Ratings","🔁 Recommendations"])

        with tab_screens:
            shots = rawg_get(f"/games/{sel.get('id')}/screenshots", api_key)
            imgs = [s.get("image") for s in shots.get("results", [])] if shots and shots.get("results") else []
            if imgs:
                # horizontal scroll container (simple)
                st.markdown("<div style='display:flex; overflow-x:auto; gap:10px;'>", unsafe_allow_html=True)
                for im in imgs:
                    st.markdown(f"<div style='min-width:300px;'><img src='{im}' style='width:300px; height:170px; object-fit:cover; border-radius:6px;' /></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.write("스크린샷 없음")

        with tab_trailer:
            movies = rawg_get(f"/games/{sel.get('id')}/movies", api_key)
            if movies and movies.get("results"):
                # take first available movie
                movie = movies["results"][0]
                # RAWG returns movie['data'] with different qualities; try '480' or 'max'
                url = movie.get("data", {}).get("480") or movie.get("data", {}).get("max")
                if url:
                    st.video(url)
                else:
                    st.write("재생 가능한 트레일러 URL이 없습니다.")
            else:
                st.write("트레일러 없음")

        with tab_ratings:
            ratings = details.get("ratings")  # list of dicts with title/count/percent
            if ratings:
                df = pd.DataFrame(ratings)
                # bar plot: percent by title
                fig, ax = plt.subplots(figsize=(6,3))
                ax.bar(df["title"], df["percent"])
                ax.set_ylabel("Percent (%)")
                ax.set_title("Ratings distribution (RAWG)")
                st.pyplot(fig)

                # pie: positive vs neutral vs negative mapping
                # mapping: exceptional/recommended -> positive, meh -> neutral, skip -> negative
                mapping = {"exceptional":"positive","recommended":"positive","meh":"neutral","skip":"negative"}
                df["sentiment"] = df["title"].map(mapping).fillna("neutral")
                sentiment_df = df.groupby("sentiment")["count"].sum().reset_index()
                fig2, ax2 = plt.subplots(figsize=(4,3))
                ax2.pie(sentiment_df["count"], labels=sentiment_df["sentiment"], autopct="%1.1f%%", startangle=140)
                ax2.set_title("Sentiment (approx.)")
                st.pyplot(fig2)
            else:
                st.write("평점 분포 데이터가 없습니다.")

        with tab_reco:
            st.write("RAWG 추천 + 장르 기반 상위 평점 조합 추천")
            # 1) RAWG suggested
            suggested = rawg_get(f"/games/{details.get('slug')}/suggested", api_key)
            suggested_list = suggested.get("results", []) if suggested and suggested.get("results") else []

            # 2) Genre-based: pick first genre slug and fetch top-rated games in same genre
            genre_based = []
            genres = details.get("genres", [])
            if genres:
                primary_genre_slug = genres[0].get("slug")
                gb_resp = rawg_get("/games", api_key, params={"genres": primary_genre_slug, "ordering": "-rating", "page_size": 6})
                if gb_resp and gb_resp.get("results"):
                    genre_based = gb_resp["results"]

            # merge and dedupe, prioritize suggested
            combined = []
            seen_ids = set()
            for g in (suggested_list + genre_based):
                gid = g.get("id")
                if gid and gid not in seen_ids and (gid != details.get("id")):
                    combined.append(g)
                    seen_ids.add(gid)

            if combined:
                cols = st.columns(3)
                for i, g in enumerate(combined[:6]):
                    with cols[i % 3]:
                        st.image(g.get("background_image") or "", width=200)
                        st.write(g.get("name"))
                        st.write(f"⭐ {g.get('rating')}  ({g.get('released','N/A')})")
                        if st.button("자세히", key=f"rec_detail_{g.get('id')}"):
                            st.session_state.selected_game = {"id": g["id"], "slug": g["slug"]}
                        if st.button("즐겨찾기", key=f"rec_fav_{g.get('id')}"):
                            fav_item = {
                                "id": g.get("id"),
                                "slug": g.get("slug"),
                                "name": g.get("name"),
                                "released": g.get("released"),
                                "rating": g.get("rating"),
                                "background_image": g.get("background_image")
                            }
                            if not any(f.get("id")==fav_item["id"] for f in st.session_state.favorites):
                                st.session_state.favorites.append(fav_item)
                                st.success("즐겨찾기 추가")
                            else:
                                st.info("이미 즐겨찾기에 있습니다.")
            else:
                st.write("추천 게임이 없습니다.")

# ---------------------------
# Footer / credits
# ---------------------------
st.markdown("---")
st.caption("데이터 출처: RAWG Video Games Database API. API 키는 사용자의 입력을 통해 직접 전달됩니다.")
