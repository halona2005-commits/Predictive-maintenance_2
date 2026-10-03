import React, { useState } from "react";
import { Activity, Cpu, MemoryStick, ListTree, ShieldAlert } from "lucide-react";
import toast, { Toaster } from 'react-hot-toast';
import "./Dashboard.css";

import HealthCard from "../components/HealthCard";
import MetricCard from "../components/MetricCard";
import CpuChart from "../components/CpuChart";
import MemoryChart from "../components/MemoryChart";
import RiskChart from "../components/RiskChart";
import ModelStatus from "../components/ModelStatus";
import AlertPanel from "../components/AlertPanel";
import DeviceCard from "../components/DeviceCard";

import { useLiveData } from "../services/api";

const MODEL_F1_SCORES = { "XGBoost": "98.75%" };

const RISK_BADGE_COLORS = {
  LOW:      { color: "#4ade80", bg: "rgba(74, 222, 128, 0.12)", border: "#4ade80" },
  NORMAL:   { color: "#4ade80", bg: "rgba(74, 222, 128, 0.12)", border: "#4ade80" },
  MEDIUM:   { color: "#f59e0b", bg: "rgba(245, 158, 11, 0.12)", border: "#f59e0b" },
  MODERATE: { color: "#f59e0b", bg: "rgba(245, 158, 11, 0.12)", border: "#f59e0b" },
  HIGH:     { color: "#f97316", bg: "rgba(249, 115, 22, 0.12)", border: "#f97316" },
  CRITICAL: { color: "#ef4444", bg: "rgba(239, 68, 68, 0.12)", border: "#ef4444" },
};

function RiskBadge({ level }) {
  const key = (level || "LOW").toUpperCase();
  const style = RISK_BADGE_COLORS[key] || RISK_BADGE_COLORS.LOW;

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      padding: "10px 18px", borderRadius: 999,
      border: `1px solid ${style.border}`,
      background: style.bg, color: style.color,
      fontWeight: 700, fontSize: 14, letterSpacing: 0.5,
    }}>
      <ShieldAlert size={16} />
      {key}
    </div>
  );
}

export default function Dashboard() {
  const { history, prediction, status, latest, error, loading } = useLiveData(2000);
  const [alerts, setAlerts] = React.useState([]);

  React.useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/alerts");
        const data = await res.json();
        setAlerts(data);
      } catch (e) {
        // silent
      }
    };
    fetchAlerts();
    const id = setInterval(fetchAlerts, 5000);
    return () => clearInterval(id);
  }, []);

  const [alertBannerVisible] = useState(false);

  const riskScore = prediction?.risk_score ?? 0;
  const overallRiskLevel = prediction?.risk_level || status?.risk_level || "NORMAL";
  const healthMap = { "NORMAL": 100, "MODERATE": 70, "HIGH": 30, "CRITICAL": 10 };
  const healthPercent = healthMap[overallRiskLevel];

  return (
    <div className="dashboard-container">
      {alertBannerVisible && (
        <div className="alert-banner">
          🚨 WARNING: System Risk is HIGH!
        </div>
      )}

      <Toaster position="top-center" reverseOrder={false} />

      <div className="dashboard-header">
        <div className="header-left">
          <h1>Predictive Maintenance Dashboard</h1>
          <p>AI-Based Intelligent System for Performance Modelling</p>
        </div>
        <div className="header-right">
          <RiskBadge level={overallRiskLevel} />
        </div>
      </div>

      {error && <div className="error-banner">⚠ Connection issue — {error}</div>}

      {loading && !latest ? (
        <div className="loading-state">Connecting to live stream…</div>
      ) : (
        <>
          <div className="metrics-row">
            <HealthCard health={healthPercent} />
            <MetricCard title="CPU Usage" value={`${latest ? latest.cpu_percent.toFixed(1) : "0.0"}%`} icon={<Cpu size={20} />} status="Current Load" />
            <MetricCard title="Memory Usage" value={`${latest ? latest.memory_percent.toFixed(1) : "0.0"}%`} icon={<MemoryStick size={20} />} status="Current Usage" />
            <MetricCard title="Processes Running" value={latest ? latest.process_count : "0"} icon={<ListTree size={20} />} status="Active Processes" />
          </div>

          <div className="charts-row">
            <CpuChart history={history} />
            <MemoryChart history={history} />
            <RiskChart history={history} />
          </div>

          <div className="bottom-row">
            <div className="left-column">
              <ModelStatus models={prediction?.models || {}} modelF1={MODEL_F1_SCORES} />
              <AlertPanel alerts={alerts} />
            </div>
            <div className="right-column">
              <DeviceCard latest={latest} riskLevel={overallRiskLevel} />

              <div className="component-card">
                <h3><Activity size={16} style={{ marginRight: 6, verticalAlign: "middle" }} /> Current Fault</h3>
                <div className="fault-grid">
                  <div className="fault-item"><span className="fault-label">Fault Type</span><span className="fault-value">{status?.fault_type || "None"}</span></div>
                  <div className="fault-item"><span className="fault-label">Top CPU Process</span><span className="fault-value" style={{ color: "#facc15", fontWeight: "bold" }}>{latest?.top_cpu_process || "N/A"}</span></div>
                  <div className="fault-item"><span className="fault-label">Top Memory Process</span><span className="fault-value" style={{ color: "#facc15", fontWeight: "bold" }}>{latest?.top_mem_process || "N/A"}</span></div>
                  <div className="fault-item"><span className="fault-label">Severity</span><span className="fault-value">{status?.severity_level || "--"}</span></div>
                  <div className="fault-item"><span className="fault-label">Risk Level</span><span className="fault-value">{status?.risk_level || "--"}</span></div>
                  <div className="fault-item"><span className="fault-label">Confidence</span><span className="fault-value">{prediction?.confidence !== undefined ? `${prediction.confidence.toFixed(1)}%` : "--"}</span></div>
                  <div className="fault-item"><span className="fault-label">Ensemble Votes</span><span className="fault-value">{prediction?.votes !== undefined ? `${prediction.votes} / 6` : "--"}</span></div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}