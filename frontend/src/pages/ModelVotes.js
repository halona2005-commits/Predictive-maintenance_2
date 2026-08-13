import React, { useEffect, useState } from "react";

const API = "http://127.0.0.1:8000";

const MODEL_F1 = {
  "Random Forest": 98.62,
  "XGBoost": 98.81,
  "Isolation Forest": 87.61,
  "One-Class SVM": 87.12,
  "Compressed IF": 89.02,
  "LSTM ": 46.53
};

export default function ModelVotes() {

  const [prediction, setPrediction] = useState(null);

  const fetchPrediction = async () => {
    try {
      const res = await fetch(`${API}/predict`);
      const data = await res.json();
      setPrediction(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchPrediction();
    const timer = setInterval(fetchPrediction, 5000);
    return () => clearInterval(timer);
  }, []);

  if (!prediction) {
    return <h2>Loading...</h2>;
  }

  const models = prediction.models || {};
  const probabilities = prediction.probabilities || {};

  const anomalyCount = Object.values(models).filter(v => v === 1).length;

  return (
    <div>

      <h2 style={{ marginBottom: 20 }}>
        AI Model Voting System
      </h2>

      {/* =========================== */}
      {/* UPPER TABLE: CURRENT VOTES  */}
      {/* =========================== */}
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Vote</th>
              <th>Score</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(models).map(([name, vote]) => {

              const confidence = (() => {
                 if (probabilities[name] !== undefined) {
                    return (probabilities[name] * 100).toFixed(2) + "%";
                }
                if (MODEL_F1[name] !== undefined) {
                    return MODEL_F1[name].toFixed(2) + "%";
                }
                return "N/A";
            })();

              const reason =
                vote === 1
                  ? `High ${prediction.fault_type} anomaly detected`
                  : "Normal operating pattern";
                  
                return (
                <tr key={name}>
                  <td>{name}</td>
                  <td>
                    <span
                      style={{
                        color: vote ? "#ef4444" : "#22c55e",
                        fontWeight: "bold"
                      }}
                    >
                      {vote ? "Anomaly" : "Normal"}
                    </span>
                  </td>
                  <td>{confidence}</td>
                  <td>{reason}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ================================================================ */}
      {/* REPLACED BOTTOM CARD: "Summary" REMOVED, "Comparison" ADDED HERE */}
      {/* ================================================================ */}
      <div
        className="card"
        style={{
          marginTop: 20
        }}
      >
        <h3>Why XGBoost was Selected for Deployment</h3>

        <div style={{ marginTop: 15 }}>
          <table style={{ marginTop: 15, width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #232838" }}>
                <th style={{ textAlign: "left", padding: "8px 0", color: "#94a3b8" }}>Model</th>
                <th style={{ textAlign: "left", padding: "8px 0", color: "#94a3b8" }}>F1-Score</th>
                <th style={{ textAlign: "left", padding: "8px 0", color: "#94a3b8" }}>Inference Latency</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: "1px solid #1a1e2a" }}>
                <td style={{ padding: "8px 0" }}>XGBoost</td>
                <td style={{ padding: "8px 0", fontWeight: "bold", color: "#4ade80" }}>98.75%</td>
                <td style={{ padding: "8px 0", fontWeight: "bold", color: "#4ade80" }}>2.8 μs</td>
              </tr>
              <tr style={{ borderBottom: "1px solid #1a1e2a" }}>
                <td style={{ padding: "8px 0" }}>Random Forest</td>
                <td style={{ padding: "8px 0" }}>98.20%</td>
                <td style={{ padding: "8px 0" }}>45.2 μs</td>
              </tr>
              <tr style={{ borderBottom: "1px solid #1a1e2a" }}>
                <td style={{ padding: "8px 0" }}>MLP Neural Net</td>
                <td style={{ padding: "8px 0" }}>98.03%</td>
                <td style={{ padding: "8px 0" }}>12.4 μs</td>
              </tr>
              <tr>
                <td style={{ padding: "8px 0" }}>Logistic Regression</td>
                <td style={{ padding: "8px 0" }}>95.28%</td>
                <td style={{ padding: "8px 0" }}>0.1 μs</td>
              </tr>
            </tbody>
          </table>

          <p style={{ marginTop: 15, lineHeight: 1.7, color: "#cbd5e1" }}>
            <strong>Conclusion:</strong> XGBoost was selected because it provided the highest F1-score (98.75%) while maintaining an inference latency of just <strong>2.8 microseconds</strong>. This makes it the ideal choice for a real-time predictive maintenance system that requires predictions every 1 second without consuming excessive system resources. The raw 5-feature variant of XGBoost was ultimately deployed to the live backend.
          </p>
        </div>
      </div>

    </div>
  );
}