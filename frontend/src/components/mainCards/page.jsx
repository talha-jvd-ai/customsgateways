"use client";
import React from "react";
import "./page.css";

const MainCards = ({ data }) => {
  // Default hardcoded data as fallback
  const defaultCards = [
    { title: "Data Quality Change", value: "—", trend: "", trendDirection: "up", iconColor: "#50CD89", iconBg: "#50CD8920" },
    { title: "Automation Increase", value: "—", trend: "", trendDirection: "up", iconColor: "#668DC9", iconBg: "#668DC920" },
    { title: "Manual Reduction", value: "—", trend: "", trendDirection: "down", iconColor: "#50CD89", iconBg: "#50CD8920" },
  ];

  // Map API data to card format if available
  const cardsData = data && data.length > 0
    ? data.map((item, idx) => ({
        title: item.title,
        value: item.value,
        trend: item.trend || "",
        trendDirection: item.trend_direction || "up",
        iconColor: idx === 1 ? "#668DC9" : "#50CD89",
        iconBg: idx === 1 ? "#668DC920" : "#50CD8920",
      }))
    : defaultCards;

  const renderIcon = (direction, color) => {
    if (direction === "up") {
      return (
        <svg width="21" height="32" viewBox="0 0 21 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10.517 24V9.98864L5.13068 15.392L3.80114 14.0795L11.4545 6.44318L19.0909 14.0795L17.7955 15.392L12.392 9.98864V24H10.517Z" fill={color}/>
        </svg>
      );
    }
    return (
      <svg width="21" height="32" viewBox="0 0 21 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12.392 6.54545V20.5568L17.7784 15.1534L19.108 16.4659L11.4545 24.1023L3.81818 16.4659L5.11364 15.1534L10.517 20.5568V6.54545H12.392Z" fill={color}/>
      </svg>
    );
  };

  const renderTrendIcon = (direction, color) => {
    if (direction === "up") {
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M14.6663 4.6665L8.99967 10.3332L5.66634 6.99984L1.33301 11.3332" stroke={color} strokeWidth="1.33333" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M10.667 4.6665H14.667V8.6665" stroke={color} strokeWidth="1.33333" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      );
    }
    return (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M14.6673 11.3332L9.00065 5.6665L5.66732 8.99984L1.33398 4.6665" stroke={color} strokeWidth="1.33333" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M10.666 11.3335H14.666V7.3335" stroke={color} strokeWidth="1.33333" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    );
  };

  return (
    <div className="main-cards-container">
      {cardsData.map((card, index) => (
        <div key={index} className="main-card">
          <div className="main-card-content">
            <div className="main-card-left">
              <h4 className="main-card-title">{card.title}</h4>
              <div className="main-card-value">{card.value}</div>
              {card.trend && (
                <div className="main-card-trend">
                  {renderTrendIcon(card.trendDirection, "#50CD89")}
                  <span className="main-card-trend-value" style={{ color: "#50CD89" }}>
                    {card.trend}
                  </span>
                  <span className="main-card-trend-label">vs last month</span>
                </div>
              )}
            </div>
            <div className="main-card-icon" style={{ backgroundColor: card.iconBg }}>
              {renderIcon(card.trendDirection, card.iconColor)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MainCards;
