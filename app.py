import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.express as px
import os

# 파일 저장 경로
ACC_FILE = "account_data.csv"
STOCK_FILE = "stock_data.csv"

st.set_page_config(page_title="자산 관리", layout="centered") 
st.title("💰 자산 관리 매니저")

def load_data(file_path, default_data):
    if os.path.exists(file_path):
        if "stock" in file_path:
            return pd.read_csv(file_path, dtype={'종목코드': str})
        return pd.read_csv(file_path)
    return pd.DataFrame(default_data)

def save_data(df, file_path):
    df.to_csv(file_path, index=False, encoding='utf-8-sig')

@st.cache_data
def get_stock_list():
    stocks = fdr.StockListing('KRX')[['Code', 'Name']]
    etfs = fdr.StockListing('ETF/KR')[['Symbol', 'Name']].rename(columns={'Symbol': 'Code'})
    return pd.concat([stocks, etfs], ignore_index=True)

all_listing = get_stock_list()

# --- [입력 섹션: 접힌 상태] ---
with st.expander("💳 1. 계좌 정보 설정", expanded=False):
    default_acc = {"계좌명": ["주식 일반", "ISA계좌"], "총 투자원금": 0, "예수금": 0}
    df_acc = load_data(ACC_FILE, default_acc)
    edited_acc = st.data_editor(df_acc, num_rows="dynamic", use_container_width=True, key="acc_edit")

with st.expander("📈 2. 보유 종목 입력", expanded=False):
    default_stock = {"계좌명": ["주식 일반", "주식 일반", "ISA계좌"], "종목코드": ["005930", "000660", "453810"], "보유수량": 0}
    df_stock = load_data(STOCK_FILE, default_stock)
    df_stock['종목코드'] = df_stock['종목코드'].astype(str).str.zfill(6)
    edited_stock = st.data_editor(df_stock, num_rows="dynamic", use_container_width=True, key="stock_edit")

c1, c2 = st.columns(2)
with c1:
    if st.button("💾 데이터 저장", use_container_width=True):
        if "종목코드" in edited_stock.columns:
            edited_stock["종목코드"] = edited_stock["종목코드"].astype(str).str.zfill(6)
        save_data(edited_acc, ACC_FILE)
        save_data(edited_stock, STOCK_FILE)
        st.success("저장 완료!")
with c2:
    run_analysis = st.button("🚀 분석 시작", type="primary", use_container_width=True)




# --- [분석 및 시각화] ---
if run_analysis:
    with st.spinner("시세 및 변동 정보 로딩 중..."):
        unique_codes = edited_stock["종목코드"].unique()
        stock_info_dict = {}

        for code in unique_codes:
            try:
                # 최근 2거래일 데이터를 가져와 현재가와 전일가 추출
                df = fdr.DataReader(code).tail(2)
                if len(df) >= 2:
                    current_price = int(df.iloc[-1]['Close'])   # 오늘 종가(현재가)
                    prev_close = int(df.iloc[-2]['Close'])     # 전일 종가
                    # 변동률 계산: (현재가 - 전일가) / 전일가 * 100
                    change_rate = round(((current_price - prev_close) / prev_close) * 100, 2)
                else:
                    current_price = int(df.iloc[-1]['Close']) if not df.empty else 0
                    prev_close = current_price
                    change_rate = 0
                
                # 종목명 찾기
                name_match = all_listing[all_listing['Code'] == code]['Name']
                name = name_match.values[0] if not name_match.empty else "미등록"

                stock_info_dict[code] = {
                    "종목명": name,
                    "현재가": current_price,
                    "전일가": prev_close,
                    "변동률(%)": change_rate
                }
            except:
                stock_info_dict[code] = {"종목명": "코드확인", "현재가": 0, "전일가": 0, "변동률(%)": 0}

        # 데이터프레임에 매핑
        edited_stock["종목명"] = edited_stock["종목코드"].map(lambda x: stock_info_dict[x]["종목명"])
        edited_stock["현재가"] = edited_stock["종목코드"].map(lambda x: stock_info_dict[x]["현재가"])
        edited_stock["전일가"] = edited_stock["종목코드"].map(lambda x: stock_info_dict[x]["전일가"])
        edited_stock["변동률(%)"] = edited_stock["종목코드"].map(lambda x: stock_info_dict[x]["변동률(%)"])
        edited_stock["평가금액"] = edited_stock["보유수량"] * edited_stock["현재가"]



        
        # --- [종목별 변동 현황 출력] ---
        st.subheader("📊 종목별 실시간 변동 (통합)")
        
        # 1. 종목코드별로 그룹화하여 수량과 평가금액을 합산 (중복 제거)
        # 현재가, 전일가, 변동률은 동일하므로 first()를 사용합니다.
        unique_stock_display = edited_stock.groupby("종목코드").agg({
            '종목명': 'first',
            '현재가': 'first',
            '전일가': 'first',
            '변동률(%)': 'first',
            '보유수량': 'sum',
            '평가금액': 'sum'
        }).reset_index()

        # 2. 변동률 순으로 정렬
        unique_stock_display = unique_stock_display.sort_values(by="변동률(%)", ascending=False)

        # 3. 화면 출력 (4컬럼 레이아웃)
        stock_cols = st.columns(4)
        for idx, (i, row) in enumerate(unique_stock_display.iterrows()):
            with stock_cols[idx % 4]:
                change_amt = int(row['현재가'] - row['전일가'])
                st.metric(
                    label=row['종목명'], 
                    value=f"{int(row['현재가']):,}원", 
                    delta=f"{change_amt:+,}원 ({row['변동률(%)']:+.2f}%)"
                )



       # --- [계좌별 자산 평가 및 비중 분석] ---
        edited_stock = edited_stock.sort_values(by="평가금액", ascending=False)

        acc_stock_sum = edited_stock.groupby("계좌명")["평가금액"].sum().reset_index()
        final_df = pd.merge(edited_acc, acc_stock_sum, on="계좌명", how="left").fillna(0)
        final_df["총자산"] = final_df["평가금액"] + final_df["예수금"]
        
        final_df = final_df.sort_values(by="총자산", ascending=False)
        final_df["수익률(%)"] = ((final_df["총자산"] / final_df["총 투자원금"] - 1) * 100).round(2)

        st.divider()
        
        # --- [변경: 2컬럼 레이아웃 설정] ---
        col1, col2 = st.columns([1, 1.2]) # 비율 조절 (지표 1 : 차트 1.2)

        with col1:
            st.subheader("📍 계좌별 현황")
            for i, row in final_df.iterrows():
                st.metric(
                    label=f"{row['계좌명']}", 
                    value=f"{int(row['총자산']):,}원", 
                    delta=f"{row['수익률(%)']}%"
                )

        with col2:
            fig_pie = px.pie(
                final_df, 
                values='총자산', 
                names='계좌명', 
                title='💳 계좌별 자산 비중', 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel # 파이 차트도 파스텔톤 적용
            )
            fig_pie.update_layout(showlegend=True, margin=dict(t=50, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)



        # --- [종목별 비중 & 상세 요약 2컬럼 배치] ---
        st.divider()
        c3, c4 = st.columns([1.2, 1]) # 차트 비중을 약간 더 넓게 설정

        with c3:
            # 1. Sunburst 차트
            fig_sun = px.sunburst(
                edited_stock, 
                path=['종목명', '계좌명'], 
                values='평가금액', 
                title='🔍 종목별 상세 비중',
                color='종목명', 
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_sun.update_traces(
                textinfo="label+percent root", 
                insidetextorientation='radial'
            )
            fig_sun.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_sun, use_container_width=True)

        with c4:
            # 2. 상세 요약 피벗 (행/열 전환)
            st.subheader("📋 계좌별 요약")
            
            # 피벗을 위해 '계좌명'을 인덱스로 설정하고 필요한 컬럼만 추출
            summary_df = final_df.set_index("계좌명")[[
                "총 투자원금", "예수금", "평가금액", "총자산", "수익률(%)"
            ]]
            
            # .T 를 사용하여 행과 열을 전환 (피벗)
            pivoted_df = summary_df.T

            # 포맷팅 적용하여 출력
            st.dataframe(pivoted_df.style.format("{:,.0f}"), use_container_width=True)



       


