import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# ------------------- 설정 -------------------
st.set_page_config(page_title="자산 관리 (G-Sheet)", layout="wide")
st.title("📊 구글 시트 연동 자산 관리")

# 구글 시트 URL (본인 시트로 변경하세요)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1T5DHiuhiYdnoLMKi1fzAQXEPfbvADKr2FnyiQLlHgd8/edit?usp=sharing"

# ------------------- 데이터 로드 -------------------
@st.cache_data(ttl=600)
def load_gsheet_data(worksheet_name):
    conn = st.connection("gsheets", type=GSheetsConnection)
    data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name)
    return data

@st.cache_data
def get_stock_list():
    stocks = fdr.StockListing('KRX')[['Code', 'Name']]
    etfs = fdr.StockListing('ETF/KR')[['Symbol', 'Name']].rename(columns={'Symbol': 'Code'})
    return pd.concat([stocks, etfs], ignore_index=True)

# 기초 데이터 로드
all_listing = get_stock_list()

try:
    df_acc = load_gsheet_data("account")
    df_stock = load_gsheet_data("stock")
    st.success("✅ 구글 시트 데이터 로드 완료")
except Exception as e:
    st.error(f"❌ 데이터를 불러올 수 없습니다: {e}")
    st.stop()

# ------------------- 분석 시작 버튼 -------------------
run_analysis = st.button("🚀 분석 시작", type="primary", use_container_width=True)

# ------------------- 분석 실행 -------------------
if run_analysis:
    with st.spinner("시세 정보를 불러오는 중..."):
        # 종목코드 추출
        unique_codes = df_stock["종목코드"].unique()
        stock_info_dict = {}

        for code in unique_codes:
            try:
                df_price = fdr.DataReader(code).tail(2)
                
                if len(df_price) >= 2:
                    current_price = int(df_price.iloc[-1]['Close'])
                    prev_close = int(df_price.iloc[-2]['Close'])
                    change_rate = round(((current_price - prev_close) / prev_close) * 100, 2)
                else:
                    current_price = int(df_price.iloc[-1]['Close']) if not df_price.empty else 0
                    prev_close = current_price
                    change_rate = 0.0

                # 종목명 찾기
                name_match = all_listing[all_listing['Code'] == code]['Name']
                name = name_match.values[0] if not name_match.empty else "미등록 종목"

                stock_info_dict[code] = {
                    "종목명": name,
                    "현재가": current_price,
                    "전일가": prev_close,
                    "변동률(%)": change_rate
                }
            except Exception:
                stock_info_dict[code] = {
                    "종목명": "데이터 오류",
                    "현재가": 0,
                    "전일가": 0,
                    "변동률(%)": 0.0
                }

        # df_stock에 실시간 정보 매핑
        df_stock = df_stock.copy()  # 원본 보호
        df_stock["종목명"] = df_stock["종목코드"].map(lambda x: stock_info_dict[x]["종목명"])
        df_stock["현재가"] = df_stock["종목코드"].map(lambda x: stock_info_dict[x]["현재가"])
        df_stock["전일가"] = df_stock["종목코드"].map(lambda x: stock_info_dict[x]["전일가"])
        df_stock["변동률(%)"] = df_stock["종목코드"].map(lambda x: stock_info_dict[x]["변동률(%)"])
        df_stock["평가금액"] = df_stock["보유수량"] * df_stock["현재가"]

        # ------------------- 1. 종목별 실시간 변동 -------------------
        st.subheader("📊 종목별 실시간 변동")

        unique_stock_display = df_stock.groupby("종목코드").agg({
            '종목명': 'first',
            '현재가': 'first',
            '전일가': 'first',
            '변동률(%)': 'first',
            '보유수량': 'sum',
            '평가금액': 'sum'
        }).reset_index()

        unique_stock_display = unique_stock_display.sort_values(by="변동률(%)", ascending=False)

        # 4열 메트릭 표시
        cols = st.columns(4)
        for idx, row in unique_stock_display.iterrows():
            with cols[idx % 4]:
                change_amt = int(row['현재가'] - row['전일가'])
                st.metric(
                    label=row['종목명'],
                    value=f"{int(row['현재가']):,}원",
                    delta=f"{change_amt:+,}원 ({row['변동률(%)']:+.2f}%)"
                )

        #
