# Predictive Maintenance System
### AI-Based Intelligent System for Performance Modelling of Standalone Systems

A full-stack, real-time predictive maintenance system for standalone Windows PCs. 
Continuously monitors hardware telemetry (CPU, Memory, Disk I/O), runs live 
inference using a lightweight 3-feature XGBoost classifier, and visualizes the 
results on an interactive React dashboard.

The system operates **fully offline** with no cloud dependency, stores all 
telemetry in a local SQLite database, and triggers desktop alerts when high-risk 
states persist.

---

## 🚀 Key Features

- **Real-time Hardware Monitoring:** Polls CPU, Memory, and Disk I/O every second 
  using Python's `psutil` library.
- **AI-Driven 3-Class Risk Classification:** XGBoost model classifies system 
  state as **NORMAL**, **MODERATE**, or **HIGH** with sub-millisecond inference.
- **REST Polling Architecture:** Frontend polls `/predict`, `/history`, `/status`, 
  and `/alerts` every 2 seconds for deterministic data freshness.
- **Persistent Data Logging:** Every metric and prediction is stored in SQLite 
  (`predictive_maintenance.db`) and mirrored to CSV (`live_data_log.csv`).
- **Desktop Notifications:** Triggers native Windows alerts when HIGH risk 
  persists for 30 seconds.
- **Interactive Dashboard:** React + Recharts dashboard with live trends, 
  risk analysis, and fault logs.

---

## 🧠 Model Details

| Property | Value |
|----------|-------|
| Algorithm | XGBoost (multi-class) |
| Features | `cpu_percent`, `memory_percent`, `disk_write_mbps` |
| Classes | NORMAL, MODERATE, HIGH |
| Cross-machine CV accuracy | 99.67% (5-fold GroupKFold) |
| Inference latency | ~2.5 μs |
| Training samples | 1,530 (510 per class) |

---

## 🛠️ Tech Stack

**Backend:** Python 3.12+, FastAPI, Uvicorn, SQLAlchemy, SQLite  
**Frontend:** React.js, Recharts, CSS3  
**ML:** XGBoost, Scikit-learn, Pandas, joblib

---

## 📁 Project Structure

```text
Predictive-maintenance_2/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI server + collector + prediction
│   │   ├── models.py               # SQLAlchemy schema
│   │   ├── schemas.py              # Pydantic models
│   │   ├── database.py             # SQLite connection
│   │   ├── xgboost_model.pkl       # Trained v2 model
│   │   ├── scaler.pkl              # StandardScaler
│   │   └── label_encoder.pkl       # Class label mapping
│   └── requirements.txt
├── DataCollector/                  # Data collection + training scripts
│   ├── datasets_v2/                # Clean 3-feature training data
│   ├── models_v2/                  # Trained v2 model artifacts
│   ├── retrain_v2_fixed.py         # Retraining script
│   └── final_training_data_3class.csv
├── frontend/                       # React dashboard
├── testing/                        # Automated test framework
│   ├── run_tests.py                # NORMAL/MODERATE/HIGH test runner
│   ├── master_results.csv          # Cross-hardware results
│   └── watch.py                    # Live prediction monitor
└── .gitignore
