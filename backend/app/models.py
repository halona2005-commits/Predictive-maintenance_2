from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.database import Base


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    system_id = Column(String, nullable=False, default="SYSTEM-01")
    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    memory_available_mb = Column(Float, nullable=False)
    disk_write_mbps = Column(Float, nullable=False)
    process_count = Column(Integer, nullable=False)
    # 👇 ADD THESE TWO NEW COLUMNS
    top_cpu_process = Column(String, nullable=True)
    top_mem_process = Column(String, nullable=True)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    system_id = Column(String, nullable=False, default="SYSTEM-01")
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    votes = Column(Integer, nullable=False)
    fault_type = Column(String, nullable=False)
    severity_level = Column(String, nullable=False)
    pem_status = Column(String, nullable=False)
    md_status = Column(String, nullable=False)
    models_json = Column(Text, nullable=True)
    probabilities_json = Column(Text, nullable=True)


class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    system_id = Column(String, nullable=False, default="SYSTEM-01")
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    fault_type = Column(String, nullable=False)
    resolved_at = Column(DateTime, nullable=True)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(String, nullable=False, default="SYSTEM-01")
    session_label = Column(String, nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    total_rows = Column(Integer, nullable=False, default=0)