"use client";
import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, ReferenceLine, Cell } from "recharts";
import "./page.css";

const FinancialImpactChart = ({ data: propData }) => {
  const defaultData = [
    { name: "Previous Exposure", value: 0, color: "#EF5350" },
    { name: "Hub Effect", value: 0, color: "#26C281" },
    { name: "Routing Effect", value: 0, color: "#26C281" },
    { name: "Final Exposure", value: 0, color: "#5B8DEF" },
  ];

  const defaultStats = [
    { label: "Total Savings", value: "—" },
    { label: "Reduction %", value: "—" },
    { label: "ROI Impact", value: "—" },
  ];

  const chartData = propData?.chart_data || defaultData;
  const stats = propData?.stats || defaultStats;
  const hasData = propData != null;

  return (
    <div className="financial-impact-container">
      <div className="financial-impact-header">
        <h3 className="financial-impact-title">Financial Impact Analysis</h3>
        <p className="financial-impact-subtitle">
          {hasData ? "Waterfall breakdown of exposure reduction" : "Available after Phase 2 steps complete"}
        </p>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 13 }} tickLine={false} axisLine={false} />
            <YAxis tickFormatter={(value) => `$${value}M`} tick={{ fill: "#94a3b8", fontSize: 12 }} tickLine={false} axisLine={false} />
            <ReferenceLine y={0} stroke="#cbd5e1" strokeWidth={2} />
            <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={280}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="financial-stats">
        {stats.map((stat, index) => (
          <div key={index} className="financial-stat-card">
            <span className="financial-stat-label">{stat.label}</span>
            <span className="financial-stat-value">{stat.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FinancialImpactChart;
