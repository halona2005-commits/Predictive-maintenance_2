import React, { useState, useEffect } from "react";
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

import { connectLiveWS } from "../services/api";

const MODEL_F1_SCORES = {
  "XGBoost": "98.75%",
};

const RISK_BADGE_COLORS = {
  LOW: { color: "#4ade80", bg: "rgba(74, 222, 128, 0.12)", border: "#4ade80" },
  MEDIUM: { color: "#f59e0b", bg: "rgba(245, 158, 11, 0.12)", border: "#f59e0b" },
  HIGH: { color: "#f97316", bg: "rgba(249, 115, 22, 0.12)", border: "#f97316" },
  CRITICAL: { color: "#ef4444", bg: "rgba(239, 68, 68, 0.12)", border: "#ef4444" },
};

function RiskBadge({ level }) {
  const key = (level || "LOW").toUpperCase();
  const style = RISK_BADGE_COLORS[key] || RISK_BADGE_COLORS.LOW;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "10px 18px",
        borderRadius: 999,
        border: `1px solid ${style.border}`,
        background: style.bg,
        color: style.color,
        fontWeight: 700,
        fontSize: 14,
        letterSpacing: 0.5,
      }}
    >
      <ShieldAlert size={16} />
      {key}
    </div>
  );
}

export default function Dashboard() {
  const [history, setHistory] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [status, setStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const [alertBannerVisible, setAlertBannerVisible] = useState(false);
  const [lastFrontendToastTime, setLastFrontendToastTime] = useState(0);

  useEffect(() => {
    setLoading(false);

    const ws = connectLiveWS((data) => {
      console.log("Dashboard Live Data:", data);

      const newMetric = {
        cpu_percent: data.cpu,
        memory_percent: data.memory,
        disk_write_mbps: data.disk || 0,
        process_count: data.process_count || 0,
        memory_available_mb: data.memory_available_mb || 0,
        risk: data.risk,
        top_cpu_process: data.top_cpu_process,
        top_mem_process: data.top_mem_process,
        timestamp: new Date().toISOString(),
      };

      // Calculate risk level
      let riskLevel = "NORMAL";
      if (data.risk >= 0.7) {
        riskLevel = "HIGH";
      } else if (data.risk >= 0.4) {
        riskLevel = "MODERATE";
      }

      // --- 3-LEVEL ALERT LOGIC (With Cooldowns) ---
      const now = Date.now();
      
      if (data.risk >= 0.7) {
        setAlertBannerVisible(true);
        // Show 3 continuous browser toasts for High. Cooldown: 30 seconds.
        if (now - lastFrontendToastTime > 30000) {
          const culpritText = data.top_cpu_process ? `CPU Spike: ${data.top_cpu_process}` : "High CPU Usage";
          
          // 3 continuous toasts with 2-second delay
          for (let i = 0; i < 3; i++) {
            setTimeout(() => {
              toast.error(`⚠️ CRITICAL (${i+1}/3): System Risk is HIGH!\n${culpritText}`, { duration: 8000 });
            }, i * 2000); 
          }
          setLastFrontendToastTime(now);
        }
      } else if (data.risk >= 0.4) {
        setAlertBannerVisible(false);
        // Show 1 toast for Moderate. Cooldown: 5 minutes.
        if (now - lastFrontendToastTime > 300000) {
          toast(`🟡 Moderate Risk Detected.\nTop process: ${data.top_cpu_process || "N/A"}`, { 
            duration: 5000, 
            style: { background: "#facc15", color: "#000" } 
          });
          setLastFrontendToastTime(now);
        }
      } else {
        setAlertBannerVisible(false);
      }

      // Health and Prediction objects
      const healthPercent = data.risk >= 0.7 ? Math.round((1 - data.risk) * 100) : 100;

      const newPrediction = {
        risk_score: data.risk,
        risk_level: riskLevel,
        confidence: 1.0,
        votes: 1,
        models: { "XGBoost": data.risk >= 0.7 ? 1 : 0 }
      };

      const newStatus = {
        risk_level: riskLevel,
        fault_type: "NONE",
        severity_level: "INFO"
      };

      setHistory(prev => [...prev, newMetric].slice(-100));
      setPrediction(newPrediction);
      setStatus(newStatus);
      setError(null);
    });

    return () => ws.close();
  }, []);

  const latest = history.length > 0 ? history[history.length - 1] : null;

  const riskScore = prediction?.risk_score ?? latest?.risk_score ?? 0;
  const healthPercent = riskScore >= 0.7 ? Math.round(Math.max(0, Math.min(100, (1 - riskScore) * 100))) : 100;

  const overallRiskLevel = prediction?.risk_level || status?.risk_level || "LOW";

  return (
    <div className="dashboard-container">
      {/* ALERT BANNER */}
      {alertBannerVisible && (
        <div className="alert-banner">
          🚨 WARNING: System Risk is HIGH! CPU and Memory usage are critical.
        </div>
      )}

      {/* TOAST CONTAINER */}
      <Toaster position="top-center" reverseOrder={false} />

      {/* HEADER */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>Predictive Maintenance Dashboard</h1>
          <p>AI-Based Intelligent System for Performance Modelling</p>
        </div>
        <div className="header-right">
          <RiskBadge level={overallRiskLevel} />
        </div>
      </div>

      {error && ( <div className="error-banner">⚠ WebSocket connection lost — {error}</div> )}
      {loading && !latest ? ( <div className="loading-state">Connecting to live stream…</div> ) : (
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
                  
                  {/* PROCESS NAMES ROW */}
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