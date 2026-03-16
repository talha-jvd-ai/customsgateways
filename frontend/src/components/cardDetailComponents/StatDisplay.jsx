import React from "react";
import "./StatDisplay.css";
const StatDisplay = ({ label, value }) => (
  <div className="stat-display-container">
    <span className="stat-display-label">{label}</span>
    <span className="stat-display-value">{value}</span>
  </div>
);
export default StatDisplay;