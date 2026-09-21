import React from "react";

function HealthCard({ health, calibrating }) {
  // Calibrating state → show --%
  if (calibrating) {
    return (
      <div style={{
        background: "#131720",
        border: "1px solid #232838",
        borderRadius: 12,
        padding: "18px"
      }}>
        <div style={{
          color: "#64748b",
          fontSize: 11,
          textTransform: "uppercase"
        }}>
          System Health
        </div>
        <div style={{
          fontSize: 50,
          fontWeight: 800,
          color: "#64748b",
          marginTop: 10
        }}>
          --%
        </div>
      </div>
    );
  }

  // Normal state → show health value
  let color = "#4ade80";
  if (health !== null && health < 50) {
    color = "#ef4444";
  } else if (health !== null && health < 75) {
    color = "#f59e0b";
  }

  return (
    <div style={{
      background: "#131720",
      border: "1px solid #232838",
      borderRadius: 12,
      padding: "18px"
    }}>
      <div style={{
        color: "#64748b",
        fontSize: 11,
        textTransform: "uppercase"
      }}>
        System Health
      </div>
      <div style={{
        fontSize: 50,
        fontWeight: 800,
        color,
        marginTop: 10
      }}>
        {health !== null ? `${health}%` : "--%"}
      </div>
    </div>
  );
}

export default HealthCard;