# dacon-wind-roadmap-v2 - Work Plan

## TL;DR (For humans)

**What you'll get**: 현재 점수(0.60154)에서 출발하여 SCADA power curve, LDAPS full grid, GFS upper-air features, temporal aggregation, Group 3 결측 보간을 **순차적으로 추가**한 6단계 개선 파이프라인. 각 단계마다 Temporal CV로 검증하여 점수 향상을 확인합니다.

**Why this approach**: 실제 데이터 분석 결과, 현재 최종 파이프라인이 기상예보 wind를 feature로만 쓰고 SCADA 실측 발전량(wind→power mapping)을 전혀 활용하지 않는 중대한 간격이 발견됨. SCADA power curve만 추가해도 NMAE 큰 폭 개선이 예상되며, 이후 LDAPS/GFS feature 확장으로 추가 개선 가능.

**What it will NOT do**: 새 모델 아키텍처(XGBoost/LightGBM 앙상블 유지), 딥러닝, 실시간 추론, 새로운 대회 참여.

**Effort**: 6개 Wave, 약 2-3주 예상 (1인 작업 기준)

**Risk**: 
- SCADA power curve이 오히려 노이즈를 주입할 가능성 (QC 필요)
- LDAPS 16개 grid 중복 feature로 overfitting 가능성
- Group 3 결측치 33%를 SCADA로 대체할 때 leakage 가능성 (SCADA에도 결측이 있다면?)
- Temporal CV의 window 크기 설정에 따른 score 변동

**Decisions**:
- 우선순위: 순차 진행 (P1→P2→P3→P4→P5)
- 코드 구조: 노트북 체계적 분할 (00_baseline, 01_power_curve, ...)
- 검증 전략: Temporal Cross-Validation
- 기본 모델: XGBoost + LightGBM 앙상블 (기존 유지)

---

## Scope

### IN
- **Wave 0**: Baseline 점수 재현 + Temporal CV framework 구축 + 노트북 구조 정리
- **Wave 1 (Priority 1)**: SCADA Power Curve + Hub Height Wind 보정
  - SCADA 데이터 QC (이상치 제거, wtg03 처리)
  - Turbine별 power curve 모델 (ws→power_kw)
  - LDAPS/GFS wind → hub height (80m) 보정 (log law)
  - 예측 파이프라인 통합
- **Wave 2 (Priority 2)**: LDAPS 16개 Grid 풀 활용
  - Grid 차원 축소 (PCA)
  - 공간 가중 평균 및 grid 간 편차 feature
- **Wave 3 (Priority 3)**: SCADA 10분→1시간 Temporal Feature
  - Ramp rate, variability, wind direction sector
- **Wave 4 (Priority 4)**: GFS Upper Air Features
  - 850/700/500hPa 등압면 feature
  - Wind shear, atmospheric stability indices
- **Wave 5 (Priority 5)**: Group 3 결측 SCADA 기반 보간
- **Wave 6**: Feature Selection + Hyperparameter Tuning + 최종 평가

### OUT
- 새로운 모델 아키텍처 도입 (CNN, LSTM, Transformer 등)
- 딥러닝 기반 접근
- 실시간/배치 추론 시스템
- 다른 대회/데이터셋 적용
- 기존 노트북 완전 폐기 (분할은 하지만 코드 재사용)

---

## Verification strategy

### Temporal Cross-Validation 상세
- **데이터 기간**: 2022-01 ~ 2024-12 (약 3년)
- **CV 전략**: 5-fold 시간순 CV (Expanding Window)
  - Fold 1: Train 2022-01~2022-12, Val 2023-01~2023-06
  - Fold 2: Train 2022-01~2023-06, Val 2023-07~2023-12
  - Fold 3: Train 2022-01~2023-12, Val 2024-01~2024-06
  - Fold 4: Train 2022-01~2024-06, Val 2024-07~2024-10
  - Fold 5: Train 2022-01~2024-10, Val 2024-11~2024-12
- **평가 지표**: NMAE + FICR 혼합 (대회 규정 동일)

### 각 Wave 검증 프로토콜
1. Baseline 점수 재현 (Wave 0에서 고정)
2. 새 feature/모듈 추가
3. Temporal CV 5-fold 실행
4. Baseline 대비 score 향상 확인 (t-test or 단순 비교)
5. Score가 악화되면 해당 wave 롤백 후 원인 분석
6. Regression test: 기존 feature만으로도 동일 score 재현되는지 확인

### Agent-executable QA
- 각 Wave의 평가 노트북은 `python -m pytest` 로 실행 가능해야 함
- 평가 결과는 CSV로 저장되어 이력 추적 가능해야 함
- 모든 평가는 재현 가능해야 함 (seed 고정)

---

## Execution strategy

### 노트북 구조
```
코드 작업/
├── .omo/plans/dacon-wind-roadmap-v2.md      # 이 파일
├── 00_baseline_evaluation.ipynb               # Baseline 재현 + Temporal CV
├── 01_scada_power_curve.ipynb                 # Wave 1: SCADA Power Curve
├── 02_ldaps_full_grid.ipynb                   # Wave 2: LDAPS 16 Grid
├── 03_scada_temporal_features.ipynb           # Wave 3: Temporal Features
├── 04_gfs_upper_air.ipynb                     # Wave 4: GFS Upper Air
├── 05_group3_imputation.ipynb                 # Wave 5: Group 3 보간
├── 06_final_optimization.ipynb                # Wave 6: Feature Selection + Tuning
├── utils.py                                    # 공통 함수 (evaluation, preprocessing 등)
└── config.py                                   # 설정 (seed, paths, parameters)
```

### 각 Wave 실행 패턴
1. `XX_<wave_name>.ipynb` 노트북 생성
2. Feature 엔지니어링/모델링 실험
3. Temporal CV 평가 → baseline 점수표 업데이트
4. 다음 wave로 진행

### 의존성 매트릭스
```
Wave 0 (Baseline) ← 모든 Wave의 기반
  └── Wave 1 (Power Curve) ← 독립적, SCADA + LDAPS/GFS wind
       └── Wave 2 (LDAPS Grid) ← Wave 1의 hub height wind feature 활용 가능
            └── Wave 3 (Temporal) ← Wave 1의 SCADA 처리 의존
                 └── Wave 4 (GFS Upper) ← 독립적, GFS 데이터
                      └── Wave 5 (Group 3) ← Wave 1의 power curve 활용
                           └── Wave 6 (Final) ← 모든 feature 통합
```

---

## Todos

### Wave 0: Baseline & Infrastructure

#### Todo 0.1: Baseline score 재현 + Temporal CV framework
- **파일**: `00_baseline_evaluation.ipynb`, `utils.py`, `config.py`
- **작업**:
  - `config.py`: seed=42, paths, model params 고정
  - `utils.py`: evaluation_metrics(nmae, ficr, combined_score), temporal_cv_split(), load_data() 함수
  - `00_baseline_evaluation.ipynb`: 기존 `클로드 코드 피드백+제미나이 리팩토링+가짜정답박멸.ipynb`에서 최종 pipeline만 추출
  - Temporal CV 5-fold로 baseline score 계산
  - 기준 score 0.60154와 일치하는지 확인
- **Acceptance criteria**:
  - [ ] Temporal CV 5-fold 실행 완료
  - [ ] Baseline score 0.60154 ± 0.01 재현
  - [ ] 각 fold의 score가 CSV로 저장됨
  - [ ] `config.py`의 seed 변경 시 같은 결과 재현
- **QA (happy)**: 전체 노트북 `Restart & Run All` 시 에러 없이 완료
- **QA (failure)**: seed mismatch 시 결과가 달라지는지 확인
- **Commit**: `git add .omo/ 00_baseline_evaluation.ipynb utils.py config.py && git commit -m "wave0: baseline + temporal cv framework"`

#### Todo 0.2: 노트북 분할 구조 생성
- **파일**: `01_scada_power_curve.ipynb`, `02_ldaps_full_grid.ipynb`, `03_scada_temporal_features.ipynb`, `04_gfs_upper_air.ipynb`, `05_group3_imputation.ipynb`, `06_final_optimization.ipynb`
- **작업**:
  - 각 노트북 skeleton 생성 (imports, data loading, config)
  - `00_baseline_evaluation.ipynb`의 공통 전처리 부분을 함수화하여 `utils.py`에 추가
- **Acceptance criteria**:
  - [ ] 6개 노트북 skeleton 생성 완료
  - [ ] 각 노트북이 `utils.py`/`config.py`를 import 가능
  - [ ] baseline data load부터 평가까지 각 노트북에서 재현 가능
- **QA**: 각 skeleton 노트북 실행 시 최소한 data load까지 에러 없음
- **Commit**: `git add *.ipynb && git commit -m "wave0: notebook skeleton structure"`

---

### Wave 1: SCADA Power Curve + Hub Height Wind (Priority 1)

#### Todo 1.1: SCADA 데이터 QC 및 분석
- **파일**: `01_scada_power_curve.ipynb`, `utils.py`
- **작업**:
  - Vestas 12개 터빈: power_kw10m, ws, wd 기초통계 및 시각화
  - Unison 5개 터빈: 동일 (wtg03 power=0 확인 및 제외 처리)
  - 이상치 탐지: power_kw10m 극단값(±40M) winsorization (1%~99% 또는 IQR)
  - Power curve 시각화: 각 turbine별 ws→power_kw scatter + fitted curve
  - Wind direction 분석: wd 분포, turbine별 wd-power 관계
- **Acceptance criteria**:
  - [ ] 각 turbine별 ws-power scatter plot 생성 (12+5개)
  - [ ] 이상치 처리 전/후 통계 변화 기록
  - [ ] Unison wtg03 제외 처리 로직 구현
  - [ ] Power curve 이상치(ws는 높은데 power 낮은 점) 제거 규칙 정의
- **Commit**: `git add 01_scada_power_curve.ipynb && git commit -m "wave1: scada qc and analysis"`

#### Todo 1.2: Turbine별 Power Curve Model 학습
- **파일**: `01_scada_power_curve.ipynb`, `utils.py`
- **작업**:
  - 각 turbine별 RandomForest (n_estimators=100, max_depth=10)로 ws→power_kw 학습
  - Input: `ws` (+ optional: `wd` cos/sin 변환)
  - Target: `power_kw10m` (winsorized)
  - 평가: MAE, R2 per turbine
  - Power curve 모델 저장 (pickle 또는 함수 형태로 utils.py에 통합)
- **Acceptance criteria**:
  - [ ] 15개 turbine(12+5, wtg03 제외=16-1) 모델 학습 완료
  - [ ] 각 turbine R2 > 0.9 (일반적인 wind power curve)
  - [ ] 모델이 `predict(ws)` 형태로 호출 가능
- **Commit**: `git add 01_scada_power_curve.ipynb utils.py && git commit -m "wave1: per-turbine power curve models"`

#### Todo 1.3: Wind Speed Vertical Extrapolation (Log Law)
- **파일**: `01_scada_power_curve.ipynb`, `utils.py`
- **작업**:
  - Log law: `u(z) = u(z_ref) * ln(z/z0) / ln(z_ref/z0)`
  - LDAPS 50m wind → 80m (Vestas/Unison hub height 가정) 보정 함수
  - GFS 80m wind → 그대로 사용, GFS 100m → 80m 보간
  - z0(roughness length) 추정: surface properties 기반 또는 고정값(0.1)
  - SCADA 실측 ws와 보정 ws 비교 검증
- **Acceptance criteria**:
  - [ ] `wind_extrapolate(u, z_from, z_to, z0=0.1)` 함수 구현
  - [ ] LDAPS 50m→80m 보정값과 SCADA 실측 80m ws의 RMSE 계산
  - [ ] GFS 100m→80m 보간 함수 구현
- **Commit**: `git add utils.py 01_scada_power_curve.ipynb && git commit -m "wave1: wind speed vertical extrapolation"`

#### Todo 1.4: Power Curve + Hub Height Wind → Pipeline 통합
- **파일**: `01_scada_power_curve.ipynb`
- **작업**:
  - 현재 파이프라인에서 기존 wind feature를 대체/보완하는 방식 결정
  - **Option A (recommended)**: LDAPS/GFS wind → hub height 보정 → power curve → turbine별 발전량 예측 → Group별 합산
  - **Option B**: power curve 예측값을 기존 feature에 추가 feature로 붙임
  - Temporal CV로 평가: Option A vs B vs Baseline
  - 기존 3개 target(kpx_group_1/2/3) 예측 유지
- **Acceptance criteria**:
  - [ ] Power curve 예측값이 pipeline에 통합됨
  - [ ] Temporal CV 5-fold score 계산
  - [ ] Baseline(0.60154) 대비 score 개선 확인
  - [ ] 개선되지 않을 경우 Option B 시도 후 비교
- **Commit**: `git add 01_scada_power_curve.ipynb && git commit -m "wave1: integrate power curve into pipeline"`

---

### Wave 2: LDAPS 16개 Grid 풀 활용 (Priority 2)

#### Todo 2.1: LDAPS Grid 차원 축소 (PCA)
- **파일**: `02_ldaps_full_grid.ipynb`
- **작업**:
  - 16개 grid × 64 feature → grid_id별 pivot
  - 각 기상변수(ws, wd, temp, pressure 등)별로 16차원 벡터 구성
  - PCA 변환 (n_components=3~10, explained variance 95% 기준)
  - Scree plot으로 최적 component 수 결정
- **Acceptance criteria**:
  - [ ] PCA 변환 완료 (n_components 결정)
  - [ ] 누적 설명분산 95% 이상
  - [ ] 각 주성분의 해석 (예: PC1=평균풍속, PC2=동서편차 등)
- **Commit**: `git add 02_ldaps_full_grid.ipynb && git commit -m "wave2: ldaps grid pca"`

#### Todo 2.2: Grid 간 공간 Feature
- **파일**: `02_ldaps_full_grid.ipynb`
- **작업**:
  - Grid 간 편차 feature: `ws_grid_i - ws_grid_j` (모든 쌍 또는 주요 쌍)
  - 또는 grid별 ws의 표준편차, 최대-최소 차이
  - 공간 가중 평균: turbine 위치 기준 inverse-distance weighting
  - 대상 변수: 50m ws, 10m ws, 2m temp, surface pressure
- **Acceptance criteria**:
  - [ ] 최소 5개의 grid-difference feature 생성
  - [ ] Grid ws std/range feature 생성
  - [ ] PIPELINE 통합 후 Temporal CV 평가
- **Commit**: `git add 02_ldaps_full_grid.ipynb && git commit -m "wave2: spatial grid features"`

---

### Wave 3: SCADA Temporal Features (Priority 3)

#### Todo 3.1: SCADA 10분→1시간 집계 Feature
- **파일**: `03_scada_temporal_features.ipynb`
- **작업**:
  - SCADA 10분 데이터를 1시간 단위로 집계
  - Feature 목록 (turbine별):
    - `ws_mean`, `ws_std`, `ws_min`, `ws_max` (풍속 변동성)
    - `power_mean`, `power_std`, `power_min`, `power_max`
    - `power_ramp_max`: 10분 간 최대 power 변화량 (급변 감지)
    - `wd_mean`, `wd_std`: 풍향 평균 및 변동성
    - `power_coverage`: 정상 가동 시간 비율 (power>0 비율)
  - Turbine 간 집계: 전체 Vestas 평균, std, 합계 등
- **Acceptance criteria**:
  - [ ] 10분→1시간 집계 로직 구현 (groupby hour)
  - [ ] 최소 20개 temporal feature 생성
  - [ ] Pipeline 통합 후 Temporal CV 평가 (Baseline + Wave1 대비)
- **Commit**: `git add 03_scada_temporal_features.ipynb && git commit -m "wave3: scada temporal aggregation"`

#### Todo 3.2: Wind Direction Sector Feature
- **파일**: `03_scada_temporal_features.ipynb`
- **작업**:
  - 풍향 16방위(22.5°씩) sector 분할
  - 각 sector별 평균 power (섹터별 power curve의 차이 활용)
  - 특정 풍향에서 turbine wake 효과 탐지
    - wtg12가 특정 wd에서 다른 패턴 → wd sector × turbine interaction feature
- **Acceptance criteria**:
  - [ ] 16-sector wd feature 생성
  - [ ] Sector별 turbine power 차이 분석 완료
  - [ ] Pipeline 통합 후 평가
- **Commit**: `git add 03_scada_temporal_features.ipynb && git commit -m "wave3: wind direction sector features"`

---

### Wave 4: GFS Upper Air Features (Priority 4)

#### Todo 4.1: GFS 850/700/500hPa Feature 추출
- **파일**: `04_gfs_upper_air.ipynb`
- **작업**:
  - GFS 데이터에서 등압면 변수 추출:
    - 850hPa: `T_850hPa`, `HGT_850hPa`, `RH_850hPa`
    - 700hPa: `T_700hPa`, `HGT_700hPa`, `RH_700hPa`
    - 500hPa: `T_500hPa`, `HGT_500hPa`, `RH_500hPa`
  - GFS 5개 grid_id의 평균/차이
  - 현재 사용 중인 GFS grid 5만 확장 → 9개 grid 활용
- **Acceptance criteria**:
  - [ ] 9개 GFS grid 모두 feature에 포함
  - [ ] 등압면 변수 추출 완료 (최소 9개 feature)
- **Commit**: `git add 04_gfs_upper_air.ipynb && git commit -m "wave4: gfs upper air features"`

#### Todo 4.2: Wind Shear + Atmospheric Stability
- **파일**: `04_gfs_upper_air.ipynb`
- **작업**:
  - Wind shear features:
    - `shear_100m_850hPa = ws_100m - ws_850hPa`
    - `shear_850_500 = ws_850hPa - ws_500hPa`
  - Thermal stability:
    - `stability_850_500 = T_850hPa - T_500hPa` (큰 양수 = 안정, 음수 = 불안정)
    - `stability_700_500 = T_700hPa - T_500hPa`
  - Vertical wind profile features (bulk Richardson number 유사)
- **Acceptance criteria**:
  - [ ] 최소 5개 wind shear/stability feature 생성
  - [ ] Pipeline 통합 후 Temporal CV 평가 (모든 이전 Wave 대비)
- **Commit**: `git add 04_gfs_upper_air.ipynb && git commit -m "wave4: wind shear and stability features"`

---

### Wave 5: Group 3 결측 SCADA 기반 보간 (Priority 5)

#### Todo 5.1: SCADA 기반 결측 Label 대체
- **파일**: `05_group3_imputation.ipynb`
- **작업**:
  - 현재: Group 3 label 33% 결측 → 선형보간
  - 제안: 결측 위치에서 SCADA power curve 예측값 + GFS/LDAPS wind 기반 예측값으로 대체
  - 구체적 방법:
    1. 결측 label 위치 식별
    2. 해당 시점의 SCADA power (있다면) 사용
    3. SCADA 없으면 power curve model로 ws→power 예측
    4. 그래도 없으면 GFS/LDAPS 기반 예측값 사용
  - Leakage 방지: 학습 시에만 이 보간 사용, validation/test 시에는 raw label 유지
- **Acceptance criteria**:
  - [ ] 결측 label 식별 및 보간 로직 구현
  - [ ] SCADA/power curve/gfs 3단계 fallback 보간
  - [ ] Pipeline 통합 후 Temporal CV 평가 (Group 3 score 별도 기록)
  - [ ] Leakage 없는지 검증 (train/val 분리 상태에서 보간)
- **Commit**: `git add 05_group3_imputation.ipynb && git commit -m "wave5: scada-based group3 imputation"`

---

### Wave 6: Final Optimization

#### Todo 6.1: Feature Selection
- **파일**: `06_final_optimization.ipynb`
- **작업**:
  - 모든 Wave feature 통합
  - Feature importance 분석 (RF/XGB importance, permutation importance)
  - Low-importance feature 제거 (threshold 기반)
  - Feature correlation 분석 → 다중공선성 제거
- **Acceptance criteria**:
  - [ ] 모든 feature importance ranking 완료
  - [ ] 제거 후 score 유지 또는 개선 확인
  - [ ] 최종 feature set 결정
- **Commit**: `git add 06_final_optimization.ipynb && git commit -m "wave6: feature selection"`

#### Todo 6.2: Hyperparameter Tuning (Optuna)
- **파일**: `06_final_optimization.ipynb`
- **작업**:
  - Optuna로 XGBoost + LightGBM hyperparameter tuning
  - Search space: n_estimators, max_depth, learning_rate, subsample, colsample_bytree, reg_lambda, reg_alpha
  - Temporal CV 3-fold (속도 고려) + combined score 최적화
  - 최적 파라미터로 최종 모델 학습
- **Acceptance criteria**:
  - [ ] Optuna 100 trials 이상 완료
  - [ ] 최적 파라미터 저장
  - [ ] Tuning 전/후 score 비교
- **Commit**: `git add 06_final_optimization.ipynb && git commit -m "wave6: hyperparameter tuning"`

#### Todo 6.3: 최종 평가 및 Submission 생성
- **파일**: `06_final_optimization.ipynb`
- **작업**:
  - 모든 Wave 통합 최종 파이프라인
  - Temporal CV 5-fold 최종 score
  - Test set 예측 → submission.csv 생성
  - Baseline(0.60154) 대비 score 개선 최종 확인
  - 결과 요약 테이블 (각 Wave별 score 변화)
- **Acceptance criteria**:
  - [ ] 최종 submission.csv 생성
  - [ ] 각 Wave별 score 변화 표로 정리
  - [ ] Baseline score와 최종 score 비교 (p-value or 단순 비교)
  - [ ] 최종 score가 Baseline보다 개선됨
- **Commit**: `git add 06_final_optimization.ipynb submission.csv && git commit -m "wave6: final evaluation and submission"`

---

## Final verification wave

(실행 후 모든 Todo 완료 시 아래 항목을 **병렬**로 검증)

1. **F1 - Plan compliance audit**: 각 Todo의 Acceptance criteria가 충족되었는지 확인
2. **F2 - Score integrity**: Baseline(0.60154) 대비 최종 score 개선 확인, Temporal CV 5-fold 결과 CSV 검증
3. **F3 - Full pipeline run**: 00→01→02→03→04→05→06 순서로 `Restart & Run All` 시 에러 없이 완료
4. **F4 - Submission integrity**: submission.csv 형식 일치 (forecast_id, forecast_kst_dtm, kpx_group_1/2/3)

## Commit strategy

- **단위**: 각 Todo 완료 시 1 commit
- **메시지 형식**: `wave<N>: <description>` (예: `wave1: scada qc and analysis`)
- **Wave 완료 시점**: 해당 Wave의 모든 Todo가 완료되고 Temporal CV score 확인된 시점에 추가 commit
  - 메시지: `wave<N> complete: score X.XXXXX (+Y.YY% vs baseline)`
- **최종 완료 시**: `final: score X.XXXXX (+Y.YY% vs baseline)`

## Success criteria

1. **Score**: 최종 Temporal CV score > Baseline (0.60154) — 최소 2% 이상 개선 목표
2. **Reproducibility**: 전체 pipeline `Restart & Run All`로 완전 재현 가능
3. **Modularity**: 각 Wave 노트북이 독립적으로 실행 가능 (의존성은 import로 해결)
4. **Traceability**: 각 Wave별 score 변화 추적 가능 (CSV 이력)
5. **Submission**: 최종 submission.csv 형식 오류 없음
