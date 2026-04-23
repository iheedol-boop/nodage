import streamlit as st

# 페이지 설정
st.set_page_config(layout="wide")

st.title("🚀 나의 웹 대시보드")

# 상단 탭 생성
tab1, tab2, tab3 = st.tabs(["홈", "분석 결과", "설정"])

with tab1:
    st.header("Home")
    st.write("여기는 메인 탭입니다.")

with tab2:
    st.header("Analysis")
    # 다른 파일의 함수를 불러와서 넣을 수도 있습니다.
    st.info("차트나 데이터를 여기에 띄웁니다.")

with tab3:
    st.header("Settings")
    st.write("환경 설정 화면입니다.")
