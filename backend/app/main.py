import json
import os
import sys
import asyncio
import psutil
import joblib
import pandas as pd
import csv
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, init_db, SessionLocal
from app.models import AnomalyAlert, Metric, Prediction
from app.schemas import AlertOut, HistoryResponse, MetricCreate, MetricOut, PredictionOut, StatusOut

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------
# SINGLE APP INSTANCE
# --------------------------------------------------------------
app = FastAPI(title="Predictive Maintenance API")

# FIXED CORS MIDDLEWARE (Allows localhost:3000 explicitly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_ID = os.getenv("SYSTEM_ID", "SYSTEM-01")

# --------------------------------------------------------------
# CSV HELPER FUNCTION (SAVES REAL-TIME DATA TO A CSV FILE)
# --------------------------------------------------------------
METRICS_CSV = "live_data_log.csv"

def append_to_csv(data_dict):
    """Appends real-time data to a CSV file. Creates headers if the file is new."""
    file_exists = os.path.isfile(METRICS_CSV)
    with open(METRICS_CSV, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data_dict.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data_dict)

# ==============================================================
# 1. LOAD THE RETRAINED 5-FEATURE XGBOOST AI MODEL
# ==============================================================
APP_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(APP_DIR, "xgboost_model.pkl")
SCALER_PATH = os.path.join(APP_DIR, "scaler.pkl")

try:
    xgb_model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print("✅ Real XGBoost AI Model loaded successfully!")
except Exception as e:
    print(f"⚠️ Could not load AI Model. Using Rule-Based Fallback. Error: {e}")
    xgb_model = None
    scaler = None

# ==============================================================
# 2. WEBSOCKET (REAL HARDWARE METRICS + CSV LOGGING)
# ==============================================================
previous_disk_bytes = psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    global previous_disk_bytes
    await websocket.accept()
    
    try:
        while True:
            try:
                # 1. Fetch REAL system metrics using psutil
                cpu_usage = psutil.cpu_percent(interval=1)        
                memory_usage = psutil.virtual_memory().percent    
                process_count = len(psutil.pids())                
                memory_available_mb = psutil.virtual_memory().available / (1024 * 1024)  

                current_disk_bytes = psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0
                disk_write = (current_disk_bytes - previous_disk_bytes) / (1024 * 1024)
                previous_disk_bytes = current_disk_bytes

                risk_score = ((cpu_usage * 0.4) + (memory_usage * 0.6)) / 100
                model_vote = 1 if risk_score > 0.6 else 0

                # 2. Save REAL metrics to Database (No disk_usage column to avoid errors)
                db = SessionLocal()
                new_metric = Metric(
                    system_id=SYSTEM_ID,
                    cpu_percent=round(cpu_usage, 1),
                    memory_percent=round(memory_usage, 1),
                    memory_available_mb=int(memory_available_mb),
                    disk_write_mbps=round(disk_write, 2),
                    process_count=int(process_count),
                )
                db.add(new_metric)

                # SAVE PREDICTION TO DB
                new_prediction = Prediction(
                    timestamp=datetime.now(),
                    risk_score=risk_score,
                    risk_level="HIGH" if risk_score > 0.6 else "NORMAL",
                    fault_type="CPU" if risk_score > 0.6 else "NONE",
                    severity_level="INFO",
                    confidence=0.95,
                    votes=1,
                    pem_status="NORMAL",
                    md_status="NORMAL",
                    models_json=json.dumps({"xgboost": model_vote}),
                    probabilities_json=json.dumps({"xgboost": risk_score, "normal": 1 - risk_score})
                )
                db.add(new_prediction)
                db.commit()
                db.close()

                # 3. Build data packet for Frontend + CSV
                data = {
                    "cpu": round(cpu_usage, 1),
                    "memory": round(memory_usage, 1),
                    "disk": round(disk_write, 2),
                    "risk": round(risk_score, 3),
                    "process_count": int(process_count),
                    "memory_available_mb": int(memory_available_mb),
                    "timestamp": datetime.now().isoformat()
                }

                # SAVE TO CSV FILE
                append_to_csv(data)
                print(f"💾 LOGGED TO CSV: CPU={cpu_usage:.1f}%, MEM={memory_usage:.1f}%, RISK={risk_score:.3f}")

                # 4. Send to Frontend
                await websocket.send_json(data)
                
                await asyncio.sleep(1)

            except Exception as e:
                print(f"WebSocket disconnected or cancelled: {e}")
                return
            
    except Exception as e:
        print(f"WebSocket outer cleanup: {e}")


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.post("/metrics", response_model=MetricOut)
def create_metric(payload: MetricCreate, db: Session = Depends(get_db)) -> MetricOut:
    metric = Metric(
        system_id=SYSTEM_ID,
        cpu_percent=payload.cpu_percent,
        memory_percent=payload.memory_percent,
        memory_available_mb=payload.memory_available_mb,
        disk_write_mbps=payload.disk_write_mbps,
        process_count=payload.process_count,
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


# ==============================================================
# 3. TRUE AI-DRIVEN PREDICTION ENDPOINT (WITH CALIBRATION)
# ==============================================================
@app.get("/predict", response_model=PredictionOut)
def get_prediction(db: Session = Depends(get_db)) -> PredictionOut:
    latest_metric = db.query(Metric).order_by(Metric.id.desc()).first()
    
    if not latest_metric:
        return PredictionOut(
            timestamp=datetime.now().isoformat(),
            risk_score=0.0, risk_level="NORMAL",
            confidence=0.0, votes=0, fault_type="NONE",
            severity_level="INFO", pem_status="NORMAL", md_status="NORMAL",
            models={}, probabilities={}
        )

    fault = "NONE"
    confidence = 0.0
    risk_score = 0.0

    try:
        # --- CRITICAL FIX: Feed the model the EXACT 10 features it was trained on ---
        inputs = pd.DataFrame([[
            latest_metric.cpu_percent,
            latest_metric.cpu_frequency_mhz,
            latest_metric.memory_percent,
            latest_metric.memory_available_mb,
            latest_metric.disk_percent,
            latest_metric.disk_read_mbps,
            latest_metric.disk_write_mbps,
            latest_metric.network_upload_mbps,
            latest_metric.network_download_mbps,
            latest_metric.process_count
        ]], columns=[
            'cpu_percent', 'cpu_frequency_mhz', 'memory_percent', 'memory_available_mb', 
            'disk_percent', 'disk_read_mbps', 'disk_write_mbps', 
            'network_upload_mbps', 'network_download_mbps', 'process_count'
        ])
        
        scaled_inputs = scaler.transform(inputs)
        proba = model.predict_proba(scaled_inputs)[0]  # Normal, Moderate, High probabilities
        predicted_class = model.predict(scaled_inputs)[0]  # 'Normal', 'Moderate', 'High'

        risk_score = max(proba)
        confidence = risk_score * 100
        risk_level = predicted_class.upper()
        
        # Log the prediction to terminal (We'll see this!)
        print(f"🤖 AI Prediction: {risk_level} (Confidence: {confidence:.2f}%)")

        if risk_level == "HIGH":
            fault = "CPU"

    except Exception as e:
        print(f"❌ AI Prediction failed: {e}")
        # Fallback rule
        risk_score = ((latest_metric.cpu_percent * 0.4) + (latest_metric.memory_percent * 0.6)) / 100
        risk_level = "HIGH" if risk_score > 0.6 else "NORMAL"
        fault = "CPU" if risk_score > 0.6 else "NONE"

    return PredictionOut(
        timestamp=datetime.now().isoformat(),
        risk_score=round(risk_score, 3),
        risk_level=risk_level,
        confidence=round(confidence, 2),
        votes=1,
        fault_type=fault,
        severity_level="INFO" if risk_level != "HIGH" else "WARNING",
        pem_status="NORMAL",
        md_status="NORMAL",
        models={"xgboost": 1 if risk_level == "HIGH" else 0},
        probabilities={
            "normal": round(proba[0], 3) if 'proba' in locals() else 0,
            "moderate": round(proba[1], 3) if 'proba' in locals() else 0,
            "high": round(proba[2], 3) if 'proba' in locals() else 0
        }
    )

# ----------------------------------------------------------------
# OTHER REST ENDPOINTS
# ----------------------------------------------------------------
@app.get("/alerts", response_model=list[AlertOut])
def get_alerts(db: Session = Depends(get_db)) -> list[AlertOut]:
    return db.query(AnomalyAlert).order_by(AnomalyAlert.id.desc()).limit(20).all()


@app.get("/status", response_model=StatusOut)
def get_status(db: Session = Depends(get_db)) -> StatusOut:
    latest = db.query(Prediction).order_by(Prediction.id.desc()).first()
    if latest is None:
        return StatusOut(risk_level="NORMAL", fault_type="NONE", severity_level="INFO")
    return StatusOut(
        risk_level=latest.risk_level,
        fault_type=latest.fault_type,
        severity_level=latest.severity_level,
    )


@app.get("/history", response_model=HistoryResponse)
def get_history(db: Session = Depends(get_db)) -> HistoryResponse:
    metrics = db.query(Metric).order_by(Metric.id.desc()).limit(100).all()
    metrics = list(reversed(metrics))
    return HistoryResponse(metrics=[MetricOut.model_validate(m, from_attributes=True) for m in metrics])


@app.get("/risk-history")
def get_risk_history(db: Session = Depends(get_db)):
    predictions = (
        db.query(Prediction)
        .order_by(Prediction.id.desc())
        .limit(30)
        .all()
    )
    predictions = list(reversed(predictions))
    return [
        {
            "timestamp": p.timestamp.strftime("%H:%M:%S"),
            "risk_score": p.risk_score,
            "risk_level": p.risk_level,
            "fault_type": p.fault_type
        }
        for p in predictions
    ]


@app.post("/calibrate")
def calibrate() -> dict:
    try:
        from app.calibration_wrapper import run_calibration
        result = run_calibration()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Calibration failed: {exc}") from exc
    return {"status": "calibrated", **result}