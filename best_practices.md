# Credit Scoring Model Development - Best Practices Guide

## Table of Contents
1. [Essential Data Requirements](#essential-data-requirements)
2. [Industry Best Practices](#industry-best-practices)
3. [Feature Engineering Guidelines](#feature-engineering-guidelines)
4. [Model Development Process](#model-development-process)
5. [Model Evaluation Metrics](#model-evaluation-metrics)
6. [Regulatory & Risk Management](#regulatory--risk-management)
7. [Common Pitfalls to Avoid](#common-pitfalls-to-avoid)
8. [Recommendations for Your Model](#recommendations-for-your-model)

---

## Essential Data Requirements

### 1. Credit Bureau Data (CRITICAL) ⭐⭐⭐⭐⭐

**What you have:** MKR (Credit Registry) data from `scoring.qnb_mkr_data_mba_backup`

**Key features needed:**

#### Payment History - Most Important Predictor
- Days past due (current and historical)
- Number of missed payments
- Maximum delinquency ever reached
- Recent payment behavior (last 3, 6, 12 months)

#### Credit Utilization
- Outstanding balance / Credit limit
- Number of active loans
- Total debt burden

#### Credit Age & Mix
- Length of credit history
- Age of oldest account
- Types of credit (mortgage, consumer, cards)
- Number of recent inquiries

#### Derogatory Marks
- Defaults, write-offs, bankruptcies
- Collections accounts
- Loan restructurings

**Industry benchmark:** Credit bureau data typically contributes **60-70% of model predictive power**

---

### 2. Application Data ⭐⭐⭐⭐⭐

**What you need:**

#### Loan Characteristics
- Requested amount
- Loan purpose (auto, home, consumption)
- Requested term
- Collateral type and value
- Interest rate offered

#### Loan-to-Value Ratios
- LTV for secured loans
- Debt-to-income ratio (DTI)
- Payment-to-income ratio (PTI)

---

### 3. Income & Employment Data ⭐⭐⭐⭐

**What you have:** ASAN Finance data via `ibs.asan_finance_is_yeri_v2@ibs_ro`

**Key features:**

#### Income Stability
- Monthly/annual income
- Income source (salary, business, pension)
- Employment sector (public vs private)
- Length of employment
- Employer stability

#### Income Verification
- Official tax records (from ASAN) ✓ BEST
- Bank statements
- Employment verification

**Industry benchmark:** Income data contributes **15-20% of predictive power**

**Best practice:** Official government data (like ASAN) is MUCH better than self-reported income

---

### 4. Demographic Data ⭐⭐⭐

**What you have:** From MKR data

**Key features:**
- Age (strong U-shaped relationship with default)
- Education level
- Marital status
- Region/location
- Number of dependents

**Industry benchmark:** Demographics contribute **5-10% of predictive power**

**⚠️ Important:** Avoid protected characteristics (gender, ethnicity, religion) - regulatory risk

---

### 5. Behavioral Data (Existing Customers Only) ⭐⭐⭐⭐

**If available:**
- Transaction history
- Account usage patterns
- Overdraft frequency
- Savings behavior
- Cross-selling success

**Industry benchmark:** For existing customers, behavioral data can add **10-15% lift**

---

### 6. External Data Sources ⭐⭐⭐

**Nice to have:**
- Property ownership records
- Vehicle ownership
- Business ownership
- Utility payment history
- Social media (controversial, limited use)
- Alternative credit data

---

## Industry Best Practices

### Data Quality Standards

#### Minimum Sample Size
```
For binary classification (default/no default):
- Minimum: 1,500-2,000 defaults (events)
- Recommended: 3,000-5,000+ defaults
- Ideal: 10,000+ defaults

Your data: 96,327 loans
If ~3-5% default rate → 3,000-5,000 defaults ✓ GOOD
```

#### Time Window
```
Training window: 2-3 years of historical data
Performance window: 12-24 months to observe defaults

Your data: 2018-2021 (3 years) ✓ GOOD
```

#### Data Quality Requirements
```
✓ Missing values: <10% for critical features
✓ Outliers: Winsorize at 1st and 99th percentile
✓ Temporal stability: Check for structural breaks
✓ Data lineage: Document all transformations
```

---

## Feature Engineering Guidelines

### 1. Payment History Features (Strongest Predictors)

#### Recency - Recent Behavior Matters More
```python
# Features to create:
- days_past_due_last_3m
- days_past_due_last_6m
- days_past_due_last_12m
- months_since_last_delinquency
```

#### Frequency - How Often Do They Miss Payments?
```python
# Features to create:
- num_missed_payments_12m
- num_30dpd_ever
- num_60dpd_ever
- num_90dpd_ever
- pct_months_with_payment_12m
```

#### Severity - How Bad Is the Worst Delinquency?
```python
# Features to create:
- max_dpd_ever
- max_dpd_12m
- max_dpd_24m
- worst_status_12m
- worst_status_ever
```

#### Trend - Is Behavior Improving or Worsening?
```python
# Features to create:
- dpd_trend_3m_vs_12m
- payment_consistency_score
- delinquency_direction (improving/stable/worsening)
```

**Example implementation:**
```python
# Recency
df['months_since_last_dlq'] = (
    (df['current_date'] - df['last_delinquency_date']).dt.days / 30
)

# Frequency
df['num_90dpd_12m'] = df.groupby('customer_id').apply(
    lambda x: (x['days_past_due'] >= 90).sum()
)

# Severity
df['max_dpd_ever'] = df.groupby('customer_id')['days_past_due'].max()

# Trend
df['dpd_improving'] = (
    df['avg_dpd_last_3m'] < df['avg_dpd_6m_to_3m']
).astype(int)
```

---

### 2. Utilization Features

#### Current Utilization
```python
# Features to create:
- utilization_rate = outstanding_balance / credit_limit
- total_debt_to_income = total_outstanding / monthly_income
- payment_to_income = monthly_payment / monthly_income
- available_credit = credit_limit - outstanding_balance
```

#### Utilization Trend
```python
# Features to create:
- utilization_change_3m
- utilization_change_6m
- balance_growth_rate_6m
- credit_limit_usage_trend
```

**Example implementation:**
```python
# Current utilization
df['utilization_rate'] = (
    df['outstanding_debt_main'] / df['line_ammount'].replace(0, np.nan)
).fillna(0).clip(0, 2)  # Cap at 200%

# DTI ratio
df['dti_ratio'] = (
    df['outstanding_debt_main'] / (df['gross_salary'] * 12).replace(0, np.nan)
).fillna(0)

# PTI ratio
df['pti_ratio'] = (
    df['monthly_payment_amount'] / df['gross_salary'].replace(0, np.nan)
).fillna(0)
```

---

### 3. Credit Vintage Features

#### Account Age
```python
# Features to create:
- months_since_first_loan
- months_since_newest_loan
- avg_account_age
- credit_history_length
```

#### Account Diversity
```python
# Features to create:
- num_active_loans
- num_closed_loans
- num_loan_types
- has_mortgage (binary)
- has_auto_loan (binary)
- has_credit_card (binary)
- credit_mix_score
```

**Example implementation:**
```python
# Account age
df['months_since_first_loan'] = (
    (df['mkr_date'] - df['granted_on']).dt.days / 30
)

# Active loans count
df['num_active_loans'] = df.groupby('fin')['id'].transform('count')

# Loan type diversity
df['num_loan_types'] = df.groupby('fin')['credit_type'].transform('nunique')

# Credit mix (Herfindahl index)
def credit_mix_score(group):
    counts = group['credit_type'].value_counts(normalize=True)
    return 1 - (counts ** 2).sum()

df['credit_mix'] = df.groupby('fin').apply(credit_mix_score)
```

---

### 4. Income & Capacity Features

#### Income Stability
```python
# Features to create:
- months_at_current_employer
- income_growth_rate
- employer_sector_risk
- has_verified_income (binary)
```

#### Affordability
```python
# Features to create:
- residual_income = income - all_debt_payments
- debt_service_coverage_ratio
- savings_to_income_ratio
- discretionary_income
```

**Example implementation:**
```python
# Residual income
df['residual_income'] = (
    df['gross_salary'] - df['monthly_payment_amount']
)

# Debt service coverage ratio
df['dscr'] = (
    df['gross_salary'] / df['monthly_payment_amount'].replace(0, np.nan)
).fillna(999).clip(0, 10)

# Income verification flag
df['has_verified_income'] = df['gross_salary'].notna().astype(int)
```

---

### 5. Loan-Specific Features

```python
# Features to create:
- loan_to_value_ratio (for secured loans)
- requested_amount_to_income
- loan_term_months
- interest_rate
- collateral_value_to_loan
- loan_purpose_risk_score
```

**Example implementation:**
```python
# LTV ratio
df['ltv_ratio'] = (
    df['initial_amount'] / df['collateral_market_value'].replace(0, np.nan)
).fillna(0)

# Loan to annual income
df['loan_to_annual_income'] = (
    df['initial_amount'] / (df['gross_salary'] * 12).replace(0, np.nan)
).fillna(0)

# Loan term
df['loan_term_months'] = (
    (df['contract_due_on'] - df['granted_on']).dt.days / 30
)
```

---

### 6. Aggregation Features

```python
# Customer-level aggregations:
- total_outstanding_all_loans
- avg_interest_rate_portfolio
- num_loans_last_12m
- total_credit_limit
- max_single_loan_amount
- portfolio_weighted_dpd
```

**Example implementation:**
```python
# Total exposure
df['total_outstanding'] = df.groupby('fin')['outstanding_debt_main'].transform('sum')

# Average interest rate
df['avg_interest_rate'] = df.groupby('fin')['interest_rate'].transform('mean')

# Portfolio metrics
df['portfolio_max_dpd'] = df.groupby('fin')['days_main_sum_overdue'].transform('max')
```

---

## Model Development Process

### Step 1: Define Target Variable

**Performance Window Approach:**
```python
# Observation point: When loan was granted
# Performance window: 12-24 months after origination
# Bad definition: Customer reached 90+ DPD within performance window

Example:
Loan granted: 2019-01-15
Performance window: 2019-01-15 to 2020-01-15 (12 months)
Target variable: Did customer reach 90+ DPD? (Yes=1, No=0)
```

**Common bad definitions:**
```python
# Option 1: Ever 90+ DPD (most common)
target = (max_dpd_12m >= 90).astype(int)

# Option 2: Ever 60+ DPD (more conservative)
target = (max_dpd_12m >= 60).astype(int)

# Option 3: Ever defaulted (most strict)
target = (credit_status.isin(['005', '006', '007', '008'])).astype(int)

# Recommended: 90+ DPD within 12 months
```

**Implementation:**
```python
def create_target(df, performance_months=12, dpd_threshold=90):
    """
    Create target variable for credit scoring

    Args:
        df: DataFrame with loan data
        performance_months: Months to observe after origination
        dpd_threshold: Days past due threshold for "bad"

    Returns:
        DataFrame with target variable
    """
    # Calculate performance window end date
    df['performance_end_date'] = df['granted_on'] + pd.DateOffset(months=performance_months)

    # Get maximum DPD within performance window
    df['max_dpd_in_window'] = df.groupby('id').apply(
        lambda x: x.loc[x['mkr_date'] <= x['performance_end_date'], 'days_main_sum_overdue'].max()
    )

    # Create binary target
    df['target'] = (df['max_dpd_in_window'] >= dpd_threshold).astype(int)

    return df
```

---

### Step 2: Temporal Validation (CRITICAL!)

**❌ WRONG Approach:**
```python
# Random split - CAUSES DATA LEAKAGE!
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
# This will give overly optimistic results!
```

**✓ CORRECT Approach:**
```python
# Time-based split - Simulates production
# Train on past, validate on future (out-of-time validation)

# Split by origination date
train_data = df[df['granted_on'] < '2020-01-01']  # 2018-2019
val_data = df[(df['granted_on'] >= '2020-01-01') &
              (df['granted_on'] < '2021-01-01')]  # 2020
test_data = df[df['granted_on'] >= '2021-01-01']  # 2021

# This simulates real production:
# "Train on 2018-2019, predict 2020, test on 2021"
```

**Why temporal split is critical:**
- Prevents data leakage from future
- Tests model stability over time
- Realistic performance estimation
- Detects concept drift
- Required by regulators (Basel)

---

### Step 3: Handle Class Imbalance

**The Problem:**
```python
# Typical credit data is imbalanced:
Good customers: 95% (majority class)
Bad customers:   5% (minority class)

# Model can achieve 95% accuracy by predicting "good" for everyone!
```

**Solutions:**

#### Option 1: SMOTE (Synthetic Minority Over-sampling)
```python
from imblearn.over_sampling import SMOTE

smote = SMOTE(sampling_strategy=0.3, random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
```

#### Option 2: Class Weights (Recommended)
```python
from sklearn.linear_model import LogisticRegression

# Automatically adjust weights inversely proportional to class frequencies
model = LogisticRegression(class_weight='balanced')
model.fit(X_train, y_train)
```

#### Option 3: XGBoost scale_pos_weight
```python
import xgboost as xgb

# Calculate scale_pos_weight
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

model = xgb.XGBClassifier(
    scale_pos_weight=scale_pos_weight,
    max_depth=5,
    learning_rate=0.1,
    n_estimators=100
)
model.fit(X_train, y_train)
```

**Recommendation:** Use XGBoost with `scale_pos_weight` - most effective for credit scoring

---

### Step 4: Model Selection

**Comparison of Common Models:**

| Model | Interpretability | Accuracy | Speed | Regulatory | Use Case |
|-------|-----------------|----------|-------|------------|----------|
| **Logistic Regression** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✓ Easy | Baseline, retail banking |
| **Scorecard (WOE)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✓ Easy | Traditional banks, manual |
| **Random Forest** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⚠️ Medium | Ensemble component |
| **XGBoost/LightGBM** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⚠️ Hard | Best performance, modern |
| **Neural Networks** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ Very hard | Large banks, big data |

**Industry Standard Approach:**

#### Baseline: Logistic Regression
```python
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# Train model
lr_model = LogisticRegression(
    class_weight='balanced',
    max_iter=1000,
    random_state=42
)
lr_model.fit(X_train_scaled, y_train)

# Feature importance
feature_importance = pd.DataFrame({
    'feature': feature_names,
    'coefficient': lr_model.coef_[0],
    'abs_coefficient': np.abs(lr_model.coef_[0])
}).sort_values('abs_coefficient', ascending=False)
```

#### Advanced: XGBoost
```python
import xgboost as xgb

# Calculate class weight
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

# Train model
xgb_model = xgb.XGBClassifier(
    scale_pos_weight=scale_pos_weight,
    max_depth=5,              # Prevent overfitting
    learning_rate=0.05,       # Slower learning = better generalization
    n_estimators=200,         # Number of trees
    subsample=0.8,            # Row sampling
    colsample_bytree=0.8,     # Column sampling
    min_child_weight=5,       # Minimum samples per leaf
    gamma=0.1,                # Regularization
    random_state=42,
    eval_metric='auc'
)

xgb_model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    early_stopping_rounds=20,
    verbose=10
)

# Feature importance
xgb.plot_importance(xgb_model, max_num_features=20)
```

#### Hybrid Ensemble (Recommended)
```python
# Combine Logistic Regression + XGBoost
# Many banks use this dual approach:
# - Simple model for regulatory reporting & explanation
# - Advanced model for actual decisions

# Get predictions from both models
lr_probs = lr_model.predict_proba(X_test_scaled)[:, 1]
xgb_probs = xgb_model.predict_proba(X_test)[:, 1]

# Ensemble: Weighted average
ensemble_probs = 0.3 * lr_probs + 0.7 * xgb_probs

# Alternative: Stacking (train meta-model on predictions)
from sklearn.ensemble import StackingClassifier

ensemble_model = StackingClassifier(
    estimators=[
        ('lr', lr_model),
        ('xgb', xgb_model)
    ],
    final_estimator=LogisticRegression()
)
```

---

### Step 5: Hyperparameter Tuning

**For XGBoost:**
```python
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV

# Time-based cross-validation
tscv = TimeSeriesSplit(n_splits=3)

# Parameter grid
param_grid = {
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [100, 200, 300],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'min_child_weight': [1, 3, 5]
}

# Grid search
grid_search = GridSearchCV(
    xgb.XGBClassifier(scale_pos_weight=scale_pos_weight),
    param_grid,
    cv=tscv,
    scoring='roc_auc',
    n_jobs=-1,
    verbose=2
)

grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_
```

---

## Model Evaluation Metrics

### 1. Discrimination Metrics (Can Model Separate Good from Bad?)

#### Gini Coefficient
```python
from sklearn.metrics import roc_auc_score

def gini_coefficient(y_true, y_pred_proba):
    """Calculate Gini coefficient from AUC"""
    auc = roc_auc_score(y_true, y_pred_proba)
    gini = 2 * auc - 1
    return gini

# Industry benchmarks:
# Gini 0.30-0.40: Acceptable
# Gini 0.40-0.50: Good
# Gini 0.50-0.60: Very good
# Gini > 0.60: Excellent

gini = gini_coefficient(y_test, y_pred_proba)
print(f"Gini: {gini:.3f}")
```

#### AUC-ROC (Area Under Curve)
```python
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib.pyplot as plt

# Calculate AUC
auc = roc_auc_score(y_test, y_pred_proba)

# Plot ROC curve
fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
plt.figure(figsize=(10, 6))
plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc:.3f})')
plt.plot([0, 1], [0, 1], 'k--', label='Random')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve')
plt.legend()
plt.grid(True)
plt.show()

# Industry benchmarks:
# AUC 0.70-0.75: Acceptable
# AUC 0.75-0.80: Good
# AUC 0.80-0.85: Very good
# AUC > 0.85: Excellent
```

#### KS Statistic (Kolmogorov-Smirnov)
```python
def ks_statistic(y_true, y_pred_proba):
    """Calculate KS statistic"""
    from sklearn.metrics import roc_curve
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    ks = max(tpr - fpr)
    return ks

ks = ks_statistic(y_test, y_pred_proba)
print(f"KS Statistic: {ks:.3f}")

# Industry benchmarks:
# KS > 0.20: Acceptable
# KS > 0.30: Good
# KS > 0.40: Very good
# KS > 0.50: Excellent
```

---

### 2. Calibration Metrics (Are Predicted Probabilities Accurate?)

#### Calibration Plot
```python
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt

# Calculate calibration curve
prob_true, prob_pred = calibration_curve(y_test, y_pred_proba, n_bins=10)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(prob_pred, prob_true, marker='o', label='Model')
plt.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')
plt.xlabel('Predicted Probability')
plt.ylabel('Actual Default Rate')
plt.title('Calibration Plot')
plt.legend()
plt.grid(True)
plt.show()
```

#### Hosmer-Lemeshow Test
```python
def hosmer_lemeshow_test(y_true, y_pred_proba, n_bins=10):
    """
    Hosmer-Lemeshow goodness of fit test
    H0: Model is well calibrated
    p-value > 0.05 → Model is well calibrated
    """
    from scipy.stats import chi2

    # Create bins
    bins = np.percentile(y_pred_proba, np.linspace(0, 100, n_bins + 1))
    bins[-1] += 0.0001  # Ensure last bin includes maximum value

    # Assign observations to bins
    bin_indices = np.digitize(y_pred_proba, bins[1:])

    # Calculate observed and expected
    chi_square = 0
    for i in range(n_bins):
        mask = bin_indices == i
        observed = y_true[mask].sum()
        expected = y_pred_proba[mask].sum()
        n = mask.sum()

        if n > 0 and expected > 0:
            chi_square += (observed - expected) ** 2 / (expected * (1 - expected / n))

    # p-value
    p_value = 1 - chi2.cdf(chi_square, n_bins - 2)

    return chi_square, p_value

chi_sq, p_val = hosmer_lemeshow_test(y_test, y_pred_proba)
print(f"Hosmer-Lemeshow: χ²={chi_sq:.3f}, p-value={p_val:.3f}")
print(f"Well calibrated: {p_val > 0.05}")
```

---

### 3. Business Metrics

#### Approval Rate Analysis
```python
def analyze_approval_rate(y_true, y_pred_proba, threshold=0.5):
    """
    Analyze approval rate and bad rate at different thresholds
    """
    results = []

    for thresh in np.arange(0.1, 0.9, 0.05):
        approved = y_pred_proba < thresh

        approval_rate = approved.mean()
        bad_rate = y_true[approved].mean() if approved.sum() > 0 else 0
        volume = approved.sum()

        results.append({
            'threshold': thresh,
            'approval_rate': approval_rate,
            'bad_rate': bad_rate,
            'volume': volume
        })

    return pd.DataFrame(results)

# Analyze
approval_analysis = analyze_approval_rate(y_test, y_pred_proba)

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

ax1.plot(approval_analysis['threshold'], approval_analysis['approval_rate'])
ax1.set_xlabel('Score Threshold')
ax1.set_ylabel('Approval Rate')
ax1.set_title('Approval Rate by Threshold')
ax1.grid(True)

ax2.plot(approval_analysis['approval_rate'], approval_analysis['bad_rate'])
ax2.set_xlabel('Approval Rate')
ax2.set_ylabel('Bad Rate')
ax2.set_title('Bad Rate by Approval Rate')
ax2.grid(True)
plt.show()
```

#### Profit Optimization
```python
def calculate_profit(y_true, y_pred_proba, threshold,
                    revenue_per_good=1000, loss_per_bad=5000):
    """
    Calculate expected profit at given threshold
    """
    approved = y_pred_proba < threshold

    # True Positives (correctly approved good customers)
    tp = ((approved) & (y_true == 0)).sum()

    # False Positives (incorrectly approved bad customers)
    fp = ((approved) & (y_true == 1)).sum()

    # Calculate profit
    profit = tp * revenue_per_good - fp * loss_per_bad

    return profit, tp, fp

# Find optimal threshold
thresholds = np.arange(0.1, 0.9, 0.01)
profits = [calculate_profit(y_test, y_pred_proba, t)[0] for t in thresholds]
optimal_threshold = thresholds[np.argmax(profits)]

print(f"Optimal threshold: {optimal_threshold:.3f}")
print(f"Maximum profit: {max(profits):,.0f}")
```

---

### 4. Model Monitoring Metrics

#### Population Stability Index (PSI)
```python
def calculate_psi(expected, actual, n_bins=10):
    """
    Calculate Population Stability Index

    PSI < 0.10: No significant shift
    PSI 0.10-0.25: Moderate shift - investigate
    PSI > 0.25: Significant shift - retrain model
    """
    # Create bins based on expected distribution
    breakpoints = np.percentile(expected, np.linspace(0, 100, n_bins + 1))
    breakpoints[-1] += 0.0001

    # Calculate distribution for expected and actual
    expected_percents = np.histogram(expected, breakpoints)[0] / len(expected)
    actual_percents = np.histogram(actual, breakpoints)[0] / len(actual)

    # Avoid division by zero
    expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
    actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)

    # Calculate PSI
    psi = np.sum((actual_percents - expected_percents) *
                 np.log(actual_percents / expected_percents))

    return psi

# Monitor PSI over time
psi_score_train_val = calculate_psi(y_train_proba, y_val_proba)
psi_score_train_test = calculate_psi(y_train_proba, y_test_proba)

print(f"PSI (train vs val): {psi_score_train_val:.3f}")
print(f"PSI (train vs test): {psi_score_train_test:.3f}")
```

---

## Regulatory & Risk Management

### Basel II/III Requirements

#### PD (Probability of Default)
```python
# Must estimate 12-month PD for each customer
# Model output = PD estimate

# Calibrate model to long-run average default rate
long_run_default_rate = 0.05  # 5% from historical data

# Scale model scores to match long-run average
from sklearn.calibration import CalibratedClassifierCV

calibrated_model = CalibratedClassifierCV(base_model, method='isotonic', cv=3)
calibrated_model.fit(X_train, y_train)
pd_estimates = calibrated_model.predict_proba(X_test)[:, 1]
```

#### LGD (Loss Given Default)
```python
# For defaulted loans, estimate recovery rate
# LGD = 1 - Recovery Rate

# Example: Build LGD model on defaulted loans
defaulted_loans = df[df['credit_status'].isin(['005', '006', '007', '008'])]
defaulted_loans['lgd'] = 1 - (
    defaulted_loans['recovered_amount'] / defaulted_loans['exposure_at_default']
)

# LGD model (regression on defaulted population)
lgd_model = RandomForestRegressor()
lgd_model.fit(X_defaulted, defaulted_loans['lgd'])
```

#### EAD (Exposure at Default)
```python
# Estimate outstanding balance at time of default
# For credit cards/overdrafts: use Credit Conversion Factor (CCF)

df['ead'] = df['outstanding_balance'] + df['ccf'] * df['undrawn_limit']
```

#### Expected Loss
```python
# Expected Loss = PD × LGD × EAD
df['expected_loss'] = df['pd'] * df['lgd'] * df['ead']

# Portfolio expected loss
total_expected_loss = df['expected_loss'].sum()
```

---

### Model Validation Requirements

#### Backtesting
```python
def backtest_model(df, model, features, target='target', score_col='score'):
    """
    Compare predicted vs actual default rates over time
    """
    df[score_col] = model.predict_proba(df[features])[:, 1]

    # Create score bands
    df['score_band'] = pd.qcut(df[score_col], q=10, labels=False, duplicates='drop')

    # Calculate predicted vs actual by band
    backtest = df.groupby('score_band').agg({
        score_col: 'mean',
        target: 'mean',
        'id': 'count'
    }).rename(columns={score_col: 'predicted_pd', target: 'actual_pd', 'id': 'volume'})

    # Plot
    plt.figure(figsize=(12, 6))
    x = range(len(backtest))
    plt.plot(x, backtest['predicted_pd'], marker='o', label='Predicted PD')
    plt.plot(x, backtest['actual_pd'], marker='s', label='Actual PD')
    plt.xlabel('Score Band (0=Best, 9=Worst)')
    plt.ylabel('Default Rate')
    plt.title('Backtesting: Predicted vs Actual Default Rates')
    plt.legend()
    plt.grid(True)
    plt.show()

    return backtest
```

#### Stress Testing
```python
def stress_test_model(df, model, features, scenarios):
    """
    Test model under economic stress scenarios

    Example scenarios:
    - Recession: Unemployment +5%, GDP -3%
    - Housing crisis: Property values -30%
    - Income shock: Salaries -10%
    """
    results = {}

    for scenario_name, adjustments in scenarios.items():
        df_stressed = df.copy()

        # Apply scenario adjustments
        for feature, adjustment in adjustments.items():
            if feature in df_stressed.columns:
                df_stressed[feature] = df_stressed[feature] * (1 + adjustment)

        # Predict under stress
        stressed_pd = model.predict_proba(df_stressed[features])[:, 1]

        results[scenario_name] = {
            'avg_pd': stressed_pd.mean(),
            'median_pd': np.median(stressed_pd),
            'pct_high_risk': (stressed_pd > 0.5).mean()
        }

    return pd.DataFrame(results).T

# Define scenarios
scenarios = {
    'Baseline': {},
    'Mild Recession': {'gross_salary': -0.05, 'outstanding_debt_main': 0.10},
    'Severe Recession': {'gross_salary': -0.15, 'outstanding_debt_main': 0.25},
    'Income Crisis': {'gross_salary': -0.20}
}

stress_results = stress_test_model(df_test, model, feature_names, scenarios)
print(stress_results)
```

---

### Model Documentation Template

```markdown
# Credit Scoring Model Documentation

## 1. Executive Summary
- Model purpose: [Predict probability of default for consumer loans]
- Model type: [XGBoost Classifier]
- Performance: [Gini = 0.52, AUC = 0.76]
- Status: [Production / Development]

## 2. Data Sources
### 2.1 Credit Bureau (MKR)
- Source: scoring.qnb_mkr_data_mba_backup
- Coverage: 2018-2021
- Records: 96,327 loans
- Update frequency: Daily

### 2.2 Income Verification (ASAN Finance)
- Source: ibs.asan_finance_is_yeri_v2@ibs_ro
- Coverage: Employment and salary data
- Update frequency: Monthly

## 3. Target Variable Definition
- Definition: Customer reached 90+ DPD within 12 months of origination
- Performance window: 12 months
- Bad rate: 4.2%

## 4. Feature Engineering
### 4.1 Payment History Features (15 features)
- [List all features with definitions]

### 4.2 Utilization Features (8 features)
- [List all features with definitions]

[... continue for all feature groups]

## 5. Model Development
### 5.1 Model Selection
- Baseline: Logistic Regression (Gini = 0.45)
- Champion: XGBoost (Gini = 0.52)

### 5.2 Training Approach
- Training period: 2018-2019
- Validation period: 2020
- Test period: 2021

### 5.3 Hyperparameters
- max_depth: 5
- learning_rate: 0.05
- n_estimators: 200
[... all parameters]

## 6. Model Performance
### 6.1 Discrimination
- Gini: 0.52
- AUC: 0.76
- KS: 0.42

### 6.2 Calibration
- Hosmer-Lemeshow p-value: 0.34 (well calibrated)

### 6.3 Business Metrics
- At 80% approval rate: 3.1% bad rate
- At 70% approval rate: 2.3% bad rate

## 7. Model Limitations
- Does not capture macro-economic shocks
- Limited data on self-employed customers
- Regional coverage gaps in rural areas

## 8. Monitoring Plan
- Monthly PSI calculation
- Quarterly performance review
- Annual model retraining
- Champion/Challenger testing framework

## 9. Override Policy
- Override authority: Credit Manager
- Documentation requirements: [specify]
- Monthly override review

## 10. Approval & Sign-off
- Model Developer: [Name, Date]
- Model Validator: [Name, Date]
- Risk Manager: [Name, Date]
- Chief Risk Officer: [Name, Date]
```

---

## Common Pitfalls to Avoid

### 1. Data Leakage (MOST COMMON ERROR!)

**❌ Using Future Information:**
```python
# WRONG: Using information not available at decision time
df['max_dpd_ever'] = df.groupby('customer_id')['days_past_due'].max()
# This includes FUTURE delinquencies after loan origination!

# CORRECT: Only use past information (point-in-time)
df['max_dpd_before_application'] = df[
    df['date'] < df['application_date']
].groupby('customer_id')['days_past_due'].max()
```

**❌ Using Target-Related Variables:**
```python
# WRONG: Using variables that directly indicate the target
features = ['outstanding_balance', 'final_loan_status']  # final_loan_status = leakage!

# CORRECT: Only use variables available before outcome
features = ['initial_amount', 'income', 'previous_payment_history']
```

**❌ Mixing Vintage Populations:**
```python
# WRONG: Mixing loans with different maturity
train = df  # Contains 2018 loans (3 years mature) and 2021 loans (0 years mature)

# CORRECT: Ensure adequate performance window
train = df[df['granted_on'] < '2020-01-01']  # All have 2+ years maturity
```

---

### 2. Overfitting

**Signs of Overfitting:**
```python
# Large gap between train and test performance
Train AUC: 0.95
Test AUC:  0.65   # 30% drop = severe overfitting!

# Too many features
num_features = 150
num_samples = 1000
# Rule of thumb: features < samples / 10
```

**Solutions:**

```python
# 1. Regularization
from sklearn.linear_model import LogisticRegression
model = LogisticRegression(C=0.1)  # Stronger regularization (smaller C)

# 2. Feature selection
from sklearn.feature_selection import SelectKBest, f_classif
selector = SelectKBest(f_classif, k=30)  # Keep top 30 features
X_selected = selector.fit_transform(X, y)

# 3. Cross-validation
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5, scoring='roc_auc')
print(f"CV AUC: {scores.mean():.3f} (+/- {scores.std():.3f})")

# 4. Early stopping (for XGBoost)
model.fit(X_train, y_train,
          eval_set=[(X_val, y_val)],
          early_stopping_rounds=20)

# 5. Limit model complexity
xgb_model = xgb.XGBClassifier(
    max_depth=3,          # Shallow trees
    min_child_weight=10,  # More samples per leaf
    gamma=0.5            # Higher regularization
)
```

---

### 3. Ignoring Temporal Drift

**The Problem:**
```python
# Model trained on pre-COVID data (2018-2019)
# Applied to post-COVID customers (2021-2023)
# Customer behavior has fundamentally changed!
```

**Detection:**
```python
# Monitor PSI (Population Stability Index)
psi_monthly = []
for month in range(12):
    actual_scores = df[df['month'] == month]['score']
    psi = calculate_psi(train_scores, actual_scores)
    psi_monthly.append(psi)

# Plot PSI over time
plt.plot(psi_monthly)
plt.axhline(y=0.10, color='orange', linestyle='--', label='Moderate drift')
plt.axhline(y=0.25, color='red', linestyle='--', label='Severe drift')
plt.xlabel('Month')
plt.ylabel('PSI')
plt.title('Population Stability Index Over Time')
plt.legend()
plt.show()

# If PSI > 0.25: RETRAIN MODEL IMMEDIATELY
```

**Solutions:**
```python
# 1. Regular retraining schedule
# Retrain quarterly or when PSI > 0.10

# 2. Champion/Challenger framework
# Always have a newer model testing against production model

# 3. Adaptive models
# Use online learning or model updating techniques

# 4. Drift detection alerts
def check_drift(production_scores, training_scores, threshold=0.10):
    psi = calculate_psi(training_scores, production_scores)
    if psi > threshold:
        send_alert(f"Model drift detected! PSI = {psi:.3f}")
```

---

### 4. Poor Feature Engineering

**❌ Using Raw Features:**
```python
# WRONG: Using raw values without transformation
features = ['age', 'income', 'loan_amount']
# Age 25 vs 26 treated as same difference as 65 vs 66

# CORRECT: Create meaningful transformations
df['age_group'] = pd.cut(df['age'], bins=[18, 25, 35, 45, 55, 100])
df['log_income'] = np.log1p(df['income'])  # Handle skewness
df['loan_to_income'] = df['loan_amount'] / df['income']  # Ratio
```

**❌ Ignoring Domain Knowledge:**
```python
# WRONG: Pure automated feature selection
selector = SelectKBest(k=20)
features_selected = selector.fit_transform(X, y)
# May drop important business-relevant features!

# CORRECT: Combine statistical selection with business logic
business_critical = ['payment_history', 'dti_ratio', 'credit_utilization']
statistical_selection = selector.get_feature_names_out()
final_features = list(set(business_critical + list(statistical_selection)))
```

---

### 5. Incorrect Performance Evaluation

**❌ Using Accuracy for Imbalanced Data:**
```python
# WRONG: Accuracy is misleading for imbalanced data
accuracy = (y_pred == y_test).mean()
# 95% accuracy by predicting everyone as "good"!

# CORRECT: Use appropriate metrics
from sklearn.metrics import roc_auc_score, precision_recall_curve
auc = roc_auc_score(y_test, y_pred_proba)
precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
```

**❌ Not Considering Business Costs:**
```python
# WRONG: Optimizing for AUC only
threshold = 0.5  # Default threshold

# CORRECT: Optimize for business profit
# False Positive (approve bad): Cost = 5000
# False Negative (reject good): Cost = 1000 (lost revenue)

def business_profit(threshold):
    approved = y_pred_proba < threshold
    tp = ((approved) & (y_test == 0)).sum() * 1000
    fp = ((approved) & (y_test == 1)).sum() * (-5000)
    return tp + fp

# Find threshold that maximizes profit
optimal_threshold = max(thresholds, key=business_profit)
```

---

## Recommendations for Your Model

### What You Have ✓

Based on your `raw_data.sql` extraction:

```sql
✓ Credit bureau data (MKR):
  - Payment history (OVERDUE_DAYS, DAYS_MAIN_SUM_OVERDUE)
  - Credit status (CREDIT_STATUS)
  - Loan details (INITIAL_AMOUNT, OUTSTANDING_DEBT_MAIN)
  - Account information (GRANTED_ON, CONTRACT_DUE_ON)

✓ Income data (ASAN Finance):
  - Verified salary (GROSS_SALARY)
  - Employer information (EMPLOYER_VOEN)
  - Employment history (SALARY_UPDATE_DATE)

✓ Demographics:
  - Age (DATE_OF_BIRTH)
  - Education (EDUCATION)
  - Marital status (MARITAL_STATUS)
  - Region (RESIDENT_REGION)

✓ Loan characteristics:
  - Credit type (CREDIT_TYPE, CREDIT_TYPE_NAME)
  - Purpose (CREDIT_PURPOSE, CREDIT_PURPOSE_NAME)
  - Collateral (COLLATERAL_CODE, COLLATERAL_MARKET_VALUE)
  - Bank (BANK_ID, BANK_NAME)

✓ Time period:
  - 2018-2021 (3 years) ✓ GOOD
  - 96,327 loans ✓ GOOD SAMPLE SIZE
```

### Priority Features to Engineer

**Tier 1 - Critical (Implement First):**
```python
# 1. Payment behavior features
- max_dpd_ever
- max_dpd_12m
- num_30dpd_12m
- num_60dpd_12m
- num_90dpd_12m

# 2. Utilization features
- utilization_rate = outstanding / line_amount
- dti_ratio = outstanding / (salary * 12)
- pti_ratio = monthly_payment / salary

# 3. Credit vintage
- months_since_first_loan
- num_active_loans
- num_loan_types
```

**Tier 2 - Important (Implement Second):**
```python
# 4. Aggregated features
- total_outstanding_all_loans
- avg_utilization_all_loans
- portfolio_max_dpd

# 5. Loan-specific
- ltv_ratio = loan_amount / collateral_value
- loan_to_income = initial_amount / annual_salary

# 6. Trend features
- payment_improving_trend
- balance_growth_rate_6m
```

### Recommended Model Architecture

```python
# Phase 1: Baseline (Week 1)
baseline_model = LogisticRegression(class_weight='balanced')
# Target: Gini > 0.40

# Phase 2: Advanced (Week 2)
xgb_model = XGBClassifier(
    scale_pos_weight=scale_pos_weight,
    max_depth=5,
    learning_rate=0.05,
    n_estimators=200
)
# Target: Gini > 0.50

# Phase 3: Ensemble (Week 3)
ensemble_predictions = 0.3 * lr_probs + 0.7 * xgb_probs
# Target: Gini > 0.52
```

### Validation Strategy

```python
# Time-based split (REQUIRED)
train_data = df[df['granted_on'] < '2020-01-01']  # 2018-2019
val_data   = df[(df['granted_on'] >= '2020-01-01') &
                (df['granted_on'] < '2021-01-01')]  # 2020
test_data  = df[df['granted_on'] >= '2021-01-01']  # 2021

# Expected performance with your data:
# Gini: 0.45-0.55 (typical for emerging markets)
# AUC: 0.72-0.77
```

### Success Criteria

```python
✓ Model Performance:
  - Gini > 0.45 (acceptable)
  - Gini > 0.50 (good)
  - Well-calibrated (Hosmer-Lemeshow p > 0.05)

✓ Business Metrics:
  - At 75% approval rate: Bad rate < 4%
  - At 80% approval rate: Bad rate < 5%

✓ Stability:
  - PSI (train vs test) < 0.10
  - Similar performance across quarters

✓ Documentation:
  - Feature definitions documented
  - Model validation report completed
  - Monitoring plan established
```

---

## Next Steps

1. **Extract raw data** (3-5 minutes)
   ```bash
   sqlplus username/password@database
   @scripts/raw_data.sql
   ```

2. **Create features in Python** (30-60 minutes)
   - Implement Tier 1 features first
   - Validate feature logic
   - Handle missing values

3. **Train baseline model** (15 minutes)
   - Logistic Regression
   - Get baseline Gini
   - Understand feature importance

4. **Train advanced model** (30 minutes)
   - XGBoost with hyperparameter tuning
   - Compare with baseline
   - Create ensemble

5. **Validate & document** (2-3 hours)
   - Out-of-time validation
   - Backtesting
   - Create model documentation
   - Prepare for regulatory review

---

## Learning Resources

### Books
1. **"Credit Risk Scorecards" by Naeem Siddiqi**
   - Industry standard reference
   - Practical implementation guide
   - WOE and scorecard development

2. **"Intelligent Credit Scoring" by Steven Finlay**
   - Modern machine learning approaches
   - Feature engineering techniques
   - Regulatory considerations

3. **"The Credit Scoring Toolkit" by Raymond Anderson**
   - Statistical foundations
   - Model validation
   - Business implementation

### Online Resources
1. **Basel Committee on Banking Supervision**
   - Basel II/III guidelines
   - IRB approach documentation
   - Risk management standards

2. **FICO Score Methodology**
   - Public documentation
   - Industry best practices
   - Feature importance insights

3. **European Banking Authority (EBA)**
   - Credit risk guidelines
   - Model validation standards
   - Stress testing frameworks

### Practical Learning
1. **Kaggle Competitions**
   - Home Credit Default Risk
   - American Express Default Prediction
   - LendingClub Loan Data

2. **Academic Papers**
   - "Super learner for credit scoring"
   - "Deep learning for credit risk"
   - "Explainable AI in credit scoring"

---

**Document Created:** 2025-12-03
**Author:** Claude Code
**Version:** 1.0
**Related Documents:**
- `docs/SQL_OPTIMIZATION_REPORT.md` - Database optimization
- `docs/RAW_DATA_EXTRACTION_GUIDE.md` - Data extraction guide
- `scripts/raw_data.sql` - Raw data extraction script
