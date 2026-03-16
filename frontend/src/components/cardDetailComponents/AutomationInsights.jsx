import React from "react";
import "./AutomationInsights.css";
const AutomationInsights = ({ title, insights }) => (
  <div className="automation-insights-container"><h4 className="automation-insights-title">{title}</h4><div className="automation-insights-list">{insights && insights.map((ins,i)=>(<div key={i} className="automation-insight-item"><div className="insight-bullet" style={{backgroundColor:ins.color}}></div><p className="insight-text"><span className="insight-highlight" style={{color:ins.color}}>{ins.highlight}</span> {ins.text}</p></div>))}</div></div>
);
export default AutomationInsights;