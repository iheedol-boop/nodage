import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.express as px
import os

# 파일 저장 및 로드 설정 (이전과 동일)
ACC_FILE = "account_data.csv"
STOCK_FILE = "stock_data.csv"

st.set_page_config(page_title="자산 관리", layout="centered") 
st.title("💰 자산 관리 매니저")

def load_data(file_path, default_data):
    if os.path.exists(file_path):
        if "stock" in file_path:
            return pd.read_csv(file_path, dtype={'종목코드': str})
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

# --- [입력 섹션: 접힌 상태] ---
with st.expander("💳 1. 계좌 정보 설정", expanded=False):
    default_acc = {"계좌명": ["주식 일반", "ISA계좌"], "총 투자원금": [10000000, 20000000], "예수금": [500000, 1500000]}
    df_acc = load_data(ACC_FILE, default_acc)
    edited_acc = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True, key="acc_edit")

with st.expander("📈 2. 보유 종목 입력", expanded=False):
    default_stock = {"계좌명": ["주식 일반", "주식 일반", "ISA계좌"], "종목코드": ["005930", "000660", "453810"], "보유수량": [50, 10, 100]}
    df_stock = load_data(STOCK_FILE, default_stock)
    df_stock['종목코드'] = df_stock['종목코드'].astype(str).str.zfill(6)
    edited_stock = st.data_editor(df_stock, num_rows="dynamic", use_container_width=True, key="stock_edit")

c1, c2 = st.columns(2)
with c1:
    if st.button("💾 데이터 저장", use_container_width=True):
        if "종목코드" in edited_stock.columns:
            edited_stock["종목코드"] = edited_stock["종목코드"].astype(str).str.zfill(6)
        save_data(edited_acc, ACC_FILE)
        save_data(edited_stock, STOCK_FILE)
        st.success("저장 완료!")
with c2:
    run_analysis = st.button("🚀 분석 시작", type="primary", use_container_width=True)

# --- [분석 및 시각화] ---
if run_analysis:
    with st.spinner("시세 로딩 중..."):
        edited_stock["종목코드"] = edited_stock["종목코드"].astype(str).str.zfill(6)
        
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

        # [개선] 종목 구성 차트를 위해 평가금액 기준 내림차순 정렬
        # 이렇게 하면 차트에서 비중이 큰 종목이 우선적으로 배치됩니다.
        edited_stock = edited_stock.sort_values(by="평가금액", ascending=False)

        acc_stock_sum = edited_stock.groupby("계좌명")["평가금액"].sum().reset_index()
        final_df = pd.merge(edited_acc, acc_stock_sum, on="계좌명", how="left").fillna(0)
        final_df["총자산"] = final_df["평가금액"] + final_df["예수금"]
        
        # 계좌 비중 차트를 위해 총자산 기준 정렬
        final_df = final_df.sort_values(by="총자산", ascending=False)
        final_df["수익률(%)"] = ((final_df["총자산"] / final_df["총 투자원금"] - 1) * 100).round(2)

        st.divider()
        
        # 지표 표시
        for i, row in final_df.iterrows():
            st.metric(label=f"📍 {row['계좌명']}", value=f"{int(row['총자산']):,}원", delta=f"{row['수익률(%)']}%")
        
        # 1. 계좌별 비중 (총자산 기준 정렬됨)
        st.plotly_chart(px.pie(final_df, values='총자산', names='계좌명', 
                               title='💳 계좌별 자산 비중', hole=0.4), use_container_width=True)
        
        # 2. 상세 종목 구성 (평가금액 기준 정렬됨)
        fig_sun = px.sunburst(
            edited_stock, 
            path=['계좌명', '종목명'], 
            values='평가금액', 
            title='🔍 상세 종목 구성 (비중 순)',
            color='평가금액',
            color_continuous_scale='Blues' # 비중이 높을수록 진한 파란색
        )
        # 차트 내부 텍스트에 비율(Percent parent) 표시 추가
        fig_sun.update_traces(textinfo="label+percent parent")
        st.plotly_chart(fig_sun, use_container_width=True)

        st.subheader("📋 상세 요약")
        st.dataframe(final_df.style.format({"총 투자원금": "{:,}", "예수금": "{:,}", "평가금액": "{:,}", "총자산": "{:,}"}), use_container_width=True)
