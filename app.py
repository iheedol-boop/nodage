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

# ------------------- 개선된 로드 함수 + 디버깅 -------------------
def load_gsheet_data(worksheet_name):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        data = conn.read(
            spreadsheet=SHEET_URL,
            worksheet=worksheet_name,
            ttl=60
        )
        data = data.fillna('').astype(str)
        st.success(f"✅ '{worksheet_name}' 시트 로드 성공 ({len(data)} 행)")
        return data
    except Exception as e:
        st.error(f"❌ '{worksheet_name}' 시트 불러오기 실패: {str(e)}")
        return pd.DataFrame()

# 데이터 새로고침 버튼
if st.button("🔄 데이터 새로고침", type="secondary"):
    st.cache_data.clear()
    st.rerun()

# ------------------- 실제 탭 이름 테스트 -------------------
st.subheader("🔍 시트 로드 테스트")

# 사용자가 직접 탭 이름을 입력할 수 있게 임시 입력창 추가
worksheet_account = st.text_input("Account 시트 이름", value="account", help="구글 시트 하단 탭 이름을 정확히 입력하세요")
worksheet_stock = st.text_input("Stock 시트 이름", value="stock", help="구글 시트 하단 탭 이름을 정확히 입력하세요")

col1, col2 = st.columns(2)

with col1:
    if st.button("📋 Account 시트 불러오기"):
        df_acc = load_gsheet_data(worksheet_account)
        if not df_acc.empty:
            st.dataframe(df_acc)

with col2:
    if st.button("📋 Stock 시트 불러오기"):
        df_stock = load_gsheet_data(worksheet_stock)
        if not df_stock.empty:
            st.dataframe(df_stock)

# ------------------- 기존 분석 버튼 (시트 로드 성공 시에만 활성화) -------------------
run_analysis = st.button("🚀 분석 시작", type="primary", disabled=True)  # 일단 disabled

st.info("👆 먼저 위에서 **Account 시트 이름**과 **Stock 시트 이름**을 정확히 입력하고 불러오기를 테스트해보세요.\n\n시트 하단 탭 이름을 그대로 복사해서 입력하는 것을 추천합니다.")
