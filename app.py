import streamlit as st
import sys
import os

# UTF-8 설정 (한글 문제 방지)
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

# ------------------- 시트(탭) 리스트 불러오기 -------------------
@st.cache_data(ttl=300)
def get_worksheet_list():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        worksheets = conn.worksheets()
        sheet_names = [ws.title for ws in worksheets]
        return sheet_names
    except Exception as e:
        st.error(f"시트 리스트 불러오기 실패: {e}")
        return []

# ------------------- 데이터 새로고침 버튼 -------------------
if st.button("🔄 전체 새로고침", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.success("✅ 캐시 초기화 완료")
    st.rerun()

# ------------------- 시트 리스트 표시 -------------------
st.subheader("📋 구글 시트 탭 목록")

sheet_list = get_worksheet_list()

if sheet_list:
    st.success(f"✅ 총 {len(sheet_list)}개의 탭을 찾았습니다.")
    for i, name in enumerate(sheet_list, 1):
        st.code(f"{i}. {name}", language=None)
else:
    st.warning("탭 목록을 불러오지 못했습니다.")

# ------------------- 특정 탭 데이터 불러오기 -------------------
st.divider()
st.subheader("📥 탭 데이터 불러오기 테스트")

col1, col2 = st.columns(2)

with col1:
    account_tab = st.selectbox("Account 탭 선택", options=sheet_list if sheet_list else [""], key="acc")
    if st.button("📋 Account 시트 불러오기", use_container_width=True) and account_tab:
        df_acc = load_gsheet_data(account_tab)
        if not df_acc.empty:
            st.dataframe(df_acc, use_container_width=True)

with col2:
    stock_tab = st.selectbox("Stock 탭 선택", options=sheet_list if sheet_list else [""], key="stock")
    if st.button("📋 Stock 시트 불러오기", use_container_width=True) and stock_tab:
        df_stock = load_gsheet_data(stock_tab)
        if not df_stock.empty:
            st.dataframe(df_stock, use_container_width=True)

# ------------------- 데이터 로드 함수 (f-string 오류 수정됨) -------------------
@st.cache_data(ttl=300)
def load_gsheet_data(worksheet_name: str):
    if not worksheet_name:
        return pd.DataFrame()
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        data = conn.read(spreadsheet=SHEET_URL, worksheet=worksheet_name)
        data = data.fillna('').astype(str)
        st.success(f"✅ '{worksheet_name}' 로드 완료 ({len(data)} 행)")
        return data
    except Exception as e:
        st.error(f"❌ '{worksheet_name}' 불러오기 실패: {str(e)}")
        return pd.DataFrame()

# ------------------- 분석 시작 버튼 -------------------
if st.button("🚀 분석 시작", type="primary", use_container_width=True):
    st.info("✅ 분석이 시작되었습니다. (여기에 기존 분석 코드를 붙여넣으시면 됩니다)")
    # 여기에 이전에 제공했던 종목별 변동, 트리맵, sunburst 코드 넣으세요
