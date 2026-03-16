"use client";
import React from "react";
import "./page.css";

const MainCharts = ({ data }) => {
  const defaultCharts = [
    {
      title: "Data Quality - Before vs After",
      categories: [
        { name: "Product Info", before: 0, after: 0 },
        { name: "Classification", before: 0, after: 0 },
        { name: "Origin Data", before: 0, after: 0 },
        { name: "Value Data", before: 0, after: 0 },
      ],
    },
    {
      title: "Product Understanding - Before vs After",
      categories: [
        { name: "HS Accuracy", before: 0, after: 0 },
        { name: "Description", before: 0, after: 0 },
        { name: "Category Match", before: 0, after: 0 },
        { name: "Completeness", before: 0, after: 0 },
      ],
    },
  ];

  const chartsData = data && data.length > 0 ? data : defaultCharts;

  return (
    <div className="main-charts-container">
      {chartsData.map((chart, chartIndex) => (
        <div key={chartIndex} className="main-chart-card">
          <h4 className="main-chart-title">{chart.title}</h4>
          <div className="chart-content">
            <div className="chart-y-axis">
              <span className="y-axis-label">100</span>
              <span className="y-axis-label">75</span>
              <span className="y-axis-label">50</span>
              <span className="y-axis-label">25</span>
              <span className="y-axis-label">0</span>
            </div>
            <div className="chart-area">
              <div className="chart-grid">
                <div className="grid-line"></div>
                <div className="grid-line"></div>
                <div className="grid-line"></div>
                <div className="grid-line"></div>
                <div className="grid-line"></div>
              </div>
              <div className="chart-bars">
                {chart.categories.map((category, index) => (
                  <div key={index} className="bar-group">
                    <div className="bars-container">
                      <div className="bar before-bar" style={{ height: `${category.before}%` }}></div>
                      <div className="bar after-bar" style={{ height: `${category.after}%` }}></div>
                    </div>
                    <span className="bar-label">{category.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="chart-legend">
            <div className="legend-item">
              <div className="legend-dot before-dot"></div>
              <span className="legend-label">Before</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot after-dot"></div>
              <span className="legend-label">After</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MainCharts;
