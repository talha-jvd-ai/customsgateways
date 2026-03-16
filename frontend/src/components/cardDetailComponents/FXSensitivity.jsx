import React from "react";
import "./FXSensitivity.css";
const FXSensitivity = ({ title, description, percentage }) => (
  <div className="fx-sensitivity-container"><div className="fx-sensitivity-left"><h4 className="fx-sensitivity-title">{title}</h4><p className="fx-sensitivity-description">{description}</p></div><div className="fx-sensitivity-percentage">{percentage}%</div></div>
);
export default FXSensitivity;