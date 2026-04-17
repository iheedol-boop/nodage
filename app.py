import streamlit as st

# 1. 페이지 설정 (아이콘 및 타이틀)
st.set_page_config(page_title="My Mobile App", page_icon="📱", layout="centered")

# 2. 핸드폰 앱 느낌을 위한 CSS 주입
st.markdown("""
    <style>
    /* 메인 컨테이너 너비 제한 (핸드폰 비율) */
    .block-container {
        max-width: 400px;
        padding-top: 2rem;
        padding-bottom: 10rem;
    }
    /* 하단 네비게이션 바 스타일 */
    .stBottom {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: white;
        z-index: 100;
    }
    /* 버튼 둥글게 */
    .stButton>button {
        border-radius: 20px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 사이드바 대신 상단/하단 탭 구성 (앱스러운 방식)
tabs = st.tabs(["🏠 홈", "🔍 검색", "👤 프로필"])

with tabs[0]:
    st.title("안녕하세요! 👋")
    st.subheader("오늘의 추천 콘텐츠")
    
    # 카드 스타일 레이아웃
    with st.container(border=True):
        st.image("https://placeholder.com", caption="오늘의 뉴스")
        st.write("Streamlit으로 만드는 모바일 UI 가이드입니다.")
        if st.button("자세히 보기", key="btn1"):
            st.toast("버튼이 클릭되었습니다!")

with tabs[1]:
    st.text_input("무엇을 찾으시나요?", placeholder="검색어를 입력하세요")
    st.write("인기 검색어: #파이썬 #스트림릿 #앱개발")

with tabs[2]:
    st.write("내 정보")
    st.divider()
    st.button("로그아웃", type="primary")
