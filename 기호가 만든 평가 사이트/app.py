import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 상수 정의
TARGET_COLS = ["kpx_group_1", "kpx_group_2", "kpx_group_3"]
CAPACITY_KWH = {"kpx_group_1": 21600, "kpx_group_2": 21600, "kpx_group_3": 21000}

st.set_page_config(page_title="BARAM 2026 로컬 채점기", layout="wide")

# ==========================================
# 1. 평가 산식 함수 (에러 수정 완료)
# ==========================================
def metric(answer_df, pred_df):
    group_nmae, group_ficr = [], []
    valid_masks = {} 
    
    for col in TARGET_COLS:
        actual = answer_df[col].to_numpy(dtype=float)
        forecast = pred_df[col].to_numpy(dtype=float)
        capacity = CAPACITY_KWH[col]

        # 실제 발전량이 설비용량의 10% 이상인 시간대만 평가
        valid = actual >= capacity * 0.10
        valid_masks[col] = valid
        
        valid_actual = actual[valid]
        valid_forecast = forecast[valid]

        # 10% 이상인 구간이 아예 없을 경우의 예외 방어
        if len(valid_actual) == 0:
            group_nmae.append(1.0)
            group_ficr.append(0.0)
            continue

        # NMAE 계산
        error_rate = np.abs(valid_forecast - valid_actual) / capacity
        group_nmae.append(np.mean(error_rate))

        # FICR 계산
        unit_price = np.select([error_rate <= 0.06, error_rate <= 0.08], [4.0, 3.0], default=0.0)
        earned_settlement = np.sum(valid_actual * unit_price)
        max_settlement = np.sum(valid_actual * 4.0)
        
        group_ficr.append(earned_settlement / max_settlement if max_settlement > 0 else 0)

    one_minus_nmae = 1 - np.mean(group_nmae)
    ficr = np.mean(group_ficr)
    total_score = 0.5 * one_minus_nmae + 0.5 * ficr
    
    return total_score, one_minus_nmae, ficr, group_nmae, group_ficr, valid_masks

# ==========================================
# 2. UI 및 파일 업로드
# ==========================================
st.title("🌬️ BARAM 2026 로컬 분석 리더보드 (Pro)")
st.markdown("데이터 명세서 기반 **10% 발전량 컷오프 라인** 과 **오차 산점도** 를 통해 모델의 약점을 분석하세요.")

col1, col2 = st.columns(2)
with col1:
    answer_file = st.file_uploader("정답 CSV 업로드 (True)", type=['csv'])
with col2:
    pred_file = st.file_uploader("예측 CSV 업로드 (Pred)", type=['csv'])

if answer_file and pred_file:
    try:
        ans_df = pd.read_csv(answer_file)
        prd_df = pd.read_csv(pred_file)
        
        # 시간축 맞추기
        if "forecast_kst_dtm" in ans_df.columns:
            ans_df["forecast_kst_dtm"] = pd.to_datetime(ans_df["forecast_kst_dtm"])
            prd_df["forecast_kst_dtm"] = pd.to_datetime(prd_df["forecast_kst_dtm"])
            
        total_score, omn, ficr, nmaes, ficrs, valid_masks = metric(ans_df, prd_df)
        
        # ==========================================
        # 3. 종합 점수 대시보드
        # ==========================================
        st.success(f"## 🎉 최종 점수 (Score): {total_score:.5f}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("1 - NMAE", f"{omn:.5f}")
        c2.metric("FICR (정산금획득률)", f"{ficr:.5f}")
        c3.info("💡 10% 미만 발전량은 평가에서 자동 제외됩니다.")
        
        # ==========================================
        # 4. 그룹별 상세 분석 탭
        # ==========================================
        st.markdown("---")
        st.subheader("📊 그룹별 상세 분석")
        
        tabs = st.tabs(["KPX Group 1", "KPX Group 2", "KPX Group 3"])
        
        for i, tgt in enumerate(TARGET_COLS):
            with tabs[i]:
                cap = CAPACITY_KWH[tgt]
                
                sc1, sc2 = st.columns(2)
                sc1.metric(f"[{tgt}] 1-NMAE", f"{1-nmaes[i]:.4f}")
                sc2.metric(f"[{tgt}] FICR", f"{ficrs[i]:.4f}")
                
                # 병합된 데이터 준비
                time_col = ans_df["forecast_kst_dtm"] if "forecast_kst_dtm" in ans_df.columns else ans_df.index
                df_plot = pd.DataFrame({
                    "Time": time_col,
                    "True": ans_df[tgt],
                    "Pred": prd_df[tgt],
                    "Is_Valid": valid_masks[tgt]
                })
                df_plot["Error_Rate(%)"] = np.abs(df_plot["Pred"] - df_plot["True"]) / cap * 100
                
                # --- Plot 1: 실제값 vs 예측값 산점도 ---
                st.markdown("**1. 실제 발전량 vs 예측 발전량 산점도**")
                st.caption("대각선(빨간 점선)에 가까울수록 예측이 정확합니다. 회색 영역은 평가에 들어가지 않는 10% 미만 구간입니다.")
                
                fig_scatter = px.scatter(
                    df_plot[df_plot["Is_Valid"]], x="True", y="Pred", 
                    opacity=0.3, color="Error_Rate(%)", color_continuous_scale="Viridis",
                    labels={"True": "실제 발전량 (kWh)", "Pred": "예측 발전량 (kWh)"}
                )
                fig_scatter.add_trace(go.Scatter(x=[cap*0.1, cap], y=[cap*0.1, cap], mode="lines", name="Ideal (y=x)", line=dict(color="red", dash="dash")))
                fig_scatter.add_vrect(x0=0, x1=cap*0.1, fillcolor="gray", opacity=0.2, layer="below", line_width=0)
                st.plotly_chart(fig_scatter, use_container_width=True)

                # --- Plot 2: 시계열 트렌드 ---
                st.markdown("**2. 시계열 예측 트렌드 (최근 500시간)**")
                df_time = df_plot.tail(500)
                
                fig_time = go.Figure()
                fig_time.add_trace(go.Scatter(x=df_time["Time"], y=df_time["True"], mode='lines', name='Actual', line=dict(color='blue')))
                fig_time.add_trace(go.Scatter(x=df_time["Time"], y=df_time["Pred"], mode='lines', name='Predicted', line=dict(color='orange', dash='dot')))
                fig_time.add_hline(y=cap*0.1, line_dash="dash", line_color="gray", annotation_text="평가 제외 기준선 (10% 용량)")
                st.plotly_chart(fig_time, use_container_width=True)
                
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")