import React, { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from "chart.js";
import { Line } from "react-chartjs-2";
import { connectLiveWS } from "../services/api"; // <-- Import the new function

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function LiveMonitor() {
  // We store the live datapoints in an array
  const [metricsHistory, setMetricsHistory] = useState([]);

  useEffect(() => {
    // Connect to WebSocket and handle incoming data
    const ws = connectLiveWS((data) => {
      console.log("Live Data Received:", data);
      
      // Create a new chart point
      const newPoint = {
        timestamp: new Date().toLocaleTimeString(), // Format time for X-Axis
        cpu: data.cpu,
        memory: data.memory,
        disk: data.disk || 0, // Fallback if not sent yet
        risk: data.risk
      };

      // Append to state. Limit to 50 points so the chart doesn't get too slow.
      setMetricsHistory(prev => [...prev, newPoint].slice(-50));
    });

    // Cleanup WebSocket when component unmounts
    return () => ws.close();
  }, []);

  // Extract data for the charts
  const labels = metricsHistory.map((m) => m.timestamp);
  const cpu = metricsHistory.map((m) => m.cpu);
  const memory = metricsHistory.map((m) => m.memory);
  const disk = metricsHistory.map((m) => m.disk);
  
  // ✨ THIS IS THE FIX! The risk now maps to the live risk from the backend
  const risk = metricsHistory.map((m) => m.risk);

  const latest = metricsHistory.length ? metricsHistory[metricsHistory.length - 1] : null;

  const makeChart = (label, color, data) => ({
    labels,
    datasets: [
      {
        label,
        data,
        borderColor: color,
        backgroundColor: color,
        tension: 0.35
      }
    ]
  });

  const options = {
    responsive: true,
    plugins: {
      legend: {
        labels: {
          color: "#fff"
        }
      }
    },
    scales: {
      x: {
        ticks: { color: "#ccc" },
        grid: { color: "#222" }
      },
      y: {
        ticks: { color: "#ccc" },
        grid: { color: "#222" }
      }
    }
  };

  return (
    <div>

      <h2 style={{ marginBottom: 20 }}>Live System Monitor</h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 20
        }}
      >

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
          {/* THIS RED LINE WILL NOW FLUCTUATE WITH THE REAL DATA */}
          <Line data={makeChart("Risk", "#ef4444", risk)} options={options} />
        </div>

      </div>

      <div
        className="card"
        style={{
          marginTop: 20
        }}
      >
        <h3 style={{ marginBottom: 15 }}>System Information</h3>

        <table>
          <tbody>
            <tr>
              <td>Total Processes</td>
              <td>{latest?.process_count ?? "--"}</td>
            </tr>
            <tr>
              <td>RAM Available</td>
              <td>
                {latest
                  ? `${latest.memory_available_mb?.toFixed(0) || 0} MB`
                  : "--"}
              </td>
            </tr>
            <tr>
              <td>Sampling Interval</td>
              <td><strong>Real-time (1 Second)</strong></td>
            </tr>
            <tr>
              <td>CPU Temperature</td>
              <td>N/A</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  );
}