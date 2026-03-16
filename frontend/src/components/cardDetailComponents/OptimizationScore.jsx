import React from "react";
import "./OptimizationScore.css";
const OptimizationScore = ({ score, label, subtitle }) => (
  <div className="optimization-score-container"><div className="optimization-score-left"><div className="optimization-score-text"><h4 className="optimization-score-label">{label}</h4><span className="optimization-score-subtitle">{subtitle}</span></div></div><div className="optimization-score-value">{score}</div></div>
);
export default OptimizationScore;