"use client";
import React, { useState } from "react";
import "./page.css";
import CardDetails from "@/components/cardDetails/page";
const ProcessingCard = ({ id, title, description, details, status }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  return (
    <div className={`processing-card ${status === "processing" ? "processing-active" : ""}`}>
      <div className="card-header" onClick={() => setIsExpanded(prev => !prev)}>
        <div className="card-left">
          <div className={`card-badge ${status === "completed" ? "badge-completed" : status === "processing" ? "badge-processing" : ""}`}>{id}</div>
          <div className="card-info">
            <h4>{title}</h4>
            <p>{description}</p>
          </div>
        </div>
        <button className="expand-btn">{isExpanded ? "−" : "+"}</button>
      </div>
      <CardDetails details={details} isExpanded={isExpanded} />
    </div>
  );
};
export default ProcessingCard;
