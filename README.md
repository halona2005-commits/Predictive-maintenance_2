# Predictive Maintenance System
### AI-Based Intelligent System for Performance Modelling of Standalone Systems

This project is a full-stack, real-time predictive maintenance system designed specifically for standalone Windows PCs. It continuously monitors hardware metrics (CPU, Memory, Disk, SSD health), runs live inference using a lightweight XGBoost AI model, and visualizes the data on an interactive React dashboard. 

The system operates entirely offline with no cloud dependency, making it ideal for local, high-privacy environments. It saves all telemetry data to a local SQLite database for historical reporting, and to a CSV file for easy data extraction and backup.

---

## 🚀 Key Features

- **Real-time Hardware Monitoring:** Uses Python's `psutil` library to poll CPU, Memory, Disk I/O, Process Count, and SSD S.M.A.R.T. attributes at a 1-second interval.
- **AI-Driven Fault Prediction:** Uses a benchmarked, deployed XGBoost model to output binary predictions (0 = Normal, 1 = Anomaly) with sub-millisecond latency.
- **Live WebSocket Streaming:** Pushes real-time data to the frontend over a robust WebSocket connection (every 1 second).
- **Persistent Data Logging:** Stores every metric and prediction in an SQLite database (`predictive_maintenance.db`) and a flat CSV file (`live_data_log.csv`).
- **Desktop Notifications:** Automatically triggers system alerts when a High or Critical risk condition persists for 30 seconds.
- **Interactive Dashboard:** Built with React.js and Chart.js, providing live trends, AI model votes, risk analysis, and historical fault logs.

---

## 🛠️ Tech Stack

**Backend:** Python 3.11, FastAPI, Uvicorn, SQLAlchemy, SQLite
**Frontend:** React.js, Recharts, CSS3
**Machine Learning:** XGBoost, Scikit-learn, Pandas

---

## 📁 Project Structure

```text
Predictive-maintenance2/
├── backend/
│   ├── app/
│   │   ├── main.py              # Main FastAPI + WebSocket server
│   │   ├── models.py            # SQLAlchemy database schema
│   │   ├── schemas.py           # Pydantic data validation models
│   │   ├── database.py          # DB connection setup
│   │   ├── xgboost_model.pkl    # Trained AI model
│   │   └── scaler.pkl           # Trained data scaler
│   ├── .env                     # Environment variables (SYSTEM_ID)
│   ├── predictive_maintenance.db # Live SQLite database
│   ├── live_data_log.csv        # Live CSV backup log
│   └── requirements.txt         # Python dependencies
├── frontend/                    # React dashboard source code
├── venv/                        # Python virtual environment
└── .gitignore                   # Git ignore rules

Set up for backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

Set up for frontend
cd frontend
npm install
npm start
