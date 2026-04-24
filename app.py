import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.express as px
import os
import libsql
from dotenv import load_dotenv

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


# ====================== Streamlit UI ======================
st.set_page_config(page_title="자산 관리", layout="wide")
st.title("💰 자산 ")

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
        #use_container_width=True,
        hide_index=True  # 인덱스 번호를 숨기면 더 깔끔합니다
    )

with st.expander("📈 2. 보유 종목 조회", expanded=False):
    df_stock = load_holdings()
    st.dataframe(
        df_stock,
        #use_container_width=True,
        hide_index=True
    )

run_analysis = st.button("🚀 분석 시작", type="primary" 
                         #use_container_width=True
                        )

# ====================== 분석 로직 ======================
if run_analysis:
    with st.spinner("시세 및 변동 정보 로딩 중..."):
        # 분석용 복사본 생성 
        analysis_stock = df_stock.copy()

        unique_codes = analysis_stock["종목코드"].unique()
        stock_info_dict = {}

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

        # 분석용 데이터프레임에 정보 매핑
        analysis_stock["종목명"] = analysis_stock["종목코드"].map(lambda x: stock_info_dict.get(x, {}).get("종목명", "미등록"))
        analysis_stock["현재가"] = analysis_stock["종목코드"].map(lambda x: stock_info_dict.get(x, {}).get("현재가", 0))
        analysis_stock["전일가"] = analysis_stock["종목코드"].map(lambda x: stock_info_dict.get(x, {}).get("전일가", 0))
        analysis_stock["변동률(%)"] = analysis_stock["종목코드"].map(lambda x: stock_info_dict.get(x, {}).get("변동률(%)", 0))
        analysis_stock["평가금액"] = analysis_stock["보유수량"] * analysis_stock["현재가"]
       


        # ====================== 종목별 실시간 변동 ======================
        st.subheader("📊 종목별 실시간 변동 (통합)")
        # 1. 상승률 기준 내림차순 정렬 (이미 잘 작성하셨습니다)
        unique_stock_display = analysis_stock.groupby("종목코드").agg({
            '종목명': 'first',
            '현재가': 'first',
            '전일가': 'first',
            '변동률(%)': 'first',
            '보유수량': 'sum',
            '평가금액': 'sum'
        }).reset_index().sort_values(by="변동률(%)", ascending=False)
        
        # 2. 정렬된 순서대로 인덱스를 재부여 (idx % 4 계산을 위해 필수)
        unique_stock_display = unique_stock_display.reset_index(drop=True)
        
        # 3. 화면 출력
        stock_cols = st.columns(4)
        for idx, row in unique_stock_display.iterrows():
            with stock_cols[idx % 4]:
                change_amt = int(row['현재가'] - row['전일가'])
                st.metric(
                    label=row['종목명'],
                    value=f"{int(row['현재가']):,}원",
                    delta=f"{change_amt:+,}원 ({row['변동률(%)']:+.2f}%)"
                )

        # ====================== 계좌 및 종목별 계층 분석 ======================
        st.divider()
        st.subheader("🏦 계좌 및 종목별 계층 분석")

        acc_stock_sum = analysis_stock.groupby("계좌명")["평가금액"].sum().reset_index()
        final_df = pd.merge(df_acc, acc_stock_sum, on="계좌명", how="left").fillna(0)
        final_df["총자산"] = final_df["평가금액"] + final_df["예수금"]

        final_df["수익률(%)"] = final_df.apply(
            lambda x: round(((x["총자산"] / x["총 투자원금"]) - 1) * 100, 2) if x["총 투자원금"] > 0 else 0, axis=1
        )

        col1, col2 = st.columns(2)
        with col1:
            for _, row in final_df.sort_values("총자산", ascending=False).iterrows():
                st.metric(
                    label=f"📂 {row['계좌명']}",
                    value=f"{int(row['총자산']):,}원",
                    delta=f"{row['수익률(%)']}%"
                )

        with col2:
            tree_data = analysis_stock[['계좌명', '종목명', '평가금액']].rename(columns={'종목명': '항목', '평가금액': '금액'})
            cash_data = final_df[['계좌명', '예수금']].rename(columns={'예수금': '금액'})
            cash_data['항목'] = "💰 예수금"
            hierarchical_df = pd.concat([tree_data, cash_data], ignore_index=True)
            hierarchical_df = hierarchical_df[hierarchical_df['금액'] > 0]

            fig_tree = px.treemap(
                hierarchical_df,
                path=[px.Constant("전체 자산"), '계좌명', '항목'],
                values='금액',
                color='계좌명',
                color_discrete_sequence=px.colors.qualitative.Pastel,
                title="📊 계층적 자산 구성"
            )
            fig_tree.update_traces(textinfo="label+value+percent parent")
            fig_tree.update_layout(margin=dict(t=30, b=10, l=10, r=10), height=500)
            st.plotly_chart(fig_tree
                            #, use_container_width=True
                           )

        # ====================== 종목별 Sunburst ======================
        st.divider()
        c3, c4 = st.columns(2)
        with c3:
            fig_sun = px.sunburst(
                hierarchical_df, # 위에서 만든 예수금 포함 데이터 활용
                path=['항목', '계좌명'],
                values='금액',
                title='🏦 항목별 자산 구성 (종목/예수금 > 계좌)',
                color='항목',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_sun.update_traces(textinfo="label+percent root", insidetextorientation='radial')
            fig_sun.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=500)
            st.plotly_chart(fig_sun
                            #, use_container_width=True
                           )
        with c4:  
            fig_sun_acc = px.sunburst(
                hierarchical_df, # 위에서 만든 예수금 포함 데이터 활용
                path=['계좌명', '항목'],
                values='금액',
                title='🏦 계좌별 자산 구성 (계좌 > 종목/예수금)',
                color='항목',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_sun_acc.update_traces(textinfo="label+percent parent")
            fig_sun_acc.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=500)
            st.plotly_chart(fig_sun_acc
                            #, use_container_width=True
                           )
            
    # 연결 종료
    conn.close()
