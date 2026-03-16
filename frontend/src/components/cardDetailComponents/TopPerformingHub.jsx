import React from "react";
import "./TopPerformingHub.css";
const TopPerformingHub = ({ hubName, score, volume }) => (
  <div className="top-performing-hub-container"><div className="top-hub-left"><div className="top-hub-info"><h4 className="top-hub-title">Top Performing Hub</h4><p className="top-hub-details">Score: {score} Volume: {volume}%</p></div></div><div className="top-hub-name">{hubName}</div></div>
);
export default TopPerformingHub;