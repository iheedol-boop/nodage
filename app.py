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
    """구글 시트 데이터 로드 (한글 인코딩 문제 해결 버전)"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 한글 깨짐 방지를 위한 옵션 추가
        data = conn.read(
            spreadsheet=SHEET_URL, 
            worksheet=worksheet_name,
            # usecols=None,          # 필요시 컬럼 제한
            # dtype=str              # 모든 컬럼을 문자열로 읽기 (선택)
        )
        
        # 데이터프레임에 한글이 제대로 들어왔는지 확인
        data = data.astype(str).replace('nan', '')  # NaN을 빈 문자열로
        
        st.success(f"✅ '{worksheet_name}' 시트 로드 완료")
        return data
        
    except Exception as e:
        st.error(f"❌ '{worksheet_name}' 시트 불러오기 실패: {str(e)}")
        # 최소한의 빈 데이터프레임 반환 (앱이 완전히 멈추지 않도록)
        return pd.DataFrame()

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


