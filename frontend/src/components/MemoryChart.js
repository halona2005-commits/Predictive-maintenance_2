import React from "react";
import { Chart, registerables } from 'chart.js';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

Chart.register(...registerables);
function MemoryChart({ history }) {

  const data = history.slice(-20).map((item) => ({
    time: new Date(item.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
    memory: Number(item.memory_percent.toFixed(1)),
  }));

  return (
    <div className="chart-card">

      <div className="chart-title">
        Memory Usage Trend
      </div>

      <ResponsiveContainer width="100%" height={250}>

        <LineChart data={data}>

          <CartesianGrid stroke="#232838" />

          <XAxis
            dataKey="time"
            stroke="#64748b"
          />

          <YAxis
            domain={[0,100]}
            stroke="#64748b"
          />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="memory"
            stroke="#f59e0b"
            strokeWidth={3}
            dot={false}
          />

        </LineChart>

      </ResponsiveContainer>

    </div>
  );

}

export default MemoryChart;