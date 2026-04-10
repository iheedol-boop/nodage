import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.express as px
import os

# 파일 저장 경로 설정
ACC_FILE = "account_data.csv"
STOCK_FILE = "stock_data.csv"

st.set_page_config(page_title="자산 관리 매니저", layout="wide")
st.title("💰 계좌별 통합 수익률 관리 (로컬 저장형)")

# --- [기능 1] 데이터 로드/저장 함수 ---
def load_data(file_path, default_data):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame(default_data)

def save_data(df, file_path):
    df.to_csv(file_path, index=False, encoding='utf-8-sig')

# --- [기능 2] 기초 데이터 준비 ---
@st.cache_data
def get_stock_list():
    stocks = fdr.StockListing('KRX')[['Code', 'Name']]
    etfs = fdr.StockListing('ETF/KR')[['Symbol', 'Name']].rename(columns={'Symbol': 'Code'})
    return pd.concat([stocks, etfs], ignore_index=True)

all_listing = get_stock_list()

# --- [기능 3] 메인 화면 UI ---

# 1. 계좌 정보 설정
st.subheader("1. 계좌 정보 설정")
default_acc = {"계좌명": ["주식 일반", "ISA계좌"], "총 투자원금": [10000000, 20000000], "예수금": [500000, 1500000]}
df_acc = load_data(ACC_FILE, default_acc)

# 데이터 에디터 (수정 즉시 반영)
edited_acc = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True, key="acc_editor")

# 2. 보유 종목 입력
st.subheader("2. 보유 종목 입력")
default_stock = {"계좌명": ["주식 일반", "주식 일반", "ISA계좌"], "종목코드": ["005930", "000660", "453810"], "보유수량": [50, 10, 100]}
df_stock = load_data(STOCK_FILE, default_stock)

edited_stock = st.data_editor(df_stock, num_rows="dynamic", use_container_width=True, key="stock_editor")

# --- [기능 4] 저장 및 분석 실행 ---
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("💾 데이터 저장하기", use_container_width=True):
        save_data(edited_acc, ACC_FILE)
        save_data(edited_stock, STOCK_FILE)
        st.success("파일 저장 완료!")

with col2:
    run_analysis = st.button("🚀 통합 자산 분석 시작", type="primary", use_container_width=True)

if run_analysis:
    with st.spinner("최신 시세 반영 중..."):
        # 종목 정보 업데이트 로직
        current_prices = []
        names = []
        for code in edited_stock["종목코드"]:
            try:
                name_match = all_listing[all_listing['Code'] == code]['Name']
                name = name_match.values[0] if not name_match.empty else "미등록종목"
                # 시세 조회 (최근 10일 데이터 중 마지막 값)
                price = fdr.DataReader(code).iloc[-1]['Close']
                names.append(name)
                current_prices.append(int(price))
            except:
                names.append("코드확인요망")
                current_prices.append(0)
        
        edited_stock["종목명"] = names
        edited_stock["현재가"] = current_prices
        edited_stock["평가금액"] = edited_stock["보유수량"] * edited_stock["현재가"]

        # 계좌 요약 계산
        acc_stock_sum = edited_stock.groupby("계좌명")["평가금액"].sum().reset_index()
        final_df = pd.merge(edited_acc, acc_stock_sum, on="계좌명", how="left").fillna(0)
        
        final_df["총자산"] = final_df["평가금액"] + final_df["예수금"]
        final_df["수익률(%)"] = ((final_df["총자산"] / final_df["총 투자원금"] - 1) * 100).round(2)

        # 결과 시각화 (기존 동일)
        st.divider()
        met_cols = st.columns(len(final_df))
        for i, row in final_df.iterrows():
            met_cols[i].metric(label=f"📍 {row['계좌명']}", value=f"{int(row['총자산']):,}원", delta=f"{row['수익률(%)']}%")

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(final_df, values='총자산', names='계좌명', title='계좌별 비중', hole=0.4), use_container_width=True)
        with c2:
            st.plotly_chart(px.sunburst(edited_stock, path=['계좌명', '종목명'], values='평가금액', title='상세 종목 구성'), use_container_width=True)

        st.subheader("📋 상세 현황 요약")
        st.dataframe(final_df.style.format({"총 투자원금": "{:,}", "예수금": "{:,}", "평가금액": "{:,}", "총자산": "{:,}"}), use_container_width=True)
