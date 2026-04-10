import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.express as px
import os

# 파일 저장 경로
ACC_FILE = "account_data.csv"
STOCK_FILE = "stock_data.csv"

# [모바일 최적화 1] 레이아웃을 'centered'로 설정하여 모바일 가독성 확보
st.set_page_config(page_title="자산 관리", layout="centered") 

st.title("💰 자산 관리 매니저")

def load_data(file_path, default_data):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame(default_data)

def save_data(df, file_path):
    df.to_csv(file_path, index=False, encoding='utf-8-sig')

@st.cache_data
def get_stock_list():
    stocks = fdr.StockListing('KRX')[['Code', 'Name']]
    etfs = fdr.StockListing('ETF/KR')[['Symbol', 'Name']].rename(columns={'Symbol': 'Code'})
    return pd.concat([stocks, etfs], ignore_index=True)

all_listing = get_stock_list()

# --- [입력 섹션] ---
with st.expander("💳 1. 계좌 정보 설정", expanded=True):
    default_acc = {"계좌명": ["주식 일반", "ISA계좌"], "총 투자원금": [10000000, 20000000], "예수금": [500000, 1500000]}
    df_acc = load_data(ACC_FILE, default_acc)
    edited_acc = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True, key="acc_edit")

with st.expander("📈 2. 보유 종목 입력", expanded=True):
    default_stock = {"계좌명": ["주식 일반", "주식 일반", "ISA계좌"], "종목코드": ["005930", "000660", "453810"], "보유수량": [50, 10, 100]}
    df_stock = load_data(STOCK_FILE, default_stock)
    edited_stock = st.data_editor(df_stock, num_rows="dynamic", use_container_width=True, key="stock_edit")

# 버튼 배치 (모바일은 세로 배치가 기본이나, 버튼 2개는 나란히)
c1, c2 = st.columns(2)
with c1:
    if st.button("💾 데이터 저장", use_container_width=True):
        save_data(edited_acc, ACC_FILE)
        save_data(edited_stock, STOCK_FILE)
        st.success("저장됨!")
with c2:
    run_analysis = st.button("🚀 분석 시작", type="primary", use_container_width=True)

# --- [분석 섹션] ---
if run_analysis:
    with st.spinner("시세 로딩 중..."):
        current_prices = []
        names = []
        for code in edited_stock["종목코드"]:
            try:
                name_match = all_listing[all_listing['Code'] == code]['Name']
                name = name_match.values[0] if not name_match.empty else "미등록"
                price = fdr.DataReader(code).iloc[-1]['Close']
                names.append(name)
                current_prices.append(int(price))
            except:
                names.append("코드확인")
                current_prices.append(0)
        
        edited_stock["종목명"] = names
        edited_stock["현재가"] = current_prices
        edited_stock["평가금액"] = edited_stock["보유수량"] * edited_stock["현재가"]

        acc_stock_sum = edited_stock.groupby("계좌명")["평가금액"].sum().reset_index()
        final_df = pd.merge(edited_acc, acc_stock_sum, on="계좌명", how="left").fillna(0)
        final_df["총자산"] = final_df["평가금액"] + final_df["예수금"]
        final_df["수익률(%)"] = ((final_df["총자산"] / final_df["총 투자원금"] - 1) * 100).round(2)

        st.divider()

        # [모바일 최적화 2] 지표(Metric)를 세로로 한 줄씩 표시
        for i, row in final_df.iterrows():
            st.metric(
                label=f"📍 {row['계좌명']}", 
                value=f"{int(row['총자산']):,}원", 
                delta=f"{row['수익률(%)']}%"
            )

        # [모바일 최적화 3] 차트를 좌우가 아닌 위아래로 배치
        st.plotly_chart(px.pie(final_df, values='총자산', names='계좌명', title='💳 계좌별 비중', hole=0.4), use_container_width=True)
        
        st.plotly_chart(px.sunburst(edited_stock, path=['계좌명', '종목명'], values='평가금액', title='🔍 상세 종목 구성'), use_container_width=True)

        # [모바일 최적화 4] 표가 너무 넓을 경우 가로 스크롤 허용
        st.subheader("📋 상세 요약")
        st.dataframe(final_df.style.format({"총 투자원금": "{:,}", "예수금": "{:,}", "평가금액": "{:,}", "총자산": "{:,}"}), use_container_width=True)
