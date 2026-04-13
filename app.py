import streamlit as st
import sys
import os

# UTF-8 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import FinanceDataReader as fdr
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="자산 관리", layout="wide")
st.title("📊 구글 시트 연동 자산 관리")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1T5DHiuhiYdnoLMKi1fzAQXEPfbvADKr2FnyiQLlHgd8"

# ------------------- 데이터 새로고침 -------------------
if st.button("🔄 전체 데이터 새로고침", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.success("✅ 캐시 초기화 완료")
    st.rerun()

# ------------------- 탭 이름 수동 입력 (가장 안정적) -------------------
st.subheader("📋 탭 이름 직접 입력")

col1, col2 = st.columns(2)

with col1:
    account_tab = st.text_input(
        "Account 탭 이름 입력",
        value="Sheet1",   # ← 여기서 기본값을 당신 시트의 실제 탭 이름으로 바꾸세요
        help="구글 시트 하단에 있는 탭 이름을 정확히 입력하세요 (대소문자 구분)"
    )

with col2:
    stock_tab = st.text_input(
        "Stock 탭 이름 입력",
        value="Sheet1",
        help="구글 시트 하단에 있는 탭 이름을 정확히 입력하세요"
    )

# ------------------- 데이터 로드 함수 -------------------
@st.cache_data(ttl=300)
def load_gsheet_data(worksheet_name: str):
    if not worksheet_name:
        st.warning("탭 이름을 입력해주세요.")
        return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name)
        data = data.fillna('').astype(str)
        st.success(f"✅ '{worksheet_name}' 로드 완료 ({len(data)} 행)")
        return data
    except Exception as e:
        st.error(f"❌ '{worksheet_name}' 불러오기 실패: {str(e)}")
        st.info("💡 구글 시트 공유 설정이 '링크가 있는 모든 사용자'로 되어 있는지 확인하세요.")
        return pd.DataFrame()

# ------------------- 불러오기 버튼 -------------------
col_a, col_s = st.columns(2)

with col_a:
    if st.button("📋 Account 시트 불러오기", use_container_width=True) and account_tab:
        df_acc = load_gsheet_data(account_tab)
        if not df_acc.empty:
            st.dataframe(df_acc, use_container_width=True)

with col_s:
    if st.button("📋 Stock 시트 불러오기", use_container_width=True) and stock_tab:
        df_stock = load_gsheet_data(stock_tab)
        if not df_stock.empty:
            st.dataframe(df_stock, use_container_width=True)

# ------------------- 분석 시작 -------------------
if st.button("🚀 분석 시작", type="primary", use_container_width=True):
    st.info("분석을 시작합니다. (여기에 이전 분석 코드 붙여넣기)")
