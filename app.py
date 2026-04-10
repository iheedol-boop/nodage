import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="자산 관리 매니저", layout="centered")
st.title("💰 계좌별 통합 수익률 관리")

# 1. 계좌별 원금 및 예수금 설정
st.subheader("1. 계좌 정보 설정")
acc_data = {
    "계좌명": ["주식 일반", "ISA계좌"],
    "총 투자원금": [10000000, 20000000], # 투입한 생돈
    "예수금": [500000, 1500000]          # 계좌 내 현금
}
df_acc = pd.DataFrame(acc_data)
edited_acc = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True, key="acc_editor")

# 2. 보유 종목 입력 (매수평균가 제외)
st.subheader("2. 보유 종목 입력")
stock_data = {
    "계좌명": ["주식 일반", "주식 일반", "ISA계좌"],
    "종목코드": ["005930", "000660", "453810"],
    "보유수량": [50, 10, 100]
}
df_stock = pd.DataFrame(stock_data)
edited_stock = st.data_editor(df_stock, num_rows="dynamic", use_container_width=True, key="stock_editor")

# 3. 분석 실행
if st.button("🚀 통합 자산 분석"):
    with st.spinner("최신 시세 반영 중..."):
        # 시장 데이터 통합 (주식 + ETF)
        stocks = fdr.StockListing('KRX')[['Code', 'Name']]
        etfs = fdr.StockListing('ETF/KR')[['Symbol', 'Name']].rename(columns={'Symbol': 'Code'})
        all_listing = pd.concat([stocks, etfs], ignore_index=True)

        # 종목별 현재가 및 평가금액 계산
        current_prices = []
        names = []
        for code in edited_stock["종목코드"]:
            try:
                name = all_listing[all_listing['Code'] == code]['Name'].values[0]
                price = fdr.DataReader(code).iloc[-1]['Close']
                names.append(name)
                current_prices.append(int(price))
            except:
                names.append("코드확인요망")
                current_prices.append(0)
        
        edited_stock["종목명"] = names
        edited_stock["현재가"] = current_prices
        edited_stock["평가금액"] = edited_stock["보유수량"] * edited_stock["현재가"]

        # 계좌별로 종목 평가금액 합산
        acc_stock_sum = edited_stock.groupby("계좌명")["평가금액"].sum().reset_index()
        
        # 계좌 정보와 합산 데이터 병합
        final_df = pd.merge(edited_acc, acc_stock_sum, on="계좌명", how="left").fillna(0)
        
        # 최종 계산 (예수금 포함)
        final_df["총자산"] = final_df["평가금액"] + final_df["예수금"]
        final_df["순손익"] = final_df["총자산"] - final_df["총 투자원금"]
        final_df["수익률(%)"] = ((final_df["총자산"] / final_df["총 투자원금"] - 1) * 100).round(2)

        # 4. 결과 대시보드
        st.divider()
        cols = st.columns(len(final_df))
        for i, row in final_df.iterrows():
            cols[i].metric(
                label=f"📍 {row['계좌명']}", 
                value=f"{int(row['총자산']):,}원", 
                delta=f"{row['수익률(%)']}% (전체)"
            )

        # 시각화
        col_left, col_right = st.columns(2)
        with col_left:
            fig_pie = px.pie(final_df, values='총자산', names='계좌명', title='계좌별 자산 비중', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_right:
            # 해당 계좌 내 종목 비중 (첫 번째 계좌 기준 예시)
            fig_stock = px.sunburst(edited_stock, path=['계좌명', '종목명'], values='평가금액', title='계좌 내 종목 구성')
            st.plotly_chart(fig_stock, use_container_width=True)

        st.subheader("📋 계좌별 상세 요약")
        st.table(final_df[['계좌명', '총 투자원금', '예수금', '평가금액', '총자산', '수익률(%)']].style.format({
            "총 투자원금": "{:,}", "예수금": "{:,}", "평가금액": "{:,}", "총자산": "{:,}"
        }))
