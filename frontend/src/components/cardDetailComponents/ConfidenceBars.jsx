import React from "react";
import "./ConfidenceBars.css";
const ConfidenceBars = ({ bars }) => (
  <div className="confidence-bars-container">
    {bars && bars.map((bar, i) => (
      <div key={i} className="confidence-bar-item">
        <span className="confidence-label">Confidence</span>
        <span className="confidence-value">{bar.value}</span>
        <div className="confidence-bar-track">
          <div className="confidence-bar-fill" style={{ width: `${bar.percentage}%`, backgroundColor: bar.color || "#50CD89" }}></div>
        </div>
      </div>
    ))}
  </div>
);
export default ConfidenceBars;