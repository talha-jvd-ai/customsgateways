import React from "react";
import "./StepStatus.css";
const StepStatus = ({ title, steps }) => (
  <div className="step-status-container">
    <h4 className="step-status-title">{title}</h4>
    <div className="step-status-list">
      {steps && steps.map((step, i) => (
        <div key={i} className="step-status-item">
          <div className="step-status-left">
            <span className="step-status-name">{step.name}</span>
          </div>
          <span className={`step-status-value ${step.value ? "status-true" : "status-false"}`}>
            {step.value ? "True" : "False"}
          </span>
        </div>
      ))}
    </div>
  </div>
);
export default StepStatus;