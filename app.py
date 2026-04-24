import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. 페이지 설정 (모바일 최적화 레이아웃)
st.set_page_config(page_title="나의 자산 관리", layout="centered")

st.title("💰 개인 자산 관리자")

# 2. 데이터 불러오기 (간단하게 CSV 저장 방식 사용)
def load_data():
    try:
        return pd.read_csv("assets_data.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["날짜", "카테고리", "금액", "메모"])

data = load_data()

# 3. 사이드바/입력창: 데이터 추가
with st.expander("➕ 내역 추가하기"):
    with st.form("input_form", clear_on_submit=True):
        date = st.date_input("날짜", datetime.now())
        category = st.selectbox("카테고리", ["예적금", "주식/코인", "부동산", "기타"])
        amount = st.number_input("금액 (원)", min_value=0, step=1000)
        memo = st.text_input("메모")
        submitted = st.form_submit_button("저장하기")

        if submitted:
            new_data = pd.DataFrame([[date, category, amount, memo]], 
                                    columns=["날짜", "카테고리", "금액", "메모"])
            data = pd.concat([data, new_data], ignore_index=True)
            data.to_csv("assets_data.csv", index=False)
            st.success("저장 완료!")
            st.rerun()

# 4. 자산 현황 요약
if not data.empty:
    total_amount = data['금액'].sum()
    st.metric(label="총 자산", value=f"{total_amount:,.0f} 원")

    # 5. 시각화 (모바일에서 보기 좋은 파이 차트)
    st.subheader("📊 자산 비중")
    fig = px.pie(data, values='금액', names='카테고리', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

    # 6. 상세 내역 확인
    st.subheader("📜 최근 내역")
    st.dataframe(data.sort_values(by="날짜", ascending=False), use_container_width=True)
else:
    st.info("데이터를 먼저 입력해주세요.")
