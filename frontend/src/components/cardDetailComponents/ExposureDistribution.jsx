import React from "react";
import "./ExposureDistribution.css";
const ExposureDistribution = ({ title, distributions }) => (
  <div className="exposure-distribution-container"><h4 className="exposure-distribution-title">{title}</h4><div className="exposure-distribution-grid">{distributions && distributions.map((d,i)=>(<div key={i} className={`exposure-dist-box exposure-${d.level}`}><span className="exposure-dist-label">{d.label}</span><span className="exposure-dist-count">{d.count}</span><span className="exposure-dist-percentage">{d.percentage}%</span></div>))}</div></div>
);
export default ExposureDistribution;