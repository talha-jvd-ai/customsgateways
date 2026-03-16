import React from "react";
import "./page.css";
const InputField = ({ label, type = "text", name, placeholder }) => (
  <div className="inputDiv">
    <label htmlFor={name}>{label}</label>
    <input type={type} name={name} id={name} placeholder={placeholder} />
  </div>
);
export default InputField;
