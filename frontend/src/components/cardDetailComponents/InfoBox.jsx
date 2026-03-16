import React from "react";
import "./InfoBox.css";
const InfoBox = ({ message }) => (
  <div className="info-box">
    <span className="info-message">{message}</span>
  </div>
);
export default InfoBox;