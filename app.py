import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.express as px
import os
import libsql
from dotenv import load_dotenv
from datetime import datetime

st.markdown("""
<style>
/* 라벨(종목명) 크기 조절 */
[data-testid="stMetricLabel"] {
    font-size: 0.8rem !important;
}
/* 값(가격) 크기 조절 */
[data-testid="stMetricValue"] {
    font-size: 1.2rem !important;
}
/* 변동폭(delta) 크기 조절 */
[data-testid="stMetricDelta"] {
    font-size: 0.7rem !important;
}
</style>
""", unsafe_allow_html=True)


# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
url = os.getenv("TURSO_DATABASE_URL")
auth_token = os.getenv("TURSO_AUTH_TOKEN")
if not url or not auth_token:
    st.error("❌ TURSO_DATABASE_URL 또는 TURSO_AUTH_TOKEN이 .env 파일에 설정되지 않았습니다.")
    st.stop()
    
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

conn.execute("""
    CREATE TABLE IF NOT EXISTS deposit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        "계좌명" TEXT NOT NULL,
        "원금" INTEGER DEFAULT 0,
        "시작일" TEXT NOT NULL,
        "예금금리" TEXT NOT NULL
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

def load_deposit():
    rows = conn.execute('SELECT  "계좌명", "원금", "시작일", "예금금리" FROM deposit').fetchall()
    if not rows:
        return pd.DataFrame(columns=["계좌명", "원금", "시작일", "예금금리"])
    return pd.DataFrame(rows, columns=["계좌명", "원금", "시작일", "예금금리"])

def get_stock_list():
    stocks = fdr.StockListing('KRX')[['Code', 'Name']]
    etfs = fdr.StockListing('ETF/KR')[['Symbol', 'Name']].rename(columns={'Symbol': 'Code'})
    return pd.concat([stocks, etfs], ignore_index=True)
    
def calculate_deposit_value(row):
    """원금, 시작일, 금리를 바탕으로 오늘 기준 평가금액 계산"""
    try:
        start_date = pd.to_datetime(row['시작일'])
        today = datetime.now()
        days_passed = (today - start_date).days
        
        if days_passed < 0: days_passed = 0 # 미래 날짜 시작 대비
        
        # 단리 계산 (일할 계산: 원금 * 금리 * 경과일수 / 365)
        # 예금금리가 3.5%라면 0.035로 계산되도록 /100 처리
        interest = row['원금'] * (float(row['예금금리']) / 100) * (days_passed / 365)
        return int(row['원금'] + interest)
    except:
        return row['원금'] # 오류 시 원금 반환

def stock_deposit():
    all_listing = get_stock_list()
    df_holdings = load_holdings()
    analysis_holdings =df_holdings.copy()
    df_deposit = load_deposit()
    unique_codes = df_holdings["종목코드"].unique()
    stock_info_dict = {}

# ====================== 주식 평가 데이터 ====================== 
    for code in unique_codes:
        try:
            df = fdr.DataReader(code).tail(3)

            GOLD_ETF_CODE = "411060"
            GOLD_MULTIPLIER = 7.15
            
            if len(df) >= 2:
                current_price = int(round(df.iloc[-1]['Close']))
                prev_close = int(round(df.iloc[-2]['Close']))
                
                # 금 ETF(ACE KRX금현물) 시세 조정
                if code == GOLD_ETF_CODE:
                    current_price = int(current_price * GOLD_MULTIPLIER)
                    prev_close = int(prev_close * GOLD_MULTIPLIER)
                
                # 등락률 계산 (분모가 0인 경우 대비)
                change_rate = round(((current_price - prev_close) / prev_close) * 100, 2) if prev_close != 0 else 0.0
            
            elif len(df) == 1:
                current_price = prev_close = int(round(df.iloc[-1]['Close']))
                if code == GOLD_ETF_CODE:
                    current_price = prev_close = int(current_price * GOLD_MULTIPLIER)
                change_rate = 0.0
            
            else:
                current_price = prev_close = 0
                change_rate = 0.0

            name_match = all_listing[all_listing['Code'] == code]['Name']
            name = name_match.values[0] if not name_match.empty else "미등록"

            stock_info_dict[code] = {
                "종목명": name,
                "현재가": current_price,
                "전일가": prev_close,
                "변동률(%)": change_rate
            }
        except Exception as e:
            st.warning(f"{code} 데이터 로드 실패: {e}")
            stock_info_dict[code] = {"종목명": "오류", "현재가": 0, "전일가": 0, "변동률(%)": 0}

    analysis_holdings["종목명"] = analysis_holdings["종목코드"].map(lambda x: stock_info_dict.get(x, {}).get("종목명", "미등록"))
    analysis_holdings["현재가"] = analysis_holdings["종목코드"].map(lambda x: stock_info_dict.get(x, {}).get("현재가", 0))
    analysis_holdings["전일가"] = analysis_holdings["종목코드"].map(lambda x: stock_info_dict.get(x, {}).get("전일가", 0))
    analysis_holdings["변동률(%)"] = analysis_holdings["종목코드"].map(lambda x: stock_info_dict.get(x, {}).get("변동률(%)", 0))
    analysis_holdings["평가금액"] = analysis_holdings["보유수량"] * analysis_holdings["현재가"]

# ====================== 예금 데이터 ====================== 
    df_deposit['종목명'] = '정기예금'
    df_deposit['현재가'] = df_deposit['원금']
    df_deposit['전일가'] = df_deposit['원금']
    df_deposit['변동률(%)'] = 0
    df_deposit['평가금액'] = df_deposit.apply(calculate_deposit_value, axis=1)
    
# ====================== 주식과 예금 총합 ====================== 
    stock_summary = analysis_holdings[['계좌명', '종목명', '현재가', '전일가', '평가금액', '변동률(%)']].copy()
    stock_summary['자산분류'] = '주식'
    deposit_summary = df_deposit[['계좌명', '종목명', '현재가', '전일가', '평가금액', '변동률(%)']].copy()
    deposit_summary['자산분류'] = '예금'
    stock_deposit = pd.concat([stock_summary, deposit_summary], ignore_index=True)

    return stock_deposit

# ====================== Streamlit UI ======================
st.set_page_config(page_title="자산 관리", layout="wide")
run_analysis = st.button("🚀 실행하기", type="primary", width="stretch")

# ====================== 분석 로직 ======================
if run_analysis:
    with st.spinner("시세 및 변동 정보 로딩 중..."):
        
        df_acc = load_accounts()
        stock_deposit = stock_deposit()

# ====================== 전체 자산 ======================
        st.markdown("📋 자산 현황")
        total_principal = df_acc["총 투자원금"].sum()
        total_cash = df_acc["예수금"].sum()
        total_stock_eval = stock_deposit["평가금액"].sum()
        total_asset = total_cash + total_stock_eval
        total_profit = total_asset - total_principal
        total_return_pct = (total_profit / total_principal * 100) if total_principal > 0 else 0
        st.metric(
                label="전체",
                value=f"{int(total_stock_eval):,}원",
                delta=f"{total_profit:+,}원 ({total_return_pct:+.2f}%)"
            )    
        
# ====================== 계좌별 자산 ====================== 
        acc_stock_sum = stock_deposit.groupby("계좌명")["평가금액"].sum().reset_index()
        final_df = pd.merge(df_acc, acc_stock_sum, on="계좌명", how="left").fillna(0)
        final_df["총자산"] = final_df["평가금액"] + final_df["예수금"]
        final_df["수익금액"] = final_df["총자산"] - final_df["총 투자원금"]
        final_df["수익률(%)"] = final_df.apply(
            lambda x: round(((x["총자산"] / x["총 투자원금"]) - 1) * 100, 2) if x["총 투자원금"] > 0 else 0, axis=1
        )
        for _, row in final_df.sort_values("수익률(%)", ascending=False).iterrows():
            st.metric(
                label=f"{row['계좌명']}",
                value=f"{int(row['총자산']):,}원",
                delta=f"{int(row['수익금액']):+,}원 ({row['수익률(%)']}%)"
            )
        st.divider()
     
# ====================== 종목별 실시간 변동 ======================
        st.markdown("📊 종목 시세 변동")

        unique_stock_display = stock_deposit[stock_deposit['종목명'] != '정기예금'].groupby("종목명").agg({
            '현재가': 'first',
            '전일가': 'first',
            '변동률(%)': 'first'
        }).reset_index().sort_values(by="변동률(%)", ascending=False)
        
        unique_stock_display = unique_stock_display.reset_index(drop=True)
        
        for idx, row in unique_stock_display.iterrows():
            change_amt = int(row['현재가'] - row['전일가'])
            
            st.metric(
                label=row['종목명'],
                value=f"{int(row['현재가']):,}원",
                delta=f"{change_amt:+,}원 ({row['변동률(%)']:+.2f}%)"
            )    
            
# ====================== 계좌 및 종목별 계층 분석 ======================
        st.divider()
        st.markdown("📊자산 분석")
        
        tree_data = stock_deposit[['계좌명', '종목명', '평가금액']].rename(columns={'종목명': '항목', '평가금액': '금액'})
        cash_data = final_df[['계좌명', '예수금']].rename(columns={'예수금': '금액'})
        cash_data['항목'] = "예수금"
        hierarchical_df = pd.concat([tree_data, cash_data], ignore_index=True)
        hierarchical_df = hierarchical_df[hierarchical_df['금액'] > 0]

        fig_sun = px.sunburst(
            hierarchical_df, # 위에서 만든 예수금 포함 데이터 활용
            path=['항목', '계좌명'],
            values='금액',
            title='종목별 구성',
            color='항목',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_sun.update_traces(textinfo="label+percent root", insidetextorientation='radial')
        fig_sun.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=500)
        st.plotly_chart(fig_sun)
           
        fig_sun_acc = px.sunburst(
            hierarchical_df, # 위에서 만든 예수금 포함 데이터 활용
            path=['계좌명', '항목'],
            values='금액',
            title='계좌별 구성',
            color='항목',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_sun_acc.update_traces(textinfo="label+percent parent")
        fig_sun_acc.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=500)
        st.plotly_chart(fig_sun_acc)
                
# 연결 종료
    conn.close()
