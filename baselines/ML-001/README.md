# ML-001: End-to-End ML Pipeline for Time Series Prediction

[English](#english) | [日本語](#japanese)

---

<a id="english"></a>
## English

## Overview

This is a reference implementation for the ML-001 problem: End-to-End ML Pipeline for Time Series Prediction with automated hyperparameter optimization, A/B testing, and model drift detection.

## Problem Requirements

### Functional Requirements (MUST)
- **MUST** implement time series preprocessing (imputation, normalization, windowing)
- **MUST** support multiple algorithms: ARIMA, LSTM, XGBoost
- **MUST** implement hyperparameter optimization using Optuna
- **MUST** provide REST API for model serving and predictions
- **MUST** implement A/B testing with traffic splitting
- **MUST** support model versioning and rollback
- **MUST** implement automated retraining pipeline
- **MUST** provide comprehensive metrics and monitoring

### Non-Functional Requirements
- **MUST** achieve <100ms prediction latency for batch size 100
- **MUST** handle 1000 prediction requests per second
- **MUST** support 500 concurrent users
- **MUST** achieve <5% MAPE (Mean Absolute Percentage Error)

## Implementation Details

### Technology Stack
- **Language**: Python 3.11
- **ML Frameworks**: scikit-learn, TensorFlow/Keras, XGBoost
- **Optimization**: Optuna for hyperparameter tuning
- **Serving**: FastAPI with Uvicorn
- **Monitoring**: MLflow + Prometheus metrics
- **Testing**: pytest with ML-specific test cases

### Project Structure
```
ML-001/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── data/
│   │   ├── __init__.py
│   │   ├── preprocessing.py # Data preprocessing pipeline
│   │   ├── feature_engineering.py # Time series features
│   │   └── validation.py    # Data validation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── arima_model.py   # ARIMA implementation
│   │   ├── lstm_model.py    # LSTM neural network
│   │   ├── xgboost_model.py # XGBoost regressor
│   │   ├── base_model.py    # Abstract base model
│   │   └── ensemble.py      # Model ensemble methods
│   ├── serving/
│   │   ├── __init__.py
│   │   ├── api.py           # REST API endpoints
│   │   ├── predictor.py     # Prediction service
│   │   └── ab_testing.py    # A/B testing framework
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── metrics.py       # Performance metrics
│   │   ├── drift_detection.py # Model drift detection
│   │   └── alerts.py        # Alert management
│   └── training/
│       ├── __init__.py
│       ├── trainer.py       # Model training orchestration
│       ├── hyperopt.py      # Hyperparameter optimization
│       └── pipeline.py      # Training pipeline
├── tests/
│   ├── unit/
│   │   ├── test_preprocessing.py
│   │   ├── test_models.py
│   │   └── test_serving.py
│   ├── integration/
│   │   ├── test_pipeline.py
│   │   └── test_api.py
│   └── performance/
│       └── test_latency.py
├── test_data/
│   ├── time_series_train.csv
│   ├── time_series_test.csv
│   └── model_config.json
├── config/
│   └── ml_config.yaml
├── models/
│   └── model_registry.json
├── Dockerfile
├── requirements.txt
└── README.md
```

## Expected Performance Metrics

Expected scores for this baseline:
- **Functional Coverage**: 100% (all MUST requirements)
- **Test Pass Rate**: 90% (comprehensive ML test suite)
- **Performance**: 85% (meets latency and throughput requirements)
- **Code Quality**: 80% (clean, maintainable ML code)
- **Security**: 75% (API security and input validation)
- **Total Score: 86%** (Gold)

## API Endpoints

### Prediction API
```bash
POST /predict
Content-Type: application/json

{
  "data": [[timestamp, value, feature1, feature2], ...],
  "model_version": "v1.2",
  "forecast_horizon": 10
}

Response:
{
  "predictions": [101.2, 102.8, 99.5, ...],
  "confidence_intervals": [[98.1, 104.3], ...],
  "model_version": "v1.2",
  "execution_time_ms": 45
}
```

### A/B Testing API
```bash
POST /ab-test/start
{
  "name": "lstm_vs_xgboost",
  "models": ["lstm_v1.2", "xgboost_v2.1"],
  "traffic_split": [0.5, 0.5],
  "duration_hours": 24
}
```

### Model Management
```bash
GET /models                    # List available models
POST /models/deploy           # Deploy new model version
POST /models/rollback         # Rollback to previous version
```

## Usage Examples

### Training Pipeline
```python
# Train multiple models with hyperparameter optimization
from src.training.trainer import ModelTrainer
from src.training.hyperopt import HyperparameterOptimizer

trainer = ModelTrainer(config_path="config/ml_config.yaml")
optimizer = HyperparameterOptimizer()

# Optimize LSTM model
best_params = optimizer.optimize("lstm", train_data, n_trials=100)
lstm_model = trainer.train_model("lstm", best_params)

# Compare models
results = trainer.compare_models(["arima", "lstm", "xgboost"], test_data)
```

### Serving Predictions
```python
# Start FastAPI server
from src.main import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)

# Make predictions
import requests

response = requests.post("http://localhost:8000/predict", json={
    "data": time_series_data,
    "forecast_horizon": 24
})

predictions = response.json()["predictions"]
```

## References

- [MLOps: Machine Learning Operations](https://ml-ops.org/)
- [Time Series Analysis in Python](https://machinelearningmastery.com/time-series-analysis-python/)
- [Optuna Documentation](https://optuna.org/)
- [MLflow Documentation](https://mlflow.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

<a id="japanese"></a>
## 日本語

# ML-001: 時系列予測のためのエンドツーエンドMLパイプライン

## 概要

ML-001問題のリファレンス実装です：自動ハイパーパラメーター最適化、A/Bテスト、モデルドリフト検出を備えた時系列予測のためのエンドツーエンドMLパイプラインです。

## 問題要件

### 機能要件（必須）
- **必須** 時系列前処理の実装（欠損値補間、正規化、ウィンドウ化）
- **必須** 複数アルゴリズムのサポート: ARIMA、LSTM、XGBoost
- **必須** Optunaを使用したハイパーパラメーター最適化の実装
- **必須** モデルサービングと予測のためのREST APIの提供
- **必須** トラフィック分割を伴うA/Bテストの実装
- **必須** モデルバージョニングとロールバックのサポート
- **必須** 自動再トレーニングパイプラインの実装
- **必須** 包括的なメトリクスと監視の提供

### 非機能要件
- **必須** バッチサイズ100で100ms未満の予測レイテンシの達成
- **必須** 1秒あたり1000予測リクエストの処理
- **必須** 500同時ユーザーのサポート
- **必須** 5%未満のMAPE（平均絶対パーセントエラー）の達成

## 実装詳細

### 技術スタック
- **言語**: Python 3.11
- **MLフレームワーク**: scikit-learn、TensorFlow/Keras、XGBoost
- **最適化**: ハイパーパラメーターチューニングのためのOptuna
- **サービング**: Uvicornを使用したFastAPI
- **監視**: MLflow + Prometheusメトリクス
- **テスト**: ML固有のテストケースを含むpytest

### プロジェクト構造
```
ML-001/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリケーションエントリポイント
│   ├── data/
│   │   ├── __init__.py
│   │   ├── preprocessing.py # データ前処理パイプライン
│   │   ├── feature_engineering.py # 時系列特徴
│   │   └── validation.py    # データ検証
│   ├── models/
│   │   ├── __init__.py
│   │   ├── arima_model.py   # ARIMA実装
│   │   ├── lstm_model.py    # LSTMニューラルネットワーク
│   │   ├── xgboost_model.py # XGBoost回帰
│   │   ├── base_model.py    # 抽象ベースモデル
│   │   └── ensemble.py      # モデルアンサンブル手法
│   ├── serving/
│   │   ├── __init__.py
│   │   ├── api.py           # REST APIエンドポイント
│   │   ├── predictor.py     # 予測サービス
│   │   └── ab_testing.py    # A/Bテストフレームワーク
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── metrics.py       # パフォーマンスメトリクス
│   │   ├── drift_detection.py # モデルドリフト検出
│   │   └── alerts.py        # アラート管理
│   └── training/
│       ├── __init__.py
│       ├── trainer.py       # モデルトレーニングオーケストレーション
│       ├── hyperopt.py      # ハイパーパラメーター最適化
│       └── pipeline.py      # トレーニングパイプライン
├── tests/
│   ├── unit/
│   │   ├── test_preprocessing.py
│   │   ├── test_models.py
│   │   └── test_serving.py
│   ├── integration/
│   │   ├── test_pipeline.py
│   │   └── test_api.py
│   └── performance/
│       └── test_latency.py
├── test_data/
│   ├── time_series_train.csv
│   ├── time_series_test.csv
│   └── model_config.json
├── config/
│   └── ml_config.yaml
├── models/
│   └── model_registry.json
├── Dockerfile
├── requirements.txt
└── README.md
```

## 期待パフォーマンス指標

このベースラインの期待スコア:
- **機能カバレッジ**: 100%（全ての必須要件）
- **テスト合格率**: 90%（網羅的MLテストスイート）
- **パフォーマンス**: 85%（レイテンシとスループット要件を満たす）
- **コード品質**: 80%（クリーンで保守性の高いMLコード）
- **セキュリティ**: 75%（APIセキュリティと入力検証）
- **総合スコア: 86%** （ゴールド）

## APIエンドポイント

### 予測API
```bash
POST /predict
Content-Type: application/json

{
  "data": [[timestamp, value, feature1, feature2], ...],
  "model_version": "v1.2",
  "forecast_horizon": 10
}

Response:
{
  "predictions": [101.2, 102.8, 99.5, ...],
  "confidence_intervals": [[98.1, 104.3], ...],
  "model_version": "v1.2",
  "execution_time_ms": 45
}
```

### A/BテストAPI
```bash
POST /ab-test/start
{
  "name": "lstm_vs_xgboost",
  "models": ["lstm_v1.2", "xgboost_v2.1"],
  "traffic_split": [0.5, 0.5],
  "duration_hours": 24
}
```

### モデル管理
```bash
GET /models                    # 利用可能モデル一覧
POST /models/deploy           # 新モデルバージョンデプロイ
POST /models/rollback         # 前バージョンへのロールバック
```

## 使用例

### トレーニングパイプライン
```python
# ハイパーパラメーター最適化で複数モデルをトレーニング
from src.training.trainer import ModelTrainer
from src.training.hyperopt import HyperparameterOptimizer

trainer = ModelTrainer(config_path="config/ml_config.yaml")
optimizer = HyperparameterOptimizer()

# LSTMモデルを最適化
best_params = optimizer.optimize("lstm", train_data, n_trials=100)
lstm_model = trainer.train_model("lstm", best_params)

# モデル比較
results = trainer.compare_models(["arima", "lstm", "xgboost"], test_data)
```

### 予測サービング
```python
# FastAPIサーバー起動
from src.main import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)

# 予測実行
import requests

response = requests.post("http://localhost:8000/predict", json={
    "data": time_series_data,
    "forecast_horizon": 24
})

predictions = response.json()["predictions"]
```

## 参考資料

- [MLOps: Machine Learning Operations](https://ml-ops.org/)
- [Pythonによる時系列分析](https://machinelearningmastery.com/time-series-analysis-python/)
- [Optunaドキュメント](https://optuna.org/)
- [MLflowドキュメント](https://mlflow.org/)
- [FastAPIドキュメント](https://fastapi.tiangolo.com/)