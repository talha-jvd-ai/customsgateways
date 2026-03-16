import React from "react";
import "./KPICircle.css";
const KPICircle = ({ label, percentage }) => {
  const r = 30, c = 2 * Math.PI * r, offset = c - (percentage / 100) * c;
  return (
    <div className="kpi-circle-container">
      <span className="kpi-label">{label}</span>
      <div className="kpi-circle-wrapper">
        <svg className="kpi-circle-svg" width="70" height="70" viewBox="0 0 70 70">
          <circle cx="35" cy="35" r={r} fill="none" stroke="#e2e8f0" strokeWidth="6"/>
          <circle cx="35" cy="35" r={r} fill="none" stroke="#50CD89" strokeWidth="6"
            strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round" transform="rotate(-90 35 35)"/>
        </svg>
        <div className="kpi-percentage">{percentage}%</div>
      </div>
    </div>
  );
};
export default KPICircle;