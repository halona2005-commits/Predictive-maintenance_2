import React from "react";
import { Chart, registerables } from 'chart.js';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

Chart.register(...registerables);
function CpuChart({ history }) {
  const data = history.slice(-20).map((item) => ({
    time: new Date(item.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
    cpu: Number(item.cpu_percent.toFixed(1)),
  }));

  return (
    <div
      style={{
        background: "#131720",
        border: "1px solid #232838",
        borderRadius: 12,
        padding: 18,
      }}
    >
      <h3 style={{ color: "#e2e8f0", marginBottom: 15 }}>
        CPU Usage Trend
      </h3>

      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid stroke="#232838" />

          <XAxis
            dataKey="time"
            stroke="#64748b"
          />

          <YAxis
            domain={[0, 100]}
            stroke="#64748b"
          />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="cpu"
            stroke="#3b82f6"
            strokeWidth={3}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default CpuChart;