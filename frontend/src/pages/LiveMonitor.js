import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { useLiveData } from "../services/api";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler            // ✅ Fixes the "fill option" warning
);

export default function LiveMonitor() {
  // 🔥 One line replaces the entire WebSocket useEffect
  const { history } = useLiveData(2000);

  // Convert history → chart-friendly points
  const metricsHistory = history.map((m) => ({
    timestamp: new Date(m.timestamp).toLocaleTimeString(),
    cpu: m.cpu_percent,
    memory: m.memory_percent,
    disk: m.disk_write_mbps,
    risk: m.risk,
  })).slice(-50);

  const labels = metricsHistory.map((m) => m.timestamp);
  const cpu = metricsHistory.map((m) => m.cpu);
  const memory = metricsHistory.map((m) => m.memory);
  const disk = metricsHistory.map((m) => m.disk);
  const risk = metricsHistory.map((m) => m.risk);

  const makeChart = (label, color, data) => ({
    labels,
    datasets: [
      {
        label,
        data,
        borderColor: color,
        backgroundColor: color + "33",  // subtle fill
        tension: 0.35,
        fill: true,                     // now works (Filler registered)
        pointRadius: 0,
      },
    ],
  });

  const options = {
    responsive: true,
    animation: false,                   // ✅ No animation = faster updates
    plugins: {
      legend: { labels: { color: "#fff" } },
    },
    scales: {
      x: { ticks: { color: "#ccc" }, grid: { color: "#222" } },
      y: { ticks: { color: "#ccc" }, grid: { color: "#222" } },
    },
  };

  return (
    <div>
      <h2 style={{ marginBottom: 20 }}>Live System Monitor</h2>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <div className="card">
          <h3>CPU Usage %</h3>
          <Line data={makeChart("CPU", "#22c55e", cpu)} options={options} />
        </div>

        <div className="card">
          <h3>Memory Usage %</h3>
          <Line data={makeChart("Memory", "#3b82f6", memory)} options={options} />
        </div>

        <div className="card">
          <h3>Disk Write Speed (MB/s)</h3>
          <Line data={makeChart("Disk", "#f59e0b", disk)} options={options} />
        </div>

        <div className="card">
          <h3>Risk Score</h3>
          <Line data={makeChart("Risk", "#ef4444", risk)} options={options} />
        </div>
      </div>
    </div>
  );
}