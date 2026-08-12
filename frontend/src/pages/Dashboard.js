import React, { useState, useEffect } from "react";
import { Activity, Cpu, MemoryStick, ListTree, ShieldAlert } from "lucide-react";
import "./Dashboard.css"; 

import HealthCard from "../components/HealthCard";
import MetricCard from "../components/MetricCard";
import CpuChart from "../components/CpuChart";
import MemoryChart from "../components/MemoryChart";
import RiskChart from "../components/RiskChart";
import ModelStatus from "../components/ModelStatus";
import AlertPanel from "../components/AlertPanel";
import DeviceCard from "../components/DeviceCard";

// ✨ 1. NEW IMPORT: Swap out the REST API for your WebSocket
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
  const [alerts, setAlerts] = useState([]); // eslint-disable-next-line no-unused-vars 
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // ✨ 2. REMOVED fetchAll & setInterval. REPLACED with this WebSocket Effect:
  useEffect(() => {
    setLoading(false); // We don't have to wait for an HTTP fetch anymore.

    const ws = connectLiveWS((data) => {
      console.log("Dashboard Live Data:", data);

      // Map WebSocket fields to the exact variable names your child components expect
      const newMetric = {
        cpu_percent: data.cpu,
        memory_percent: data.memory,
        disk_write_mbps: data.disk || 0,
        process_count: data.process_count || 0,
        memory_available_mb: data.memory_available_mb || 0,
        risk: data.risk,
        timestamp: new Date().toISOString(),
      };

      // Calculate risk level from the floating 0.0 - 1.0 score
            // --- FIX: Only trigger danger if risk exceeds 0.6 ---
      let riskLevel = "NORMAL"; 
      if (data.risk > 0.6) {
        riskLevel = "HIGH";
      }
      
      // --- FIX: Health is 100% unless risk goes above the anomaly threshold ---
      const healthPercent = data.risk > 0.6 ? Math.round((1 - data.risk) * 100) : 100;

      // Construct prediction/status objects to match your existing Dashboard code
      const newPrediction = {
        risk_score: data.risk,
        risk_level: riskLevel,
        confidence: 1.0,
        votes: 1,
        models: { "XGBoost": 1 }
      };

      const newStatus = {
        risk_level: riskLevel,
        fault_type: "NONE",
        severity_level: "INFO"
      };

      // Update your states (keep last 100 data points for the charts)
      setHistory(prev => [...prev, newMetric].slice(-100));
      setPrediction(newPrediction);
      setStatus(newStatus);
      setError(null);
    });

    // Cleanup WebSocket on page leave
    return () => ws.close();
  }, []);

  const latest = history.length > 0 ? history[history.length - 1] : null;

  const riskScore = prediction?.risk_score ?? latest?.risk_score ?? 0;
  const healthPercent = riskScore > 0.6 ? Math.round(Math.max(0, Math.min(100, (1 - riskScore) * 100))) : 100;

  const overallRiskLevel = prediction?.risk_level || status?.risk_level || "LOW";

  return (
    <div className="dashboard-container">
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

      {error && (
        <div className="error-banner">
          ⚠ WebSocket connection lost — {error}
        </div>
      )}

      {loading && !latest ? (
        <div className="loading-state">Connecting to live stream…</div>
      ) : (
        <>
          {/* ROW 2: TOP METRICS */}
          <div className="metrics-row">
            <HealthCard health={healthPercent} />

            <MetricCard
              title="CPU Usage"
              value={`${latest ? latest.cpu_percent.toFixed(1) : "0.0"}%`}
              icon={<Cpu size={20} />}
              status="Current Load"
            />

            <MetricCard
              title="Memory Usage"
              value={`${latest ? latest.memory_percent.toFixed(1) : "0.0"}%`}
              icon={<MemoryStick size={20} />}
              status="Current Usage"
            />

            <MetricCard
              title="Processes Running"
              value={latest ? latest.process_count : "0"}
              icon={<ListTree size={20} />}
              status="Active Processes"
            />
          </div>

          {/* ROW 3: CHARTS */}
          <div className="charts-row">
            <CpuChart history={history} />
            <MemoryChart history={history} />
            <RiskChart history={history} />
          </div>

          {/* ROW 4: BOTTOM SECTION */}
          <div className="bottom-row">
            {/* LEFT COLUMN */}
            <div className="left-column">
              <ModelStatus
                models={prediction?.models || {}}
                modelF1={MODEL_F1_SCORES}
              />
              <AlertPanel alerts={alerts} />
            </div>

            {/* RIGHT COLUMN */}
            <div className="right-column">
              <DeviceCard latest={latest} riskLevel={overallRiskLevel} />

              <div className="component-card">
                <h3>
                  <Activity size={16} style={{ marginRight: 6, verticalAlign: "middle" }} />
                  Current Fault
                </h3>

                <div className="fault-grid">
                  <div className="fault-item">
                    <span className="fault-label">Fault Type</span>
                    <span className="fault-value">
                      {status?.fault_type || "None"}
                    </span>
                  </div>

                  <div className="fault-item">
                    <span className="fault-label">Severity</span>
                    <span className="fault-value">
                      {status?.severity_level || "--"}
                    </span>
                  </div>

                  <div className="fault-item">
                    <span className="fault-label">Risk Level</span>
                    <span className="fault-value">
                      {status?.risk_level || "--"}
                    </span>
                  </div>

                  <div className="fault-item">
                    <span className="fault-label">Confidence</span>
                    <span className="fault-value">
                      {prediction?.confidence !== undefined
                        ? `${prediction.confidence.toFixed(1)}%`
                        : "--"}
                    </span>
                  </div>

                  <div className="fault-item">
                    <span className="fault-label">Ensemble Votes</span>
                    <span className="fault-value">
                      {prediction?.votes !== undefined
                        ? `${prediction.votes} / 6`
                        : "--"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}