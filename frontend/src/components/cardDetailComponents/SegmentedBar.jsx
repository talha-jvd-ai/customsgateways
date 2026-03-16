import React from "react";
import "./SegmentedBar.css";
const SegmentedBar = ({ title, segments }) => (
  <div className="segmented-bar-container">
    <h4 className="segmented-bar-title">{title}</h4>
    <div className="segmented-bar-content">
      <div className="segmented-bar-track">{segments && segments.map((s,i)=><div key={i} className="segmented-bar-segment" style={{width:`${s.percentage}%`,backgroundColor:s.color}}/>)}</div>
      <div className="segmented-bar-legend">{segments && segments.map((s,i)=>(<div key={i} className="segmented-legend-item"><div className="segmented-legend-header"><div className="segmented-legend-color" style={{backgroundColor:s.color}}></div><span className="segmented-legend-label">{s.label}</span></div><span className="segmented-legend-value">{s.percentage}%</span>{s.description&&<span className="segmented-legend-description">{s.description}</span>}</div>))}</div>
    </div>
  </div>
);
export default SegmentedBar;