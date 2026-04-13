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

# ------------------- 시트(탭) 리스트 불러오기 함수 -------------------
@st.cache_data(ttl=300)
def get_worksheet_list():
    """구글 시트의 모든 탭(워크시트) 이름 리스트 반환"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # 내부 gspread client 접근
        client = conn._client  # 또는 conn.client (버전에 따라 다를 수 있음)
        spreadsheet = client.open_by_url(SHEET_URL)   # 또는 open_by_key(ID)
        worksheets = spreadsheet.worksheets()
        sheet_names = [ws.title for ws in worksheets]
        return sheet_names
    except Exception as e:
        st.error(f"시트 리스트 불러오기 실패: {e}")
        return []

# ------------------- 데이터 새로고침 버튼 -------------------
if st.button("🔄 전체 데이터 새로고침", type="secondary", use_container_width=True):
    st.cache_data.clear()
    st.success("캐시 초기화 완료 → 앱을 새로 불러옵니다.")
    st.rerun()

# ------------------- 시트 리스트 표시 -------------------
st.subheader("📋 구글 시트에 존재하는 탭 목록")

sheet_list = get_worksheet_list()

if sheet_list:
    st.success(f"총 {len(sheet_list)}개의 탭을 찾았습니다.")
    st.write("**탭 이름 목록:**")
    for name in sheet_list:
        st.code(name, language=None)
    
    # 자동으로 account / stock 후보 추천
    st.info("아래 입력창에 위 목록 중 정확한 탭 이름을 복사해서 사용하세요.")
else:
    st.error("시트 리스트를 불러올 수 없습니다. 시트 공유 설정을 다시 확인해주세요.")

# ------------------- 특정 시트 불러오기 테스트 -------------------
st.divider()
st.subheader("📥 특정 탭 데이터 불러오기 테스트")

col_a, col_s = st.columns(2)

with col_a:
    acc_name = st.text_input("Account 탭 이름", value="account" if "account" in [s.lower() for s in sheet_list] else sheet_list[0] if sheet_list else "")
    if st.button("Account 시트 불러오기", use_container_width=True):
        if acc_name:
            df_acc = load_gsheet_data(acc_name)   # 아래에 정의된 함수 사용
            if not df_acc.empty:
                st.dataframe(df_acc, use_container_width=True)

with col_s:
    stock_name = st.text_input("Stock 탭 이름", value="stock" if "stock" in [s.lower() for s in sheet_list] else sheet_list[0] if sheet_list else "")
    if st.button("Stock 시트 불러오기", use_container_width=True):
        if stock_name:
            df_stock = load_gsheet_data(stock_name)
            if not df_stock.empty:
                st.dataframe(df_stock, use_container_width=True)

# ------------------- 기존 load_gsheet_data 함수 (개선 버전) -------------------
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

# 분석 시작 버튼 (나중에 df_acc, df_stock이 제대로 로드되면 활성화)
run_analysis = st.button("🚀 분석 시작", type="primary", use_container_width=True)
