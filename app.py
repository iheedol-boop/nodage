import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.express as px
import os
import libsql
from dotenv import load_dotenv


# 페이지 설정
st.set_page_config(layout="wide")

st.title("🚀 대시보드")

# ====================== 환경변수  ======================
# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
url = os.getenv("TURSO_DATABASE_URL")
auth_token = os.getenv("TURSO_AUTH_TOKEN")
if not url or not auth_token:
    st.error("❌ TURSO_DATABASE_URL 또는 TURSO_AUTH_TOKEN이 .env 파일에 설정되지 않았습니다.")
    st.stop()
    
# ====================== DB 연결  ======================
# Embedded Replica 연결
conn = libsql.connect(
    "app.db",           # 로컬 SQLite 파일
    sync_url=url,
    auth_token=auth_token
)
conn.sync()             # remote → local 동기화

# ====================== 테이블 생성 (없으면 자동 생성) ======================
conn.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        "계좌명" TEXT UNIQUE NOT NULL,
        "총 투자원금" INTEGER DEFAULT 0,
        "예수금" INTEGER DEFAULT 0
    )
""")

conn.execute("""
    CREATE TABLE IF NOT EXISTS holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        "계좌명" TEXT NOT NULL,
        "종목코드" TEXT NOT NULL,
        "보유수량" INTEGER DEFAULT 0
    )
""")

# ====================== DB → DataFrame 로드 ======================
def load_accounts():
    rows = conn.execute('SELECT "계좌명", "총 투자원금", "예수금" FROM accounts').fetchall()
    if not rows:
        return pd.DataFrame(columns=["계좌명", "총 투자원금", "예수금"])
    return pd.DataFrame(rows, columns=["계좌명", "총 투자원금", "예수금"])

def load_holdings():
    rows = conn.execute('SELECT "계좌명", "종목코드", "보유수량" FROM holdings').fetchall()
    if not rows:
        return pd.DataFrame(columns=["계좌명", "종목코드", "보유수량"])
    df = pd.DataFrame(rows, columns=["계좌명", "종목코드", "보유수량"])
    df['종목코드'] = df['종목코드'].astype(str).str.zfill(6)
    return df


# 상단 탭 생성
tab1, tab2, tab3 = st.tabs(["홈", "분석 결과", "설정"])

with tab1:
    st.header("Home")
    st.write("여기는 메인 탭입니다.")

with tab2:
    st.header("Analysis")
    # 종목 리스트 캐시
    @st.cache_data(ttl=3600)
    def get_stock_list():
        stocks = fdr.StockListing('KRX')[['Code', 'Name']]
        etfs = fdr.StockListing('ETF/KR')[['Symbol', 'Name']].rename(columns={'Symbol': 'Code'})
        return pd.concat([stocks, etfs], ignore_index=True)
    
    all_listing = get_stock_list()
    
    # ====================== 조회 섹션 ======================
    with st.expander("💳 1. 계좌 정보 조회", expanded=False): # 보기 편하도록 기본 접음
        df_acc = load_accounts()
        st.dataframe(
            df_acc,
            use_container_width=True,
            hide_index=True  # 인덱스 번호를 숨기면 더 깔끔합니다
        )
    
    with st.expander("📈 2. 보유 종목 조회", expanded=False):
        df_stock = load_holdings()
        st.dataframe(
            df_stock,
            use_container_width=True,
            hide_index=True
        )
    
    run_analysis = st.button("🚀 분석 시작", type="primary", use_container_width=True)

    # 다른 파일의 함수를 불러와서 넣을 수도 있습니다.
    st.info("차트나 데이터를 여기에 띄웁니다.")

with tab3:
    st.header("Settings")
    st.write("환경 설정 화면입니다.")
