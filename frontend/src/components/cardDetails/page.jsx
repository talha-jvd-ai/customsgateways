"use client";
import React from "react";
import "./page.css";
import ProgressBar from "@/components/cardDetailComponents/ProgressBar";
import StepStatus from "@/components/cardDetailComponents/StepStatus";
import KPICircle from "@/components/cardDetailComponents/KPICircle";
import InfoBox from "@/components/cardDetailComponents/InfoBox";
import ActionButtons from "@/components/cardDetailComponents/ActionButtons";
import AISuggestion from "@/components/cardDetailComponents/AISuggestion";
import ConfidenceBars from "@/components/cardDetailComponents/ConfidenceBars";
import AssumptionsList from "@/components/cardDetailComponents/AssumptionsList";
import StatDisplay from "@/components/cardDetailComponents/StatDisplay";
import DonutChartGrid from "@/components/cardDetailComponents/DonutChartGrid";
import StatsGrid from "@/components/cardDetailComponents/StatsGrid";
import SegmentedBar from "@/components/cardDetailComponents/SegmentedBar";
import FXSensitivity from "@/components/cardDetailComponents/FXSensitivity";
import ReliabilityBars from "@/components/cardDetailComponents/ReliabilityBars";
import TopPerformingHub from "@/components/cardDetailComponents/TopPerformingHub";
import HubTable from "@/components/cardDetailComponents/HubTable";
import HubComparison from "@/components/cardDetailComponents/HubComparison";
import ExposureDistribution from "@/components/cardDetailComponents/ExposureDistribution";
import AutomationInsights from "@/components/cardDetailComponents/AutomationInsights";
import OptimizationScore from "@/components/cardDetailComponents/OptimizationScore";
import ImprovementMetrics from "@/components/cardDetailComponents/ImprovementMetrics";

const CardDetails = ({ details, isExpanded }) => {
  const renderComponent = (component, index) => {
    switch (component.type) {
      case "progress": return <ProgressBar key={index} label={component.label} percentage={component.percentage} />;
      case "stepStatus": return <StepStatus key={index} title={component.title} steps={component.steps} />;
      case "kpi": return <KPICircle key={index} label={component.label} percentage={component.percentage} />;
      case "info": return <InfoBox key={index} message={component.message} />;
      case "buttons": return <ActionButtons key={index} buttons={component.buttons} />;
      case "aiSuggestion": return <AISuggestion key={index} title={component.title} description={component.description} />;
      case "confidenceBars": return <ConfidenceBars key={index} bars={component.bars} />;
      case "assumptions": return <AssumptionsList key={index} title={component.title} assumptions={component.assumptions} />;
      case "statDisplay": return <StatDisplay key={index} label={component.label} value={component.value} />;
      case "donutChartGrid": return <DonutChartGrid key={index} charts={component.charts} />;
      case "statsGrid": return <StatsGrid key={index} title={component.title} stats={component.stats} />;
      case "segmentedBar": return <SegmentedBar key={index} title={component.title} segments={component.segments} />;
      case "fxSensitivity": return <FXSensitivity key={index} title={component.title} description={component.description} percentage={component.percentage} />;
      case "reliabilityBars": return <ReliabilityBars key={index} title={component.title} items={component.items} />;
      case "topPerformingHub": return <TopPerformingHub key={index} hubName={component.hubName} score={component.score} volume={component.volume} />;
      case "hubTable": return <HubTable key={index} hubs={component.hubs} />;
      case "hubComparison": return <HubComparison key={index} comparisons={component.comparisons} />;
      case "exposureDistribution": return <ExposureDistribution key={index} title={component.title} distributions={component.distributions} />;
      case "automationInsights": return <AutomationInsights key={index} title={component.title} insights={component.insights} />;
      case "optimizationScore": return <OptimizationScore key={index} score={component.score} label={component.label} subtitle={component.subtitle} />;
      case "improvementMetrics": return <ImprovementMetrics key={index} title={component.title} metrics={component.metrics} />;
      case "simple": return (<div key={index} className="detail-row"><span className="detail-label">{component.label}:</span><span className="detail-value">{component.value}</span></div>);
      default: return null;
    }
  };

  return (
    <div className={`card-details ${isExpanded ? "expanded" : ""}`}>
      <div className="details-content">
        {Array.isArray(details) ? details.map((c, i) => renderComponent(c, i))
          : details ? Object.entries(details).map(([k, v], i) => (
              <div key={i} className="detail-row">
                <span className="detail-label">{k.replace(/([A-Z])/g, " $1").trim()}:</span>
                <span className="detail-value">{v}</span>
              </div>)) : null}
      </div>
    </div>
  );
};
export default CardDetails;
