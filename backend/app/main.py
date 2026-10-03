import json
import os
import sys
import asyncio
import time
import threading
import psutil
import joblib
import pandas as pd
import csv
from datetime import datetime
from pathlib import Path
from win10toast import ToastNotifier

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.database import get_db, init_db, SessionLocal
from app.models import AnomalyAlert, Metric, Prediction
from app.schemas import AlertOut, HistoryResponse, MetricCreate, MetricOut, PredictionOut, StatusOut

print("🟢🟢🟢 main.py LOADED 🟢🟢🟢")
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================
# BACKGROUND COLLECTOR (runs forever, writes to DB every 5 sec)
# =============================================================
async def collect_metrics_forever():
    print("🟣 COLLECTOR FUNCTION ENTERED")
    prev_disk_write = psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0
    prev_disk_read = psutil.disk_io_counters().read_bytes if psutil.disk_io_counters() else 0

    # ✅ FIX: Track previous network values for per-second delta
    net_io_init = psutil.net_io_counters()
    prev_net_up = net_io_init.bytes_sent if net_io_init else 0
    prev_net_down = net_io_init.bytes_recv if net_io_init else 0

    psutil.cpu_percent(interval=None)

    pending_metrics = []
    pending_predictions = []
    cycle_count = 0
    current_risk_time = 0
    last_alert_time = 0

    while True:
        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            memory_usage = psutil.virtual_memory().percent
            process_count = len(psutil.pids())
            memory_available_mb = psutil.virtual_memory().available / (1024 * 1024)

            cpu_freq = psutil.cpu_freq()
            cpu_frequency_mhz = cpu_freq.current if cpu_freq else 0.0

            try:
                disk_percent = psutil.disk_usage('C:\\').percent
            except Exception:
                disk_percent = 0.0

            disk_io = psutil.disk_io_counters()
            cur_write = disk_io.write_bytes if disk_io else 0
            disk_write = (cur_write - prev_disk_write) / (1024 * 1024)
            prev_disk_write = cur_write

            cur_read = disk_io.read_bytes if disk_io else 0
            disk_read = (cur_read - prev_disk_read) / (1024 * 1024)
            prev_disk_read = cur_read

            # ✅ FIX: Compute network as per-second delta (matches training)
            net_io = psutil.net_io_counters()
            cur_net_up = net_io.bytes_sent if net_io else 0
            cur_net_down = net_io.bytes_recv if net_io else 0
            net_up = (cur_net_up - prev_net_up) / (1024 * 1024)
            net_down = (cur_net_down - prev_net_down) / (1024 * 1024)
            prev_net_up = cur_net_up
            prev_net_down = cur_net_down

            # Rule-based risk score
            risk_score = ((cpu_usage * 0.4) + (memory_usage * 0.6)) / 100
            model_vote = 1 if risk_score > 0.6 else 0

            top_cpu_process = "N/A"
            top_mem_process = "N/A"
            if cycle_count % 5 == 0:
                try:
                    all_procs = [p for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent'])]
                    cpu_sorted = sorted(all_procs, key=lambda p: p.info['cpu_percent'] or 0, reverse=True)
                    top_cpu_process = cpu_sorted[0].info['name'] if cpu_sorted else "N/A"
                    mem_sorted = sorted(all_procs, key=lambda p: p.info['memory_percent'] or 0, reverse=True)
                    top_mem_process = mem_sorted[0].info['name'] if mem_sorted else "N/A"
                except Exception:
                    pass

            pending_metrics.append(Metric(
                system_id=SYSTEM_ID,
                cpu_percent=round(cpu_usage, 1),
                memory_percent=round(memory_usage, 1),
                memory_available_mb=int(memory_available_mb),
                disk_write_mbps=round(disk_write, 2),
                process_count=int(process_count),
                top_cpu_process=top_cpu_process,
                top_mem_process=top_mem_process,
                cpu_frequency_mhz=round(cpu_frequency_mhz, 1),
                disk_percent=round(disk_percent, 1),
                disk_read_mbps=round(disk_read, 2),
                network_upload_mbps=round(net_up, 2),
                network_download_mbps=round(net_down, 2),
            ))

            pending_predictions.append(Prediction(
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
            ))

            # ============================================================
            # 🔔 HIGH RISK DETECTION + NOTIFICATION + ALERT DB WRITE
            # ============================================================
            HIGH_THRESHOLD = 0.7
            PERSISTENCE_SECONDS = 30
            ALERT_COOLDOWN_SECONDS = 300

            if risk_score >= HIGH_THRESHOLD:
                current_risk_time += 1
                if current_risk_time == PERSISTENCE_SECONDS:
                    now_ts = time.time()
                    if now_ts - last_alert_time > ALERT_COOLDOWN_SECONDS:
                        print(f"🚨 HIGH RISK PERSISTED 30s — firing alert")

                        def send_desktop_alert(top_cpu):
                            try:
                                _toaster = ToastNotifier()
                                _toaster.show_toast(
                                    "⚠️ CRITICAL SYSTEM RISK!",
                                    f"High risk detected.\nTop process: {top_cpu}\nAction required!",
                                    duration=6,
                                    threaded=True
                                )
                            except Exception as _e:
                                print(f"⚠️ Toast failed: {_e}")

                        threading.Thread(
                            target=send_desktop_alert,
                            args=(top_cpu_process,),
                            daemon=True
                        ).start()

                        try:
                            _db = SessionLocal()
                            _alert = AnomalyAlert(
                                system_id=SYSTEM_ID,
                                alert_type="HIGH_RISK",
                                severity="CRITICAL",
                                fault_type="CPU" if cpu_usage > memory_usage else "MEMORY",
                                resolved_at=None
                            )
                            _db.add(_alert)
                            _db.commit()
                            _db.close()
                            print(f"✅ Alert written to DB | ID: {_alert.id}")
                        except Exception as _e:
                            print(f"❌ Alert DB write failed: {_e}")

                        last_alert_time = now_ts
                        current_risk_time = 0
            else:
                current_risk_time = 0

            if len(pending_metrics) >= 5:
                db = SessionLocal()
                for m in pending_metrics:
                    db.add(m)
                for p in pending_predictions:
                    db.add(p)
                db.commit()
                db.close()
                pending_metrics = []
                pending_predictions = []
                print(f"💾 Saved to DB | CPU: {cpu_usage:.1f}% | MEM: {memory_usage:.1f}% | RISK: {risk_score:.3f}")

            cycle_count += 1
            await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Collector error: {e}")
            await asyncio.sleep(1)


# =============================================================
# LIFESPAN
# =============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(collect_metrics_forever())
    print("✅ Background metric collector started")
    yield
    task.cancel()
    print("🛑 Background metric collector stopped")


app = FastAPI(title="Predictive Maintenance API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_ID = os.getenv("SYSTEM_ID", "SYSTEM-01")


# =============================================================
# CSV HELPER
# =============================================================
METRICS_CSV = "live_data_log.csv"

def append_to_csv(data_dict):
    fieldnames = [
        'cpu', 'memory', 'disk', 'risk', 'process_count',
        'memory_available_mb', 'timestamp',
        'top_cpu_process', 'top_mem_process'
    ]
    file_exists = os.path.isfile(METRICS_CSV)
    with open(METRICS_CSV, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: data_dict.get(k, '') for k in fieldnames})


# =============================================================
# LOAD AI MODEL
# =============================================================
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


# =============================================================
# WEBSOCKET (kept for compatibility)
# =============================================================
previous_disk_bytes = psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0
previous_disk_read_bytes = psutil.disk_io_counters().read_bytes if psutil.disk_io_counters() else 0

# ✅ FIX: Network delta tracking for WebSocket
_ws_net_init = psutil.net_io_counters()
previous_net_up = _ws_net_init.bytes_sent if _ws_net_init else 0
previous_net_down = _ws_net_init.bytes_recv if _ws_net_init else 0


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    global previous_disk_bytes
    global previous_disk_read_bytes
    global previous_net_up
    global previous_net_down
    await websocket.accept()
    psutil.cpu_percent(interval=None)

    toaster = ToastNotifier()
    last_moderate_alert_time = 0
    current_risk_time = 0

    pending_metrics = []
    pending_predictions = []
    cycle_count = 0
    top_cpu_process = "N/A"
    top_mem_process = "N/A"

    try:
        while True:
            try:
                cpu_usage = psutil.cpu_percent(interval=None)
                memory_usage = psutil.virtual_memory().percent
                process_count = len(psutil.pids())
                memory_available_mb = psutil.virtual_memory().available / (1024 * 1024)

                current_disk_bytes = psutil.disk_io_counters().write_bytes if psutil.disk_io_counters() else 0
                cpu_freq = psutil.cpu_freq()
                cpu_frequency_mhz = cpu_freq.current if cpu_freq else 0.0
                try:
                    disk_percent = psutil.disk_usage('C:\\').percent
                except Exception:
                    disk_percent = 0.0
                disk_io = psutil.disk_io_counters()
                disk_read_bytes = disk_io.read_bytes if disk_io else 0
                disk_read_mbps = (disk_read_bytes - previous_disk_read_bytes) / (1024 * 1024)
                previous_disk_read_bytes = disk_read_bytes

                # ✅ FIX: Network delta
                net_io = psutil.net_io_counters()
                cur_net_up = net_io.bytes_sent if net_io else 0
                cur_net_down = net_io.bytes_recv if net_io else 0
                network_upload_mbps = (cur_net_up - previous_net_up) / (1024 * 1024)
                network_download_mbps = (cur_net_down - previous_net_down) / (1024 * 1024)
                previous_net_up = cur_net_up
                previous_net_down = cur_net_down

                disk_write = (current_disk_bytes - previous_disk_bytes) / (1024 * 1024)
                previous_disk_bytes = current_disk_bytes

                risk_score = ((cpu_usage * 0.4) + (memory_usage * 0.6)) / 100
                model_vote = 1 if risk_score > 0.6 else 0

                if cycle_count % 5 == 0:
                    try:
                        all_procs = [p for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent'])]
                        cpu_sorted = sorted(all_procs, key=lambda p: p.info['cpu_percent'] or 0, reverse=True)
                        top_cpu_process = cpu_sorted[0].info['name'] if cpu_sorted else "N/A"
                        mem_sorted = sorted(all_procs, key=lambda p: p.info['memory_percent'] or 0, reverse=True)
                        top_mem_process = mem_sorted[0].info['name'] if mem_sorted else "N/A"
                    except Exception:
                        pass

                pending_metrics.append(Metric(
                    system_id=SYSTEM_ID,
                    cpu_percent=round(cpu_usage, 1),
                    memory_percent=round(memory_usage, 1),
                    memory_available_mb=int(memory_available_mb),
                    disk_write_mbps=round(disk_write, 2),
                    process_count=int(process_count),
                    top_cpu_process=top_cpu_process,
                    top_mem_process=top_mem_process,
                    cpu_frequency_mhz=round(cpu_frequency_mhz, 2),
                    disk_percent=round(disk_percent, 2),
                    disk_read_mbps=round(disk_read_mbps, 2),
                    network_upload_mbps=round(network_upload_mbps, 2),
                    network_download_mbps=round(network_download_mbps, 2)
                ))

                pending_predictions.append(Prediction(
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
                ))

                if len(pending_metrics) >= 5:
                    db = SessionLocal()
                    for m in pending_metrics:
                        db.add(m)
                    for p in pending_predictions:
                        db.add(p)
                    db.commit()
                    db.close()
                    pending_metrics = []
                    pending_predictions = []

                data = {
                    "cpu": round(cpu_usage, 1),
                    "memory": round(memory_usage, 1),
                    "disk": round(disk_write, 2),
                    "risk": round(risk_score, 3),
                    "process_count": int(process_count),
                    "memory_available_mb": int(memory_available_mb),
                    "top_cpu_process": top_cpu_process,
                    "top_mem_process": top_mem_process,
                    "cpu_frequency_mhz": round(cpu_frequency_mhz, 1),
                    "disk_percent": round(disk_percent, 1),
                    "disk_read_mbps": round(disk_read_mbps, 2),
                    "network_upload_mbps": round(network_upload_mbps, 2),
                    "network_download_mbps": round(network_download_mbps, 2),
                    "timestamp": datetime.now().isoformat()
                }

                append_to_csv(data)
                print(f"📊 CPU: {cpu_usage:.1f}% | MEM: {memory_usage:.1f}% | RISK: {risk_score:.3f} | TOP CPU: {top_cpu_process} | TOP MEM: {top_mem_process}")

                current_ts = time.time()
                if 0.4 <= risk_score < 0.7:
                    if current_ts - last_moderate_alert_time > 300:
                        toaster.show_toast(
                            "🟡 Moderate Risk Detected",
                            f"System load rising.\nTop process: {top_cpu_process}",
                            duration=5
                        )
                        last_moderate_alert_time = current_ts

                if risk_score >= 0.7:
                    current_risk_time += 1
                    if current_risk_time >= 30:
                        def send_high_burst(cpu, mem):
                            for _ in range(3):
                                toaster.show_toast(
                                    "⚠️ CRITICAL SYSTEM RISK!",
                                    f"CPU Spike: {cpu}\nAction required!",
                                    duration=6
                                )
                                time.sleep(2)
                        threading.Thread(target=send_high_burst, args=(top_cpu_process, top_mem_process)).start()
                        current_risk_time = 0
                else:
                    current_risk_time = 0

                try:
                    await websocket.send_json(data)
                except Exception as send_error:
                    print(f"❌ WebSocket send failed: {send_error}")
                    return

                cycle_count += 1
                await asyncio.sleep(1)

            except Exception as e:
                print(f"WebSocket disconnected or cancelled: {e}")
                return
    except Exception as e:
        print(f"WebSocket outer cleanup: {e}")


# =============================================================
# REST ENDPOINTS
# =============================================================
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


@app.get("/predict", response_model=PredictionOut)
def get_prediction(db: Session = Depends(get_db)) -> PredictionOut:
    latest_metric = db.query(Metric).order_by(Metric.id.desc()).first()

    if not latest_metric:
        return PredictionOut(
            timestamp=datetime.now().isoformat(),
            risk_score=0.0, risk_level="NORMAL",
            confidence=0.0, votes=0, fault_type="NONE",
            severity_level="INFO",
            pem_status="NORMAL",
            md_status="NORMAL",
            models={}, probabilities={}
        )

    fault = "NONE"
    confidence = 0.0
    risk_score = 0.1
    risk_level = "NORMAL"

    try:
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
        proba = xgb_model.predict_proba(scaled_inputs)[0]
        predicted_class = int(xgb_model.predict(scaled_inputs)[0])

        label_map = {0: "NORMAL", 1: "MODERATE", 2: "HIGH"}
        class_risk_map = {0: 0.1, 1: 0.5, 2: 0.9}

        risk_level = label_map.get(predicted_class, "NORMAL")
        confidence = float(proba[predicted_class]) * 100
        risk_score = class_risk_map.get(predicted_class, 0.1)

        # Idle override: force NORMAL when system is clearly idle
        if (latest_metric.cpu_percent < 8
                and latest_metric.memory_percent < 55
                and risk_level != "HIGH"):
            risk_level = "NORMAL"
            confidence = 99.0
            risk_score = 0.1
        print(f"🤖 AI Prediction: {risk_level} (Conf: {confidence:.2f}%)")

        if risk_level == "HIGH":
            fault = "CPU"

    except Exception as e:
        print(f"❌ AI Prediction failed: {e}")
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
            "normal": round(float(proba[0]), 3) if 'proba' in locals() else 0,
            "moderate": round(float(proba[1]), 3) if 'proba' in locals() else 0,
            "high": round(float(proba[2]), 3) if 'proba' in locals() else 0
        }
    )


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