// frontend/src/services/api.js
import axios from 'axios';
import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

// =========================================================
// LEGACY ENDPOINT (Keep this)
// =========================================================
export async function getPrediction(){
    try {
        const response = await fetch(`${API_URL}/predict`);
        if(!response.ok){
            throw new Error("Prediction API failed");
        }
        return await response.json();
    } catch(error){
        console.error("API Error:", error);
        throw error;
    }
}

// =========================================================
// NEW XGBOOST ENDPOINTS (Keep these)
// =========================================================
export async function predictXGBoost(metrics) {
    try {
        const response = await axios.post(`${API_URL}/predict/`, {
            hostname: metrics.hostname || 'system-01',
            timestamp: metrics.timestamp || new Date().toISOString(),
            cpu_percent: metrics.cpu_percent || 0,
            memory_percent: metrics.memory_percent || 0,
            disk_read_mbps: metrics.disk_read_mbps || 0,
            disk_write_mbps: metrics.disk_write_mbps || 0,
            network_upload_mbps: metrics.network_upload_mbps || 0,
            network_download_mbps: metrics.network_download_mbps || 0,
            process_count: metrics.process_count || 0,
            ssd_percentage_used: metrics.ssd_percentage_used || 0,
        });
        return response.data;
    } catch (error) {
        console.error("XGBoost Prediction Error:", error);
        throw error;
    }
}

export async function getBufferStatus() {
    try {
        const response = await axios.get(`${API_URL}/predict/buffer_status`);
        return response.data;
    } catch (error) {
        console.error("Buffer Status Error:", error);
        throw error;
    }
}

export async function healthCheck() {
    try {
        const response = await axios.get(`${API_URL}/predict/health`);
        return response.data;
    } catch (error) {
        console.error("Health Check Error:", error);
        throw error;
    }
}

// =========================================================
// ✨ NEW: WEBSOCKET CONNECTION (Add this at the bottom)
// =========================================================
export const connectLiveWS = (onDataReceived) => {
  // Create a native WebSocket connection to your backend
  const ws = new WebSocket(`ws://127.0.0.1:8000/ws/live`);

  ws.onopen = () => {
    console.log("Connected to live WebSocket!");
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onDataReceived(data);
  };

  ws.onerror = (error) => {
    console.error("WebSocket Error:", error);
  };

  return ws; // Return the socket so we can close it in the component
};
// =========================================================
// ✨ NEW: REST POLLING HELPERS
// =========================================================
export async function fetchHistory() {
  const res = await fetch(`${API_URL}/history`);
  if (!res.ok) throw new Error("History fetch failed");
  return res.json();
}

export async function fetchStatus() {
  const res = await fetch(`${API_URL}/status`);
  if (!res.ok) throw new Error("Status fetch failed");
  return res.json();
}

// Shared hook any page can use
export function useLiveData(intervalMs = 2000) {
  const [history, setHistory] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const [historyData, pred, stat] = await Promise.all([
          fetchHistory(),
          getPrediction(),
          fetchStatus(),
        ]);

        if (cancelled) return;

        const metrics = historyData?.metrics || [];
        const latest = metrics[metrics.length - 1];

        if (latest) {
          const newMetric = {
            cpu_percent: latest.cpu_percent ?? 0,
            memory_percent: latest.memory_percent ?? 0,
            disk_write_mbps: latest.disk_write_mbps ?? 0,
            process_count: latest.process_count ?? 0,
            memory_available_mb: latest.memory_available_mb ?? 0,
            top_cpu_process: latest.top_cpu_process || "N/A",
            top_mem_process: latest.top_mem_process || "N/A",
            risk: pred?.risk_score ?? 0,
            timestamp: new Date().toISOString(),
          };

          setHistory(prev => {
            // Avoid duplicates by checking last timestamp
            if (prev.length > 0) {
              const lastTs = prev[prev.length - 1].timestamp;
              if (lastTs === newMetric.timestamp) return prev;
            }
            return [...prev, newMetric].slice(-100);
          });
        }

        setPrediction(pred);
        setStatus(stat);
        setError(null);
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    poll();
    const id = setInterval(poll, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [intervalMs]);

  const latest = history.length > 0 ? history[history.length - 1] : null;
  return { history, prediction, status, error, loading, latest };
}