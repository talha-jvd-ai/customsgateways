import React from "react";
import "./DonutChartGrid.css";
import DonutChart from "./DonutChart";
const DonutChartGrid = ({ charts }) => (
  <div className="donut-chart-grid">{charts && charts.map((c,i)=><DonutChart key={i} title={c.title} segments={c.segments}/>)}</div>
);
export default DonutChartGrid;