import React from "react";
import "./ProgressBar.css";
const ProgressBar = ({ label, percentage }) => (
  <div className="progress-bar-container">
    <div className="progress-header">
      <span className="progress-label">{label}</span>
      <span className="progress-percentage">{percentage}%</span>
    </div>
    <div className="progress-bar-track">
      <div className="progress-bar-fill" style={{ width: `${percentage}%` }}></div>
    </div>
  </div>
);
export default ProgressBar;