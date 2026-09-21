import React from "react";
import { Chart, registerables } from 'chart.js';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

Chart.register(...registerables);
function RiskChart({ history }) {

  const data = history.slice(-20).map((item) => ({

    time: new Date(item.timestamp).toLocaleTimeString([],{
      hour:"2-digit",
      minute:"2-digit"
    }),

    risk:
      item.risk_score ??
      item.risk ??
      0

  }));


  return (

    <div className="chart-card">

      <div className="chart-title">

        Risk Score Trend

      </div>

      <ResponsiveContainer
        width="100%"
        height={250}
      >

        <AreaChart data={data}>

          <CartesianGrid stroke="#232838"/>

          <XAxis
            dataKey="time"
            stroke="#64748b"
          />

          <YAxis
            domain={[0,1]}
            stroke="#64748b"
          />

          <Tooltip/>

          <Area
            type="monotone"
            dataKey="risk"
            stroke="#ef4444"
            fill="#7f1d1d"
          />

        </AreaChart>

      </ResponsiveContainer>

    </div>

  );

}

export default RiskChart;