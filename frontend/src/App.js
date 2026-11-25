import React, { useEffect, useState } from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import "./App.css";

// Pages
import Dashboard from "./pages/Dashboard";
import LiveMonitor from "./pages/LiveMonitor";
import ModelVotes from "./pages/ModelVotes";
import RiskAnalysis from "./pages/RiskAnalysis";
import FaultPrediction from "./pages/FaultPrediction";
import Alerts from "./pages/Alerts";
import History from "./pages/History";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import About from "./pages/About";

function App() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const menu = [
    { path: "/", label: "Dashboard" },
    { path: "/live", label: "Live Monitor" },
    { path: "/votes", label: "Model Votes" },
    { path: "/risk", label: "Risk Analysis" },
    { path: "/fault", label: "Fault Prediction" },
    { path: "/alerts", label: "Alerts" },
    { path: "/history", label: "History" },
    { path: "/reports", label: "Reports" },
    { path: "/settings", label: "Settings" },
    { path: "/about", label: "About" }
  ];

  return (
    <div className="app">

      <aside className="sidebar">
        <nav>

          {menu.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              {item.label}
            </NavLink>
          ))}

        </nav>

      </aside>

      <div className="main">

        <header className="header">

          <div>
            <h2>Predictive Maintenance System</h2>
            <small>AI Powered Monitoring & Anomaly Detection</small>
          </div>

          <div className="header-right">

            <div className="live-status">
              <span className="live-dot"></span>
              Live
            </div>

            <div className="timestamp">
              {time.toLocaleString()}
            </div>

          </div>

        </header>

        <main className="content">

          <Routes>

            <Route path="/" element={<Dashboard />} />
            <Route path="/live" element={<LiveMonitor />} />
            <Route path="/votes" element={<ModelVotes />} />
            <Route path="/risk" element={<RiskAnalysis />} />
            <Route path="/fault" element={<FaultPrediction />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/history" element={<History />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/about" element={<About />} />

          </Routes>

        </main>

      </div>

    </div>
  );
}

export default App;