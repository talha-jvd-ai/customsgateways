import React from "react";
import "./DonutChart.css";
const DonutChart = ({ title, segments }) => {
  let cum = 0;
  const arc = (pct, off) => {
    const s=(off/100)*360-90, e=((off+pct)/100)*360-90, sr=s*Math.PI/180, er=e*Math.PI/180, r=40, cx=50, cy=50;
    return `M ${cx} ${cy} L ${cx+r*Math.cos(sr)} ${cy+r*Math.sin(sr)} A ${r} ${r} 0 ${pct>50?1:0} 1 ${cx+r*Math.cos(er)} ${cy+r*Math.sin(er)} Z`;
  };
  return (
    <div className="donut-chart-container">
      <h4 className="donut-chart-title">{title}</h4>
      <div className="donut-chart-content">
        <div className="donut-chart-legend">
          {segments && segments.map((s,i)=>(<div key={i} className="legend-item"><div className="legend-color" style={{backgroundColor:s.color}}></div><span className="legend-label">{s.label}</span><span className="legend-value">{s.value}%</span></div>))}
        </div>
        <div className="donut-chart-svg-wrapper">
          <svg viewBox="0 0 100 100" className="donut-chart-svg">
            {segments && segments.map((s,i)=>{const p=s.value,o=cum;cum+=p;return <path key={i} d={arc(p,o)} fill={s.color}/>;})}
            <circle cx="50" cy="50" r="25" fill="white"/>
          </svg>
        </div>
      </div>
    </div>
  );
};
export default DonutChart;