"use client";
import React from "react";
import "./page.css";
import Image from "next/image";
import { usePipeline } from "@/context/PipelineContext";

const Navbar = () => {
  const { enabledSteps, toggleStep } = usePipeline();

  // Step definitions matching backend STEP_DEFINITIONS
  const controls = [
    { id: 1, tag: "P1", name: "Data Extraction" },
    { id: 2, tag: "P2", name: "AI Enrichment" },
    { id: 3, tag: "P3", name: "Tariff Classification" },
    { id: 4, tag: "P4", name: "Customs Value Calculation" },
    { id: 5, tag: "P5", name: "Risk Analysis" },
    { id: 6, tag: "P6", name: "Hub Comparison" },
    { id: 7, tag: "P7", name: "Duties & Taxes" },
    { id: 8, tag: "P8", name: "eCommerce Eligibility" },
    { id: 9, tag: "P9", name: "Integrity & Recovery" },
  ];

  const enabledCount = enabledSteps.length;

  return (
    <div className="navbar">
      <div className="top-navbar">
        <div className="top-navbar-left">
          <h3>CustomsGateways Processing Pipeline</h3>
          <p>Configure and process shipping documentation</p>
        </div>
        <div className="top-navbar-right">
          <Image
            src="/assets/user.png"
            height={50}
            width={50}
            className="userpfp"
            alt="User"
          />
        </div>
      </div>
      <div className="process-pipeline">
        <div className="pipeline-header">
          <h3>Process in Pipeline</h3>
          <span className="step-counter">
            {enabledCount} of {controls.length} steps enabled
          </span>
        </div>
        <div className="toggles">
          {controls.map((control) => {
            const isEnabled = enabledSteps.includes(control.tag);
            return (
              <div className="toggle" key={control.id}>
                <div
                  className={`tag-circle ${isEnabled ? "active" : "inactive"}`}
                >
                  <h2>{control.tag}</h2>
                </div>
                <p>{control.name}</p>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={isEnabled}
                    onChange={() => toggleStep(control.tag)}
                  />
                  <span className="slider"></span>
                </label>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Navbar;
