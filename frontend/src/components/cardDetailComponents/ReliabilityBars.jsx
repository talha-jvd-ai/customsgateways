import React from "react";
import "./ReliabilityBars.css";
const ReliabilityBars = ({ title, items }) => (
  <div className="reliability-bars-container">
    <h4 className="reliability-bars-title">{title}</h4>
    <div className="reliability-bars-content"><div className="reliability-bars-list">{items && items.map((item,i)=>(<div key={i} className="reliability-bar-item"><div className="reliability-bar-header"><span className="reliability-bar-label">{item.label}</span><span className="reliability-bar-percentage">{item.percentage}%</span></div><div className="reliability-bar-track"><div className="reliability-bar-fill" style={{width:`${item.percentage}%`,backgroundColor:item.color}}/></div></div>))}</div></div>
  </div>
);
export default ReliabilityBars;