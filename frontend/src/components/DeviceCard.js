import React from "react";
import { Chart, registerables } from 'chart.js';
import {
  Monitor,
  Cpu,
  MemoryStick,
  HardDrive
} from "lucide-react";

Chart.register(...registerables);
export default function DeviceCard({
  latest,
  riskLevel
}) {
  if (!latest) return null;

  return (
    <div className="component-card">

      <h3>🖥 Device Information</h3>

      <div className="device-row">
        <Monitor size={18} />
        <span>{latest.system_id || "SYSTEM-01"}</span>
      </div>

      <div className="device-row">
        <Cpu size={18} />
        <span>CPU : {latest.cpu_percent}%</span>
      </div>

      <div className="device-row">
        <MemoryStick size={18} />
        <span>Memory : {latest.memory_percent}%</span>
      </div>

      <div className="device-row">
        <HardDrive size={18} />
        <span>
          Disk : {latest.disk_write_mbps} MB/s
        </span>
      </div>

      <div
        className={`device-health ${riskLevel?.toLowerCase()}`}
      >
        Current Risk : {riskLevel}
      </div>
    </div>
  );
}