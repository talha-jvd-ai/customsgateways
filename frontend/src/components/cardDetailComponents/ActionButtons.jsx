import React from "react";
import "./ActionButtons.css";
import { usePipeline } from "@/context/PipelineContext";
const ActionButtons = ({ buttons }) => {
  const { downloadResult, runId } = usePipeline();
  const handleClick = (btn) => {
    if (btn.label === "Download Result" && runId) downloadResult(btn.stepId || "P1");
    else if (btn.onClick) btn.onClick();
  };
  return (
    <div className="action-buttons-container">
      {buttons && buttons.map((btn, i) => (
        <button key={i} className={`action-btn ${btn.variant || "secondary"}`} onClick={() => handleClick(btn)}>
          {btn.label}
        </button>
      ))}
    </div>
  );
};
export default ActionButtons;