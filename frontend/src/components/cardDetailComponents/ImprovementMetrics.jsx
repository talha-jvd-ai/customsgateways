import React from "react";
import "./ImprovementMetrics.css";
const ImprovementMetrics = ({ title, metrics }) => (
  <div className="improvement-metrics-container">{title && <h4 className="improvement-metrics-title">{title}</h4>}<div className="improvement-metrics-list">{metrics && metrics.map((m,i)=>(<div key={i} className="improvement-metric-card"><div className="improvement-metric-header"><div className="improvement-metric-text"><h5 className="improvement-metric-label">{m.label}</h5><span className="improvement-metric-description">{m.description}</span></div><span className="improvement-metric-value" style={{color:m.color}}>{m.value}</span></div><div className="improvement-metric-bar-container"><span className="improvement-metric-bar-label">{m.barLabel}</span><div className="improvement-metric-bar-track"><div className="improvement-metric-bar-fill" style={{width:`${m.percentage}%`,backgroundColor:m.color}}/></div></div></div>))}</div></div>
);
export default ImprovementMetrics;