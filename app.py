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


