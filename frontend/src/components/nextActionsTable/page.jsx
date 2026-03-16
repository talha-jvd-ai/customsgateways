"use client";
import React from "react";
import "./page.css";

const NextActionsTable = ({ data }) => {
  const defaultIssues = [
    { type: "Awaiting pipeline results", count: 0, impact: "—", impactColor: "#f1f5f9", impactText: "#64748b", fixability: "—", fixabilityColor: "#64748b", icon: "check" },
  ];

  const issues = data && data.length > 0
    ? data.map((item) => ({
        type: item.type,
        count: item.count,
        impact: item.impact,
        impactColor: item.impact_color || "#FEF3C7",
        impactText: item.impact_text || "#D97706",
        fixability: item.fixability,
        fixabilityColor: item.fixability_color || "#50CD89",
        icon: item.icon || "check",
      }))
    : defaultIssues;

  const renderIcon = (type, color) => {
    if (type === "check") {
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="8" cy="8" r="7.5" stroke={color} strokeWidth="1" />
          <path d="M11 5.5L7 10L5 8" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    } else if (type === "warning") {
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="8" cy="8" r="7.5" stroke={color} strokeWidth="1" />
          <path d="M8 5V9" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
          <circle cx="8" cy="11" r="0.5" fill={color} />
        </svg>
      );
    }
    return (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="8" cy="8" r="7.5" stroke={color} strokeWidth="1" />
        <path d="M10 6L6 10M6 6L10 10" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    );
  };

  return (
    <div className="next-actions-container">
      <div className="next-actions-header">
        <h3 className="next-actions-title">Next Actions Required</h3>
        <p className="next-actions-subtitle">Priority issues requiring manual review and optimization</p>
      </div>
      <div className="table-container">
        <table className="next-actions-table">
          <thead>
            <tr>
              <th>ISSUE TYPE</th>
              <th>COUNT</th>
              <th>IMPACT</th>
              <th>FIXABILITY</th>
            </tr>
          </thead>
          <tbody>
            {issues.map((issue, index) => (
              <tr key={index}>
                <td className="issue-type">{issue.type}</td>
                <td className="issue-count">{issue.count}</td>
                <td>
                  <span className="impact-badge" style={{ backgroundColor: issue.impactColor, color: issue.impactText }}>
                    {issue.impact}
                  </span>
                </td>
                <td>
                  <div className="fixability-cell">
                    {renderIcon(issue.icon, issue.fixabilityColor)}
                    <span style={{ color: issue.fixabilityColor }}>{issue.fixability}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default NextActionsTable;
