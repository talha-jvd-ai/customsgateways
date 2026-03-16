import React from "react";
import "./AssumptionsList.css";
const AssumptionsList = ({ title, assumptions }) => (
  <div className="assumptions-container">
    <h4 className="assumptions-title">{title}</h4>
    <div className="assumptions-list">
      {assumptions && assumptions.map((a, i) => (
        <div key={i} className="assumption-item"><div className="assumption-number">{i+1}</div><span className="assumption-text">{a}</span></div>
      ))}
    </div>
  </div>
);
export default AssumptionsList;