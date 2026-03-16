import React from "react";
import "./AISuggestion.css";
const AISuggestion = ({ title, description }) => (
  <div className="ai-suggestion-container">
    <h4 className="ai-suggestion-title">{title}</h4>
    <p className="ai-suggestion-description">{description}</p>
  </div>
);
export default AISuggestion;