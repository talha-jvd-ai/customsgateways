import React from "react";
import "./StatsGrid.css";
const StatsGrid = ({ title, stats }) => (
  <div className="stats-grid-container">
    {title && <h4 className="stats-grid-title">{title}</h4>}
    <div className="stats-grid">{stats && stats.map((s,i)=>(<div key={i} className="stat-box"><span className="stat-box-label">{s.label}</span><span className="stat-box-value" style={{color:s.color}}>{s.value}</span>{s.description&&<span className="stat-box-description">{s.description}</span>}</div>))}</div>
  </div>
);
export default StatsGrid;