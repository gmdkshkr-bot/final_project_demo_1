# final_project_demo_1
게임 검색 + 상세 정보 + 평가 분석 앱 (RAWG API 기반)

# Game Explorer (Streamlit + RAWG API)

## 개요
Game Explorer는 RAWG Video Games Database API를 이용해 게임을 검색하고,
게임의 상세 정보(설명, 플랫폼, 장르, 평점, 스크린샷)와 추천 게임을 보여주는 Streamlit 웹 앱입니다.
또한 RAWG가 제공하는 평점 분포를 시각화합니다.

## 주요 기능
- 게임 제목 검색
- 검색 결과 카드형 표시 (포스터, 제목, 평점, 출시일)
- 게임 상세 페이지 (설명, 개발사, 플랫폼, 장르, 스크린샷)
- 평점 분포 시각화
- RAWG 기반 추천 게임 표시
- 즐겨찾기(로컬 세션 저장)

## 사용 API
- RAWG Video Games Database API — 검색, 상세, 추천, 스크린샷 엔드포인트 사용. (모든 요청에 API 키 필요) :contentReference[oaicite:2]{index=2}

## 설치 및 실행 (로컬)
1. 레포지토리 클론
2. 가상환경 생성 (권장) 후 `pip install -r requirements.txt`
3. RAWG API 키 발급:
   - RAWG에 가입 후 API 키를 발급받으세요: https://rawg.io/apidocs. :contentReference[oaicite:3]{index=3}
4. Streamlit에서 키 설정(예시):
   - 방법 A) `secrets.toml` 사용 (Streamlit Cloud 배포 시)
     ```
     [global]
     RAWG_API_KEY = "여기에_당신의_API_KEY"
     ```
   - 방법 B) 로컬 실행 시 환경변수 설정:
     - macOS/Linux: `export RAWG_API_KEY="여기에_당신의_API_KEY"`
     - Windows (PowerShell): `setx RAWG_API_KEY "여기에_당신의_API_KEY"`
5. 실행:
