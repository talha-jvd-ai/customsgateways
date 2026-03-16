"use client";
import React, { useEffect } from "react";
import "./page.css";
import Navbar from "@/components/navbar/page";
import FileUpload from "@/components/fileUpload/page";
import ProcessingCard from "@/components/processingCard/page";
import MainCards from "@/components/mainCards/page";
import MainCharts from "@/components/mainCharts/page";
import FinancialImpactChart from "@/components/financialImpactChart/page";
import NextActionsTable from "@/components/nextActionsTable/page";
import { useRouter } from "next/navigation";
import { usePipeline } from "@/context/PipelineContext";
import { processingStepsData } from "@/data/processingStepsData";

const DashboardPage = () => {
  const router = useRouter();
  const { pipelineStatus, analytics } = usePipeline();

  useEffect(() => {
    if (typeof window !== "undefined") {
      const loggedIn = localStorage.getItem("Authenticated") === "True";
      if (!loggedIn) {
        router.replace("/login");
      }
    }
  }, [router]);

  // Use live data from API if available, otherwise fallback to static
  const stepsData =
    pipelineStatus?.steps?.map((step) => ({
      id: step.step_id,
      title: step.title,
      description: step.description,
      status: step.status,
      details: step.details || [],
    })) || processingStepsData;

  return (
    <div className="dashboard">
      <Navbar />
      <div className="dashboard-layout">
        <div className="left-side">
          <FileUpload />
        </div>
        <div className="right-side">
          <h3>Processing Assembly</h3>
          <p>Monitor each step with detailed status information</p>
          <div className="cards-container">
            {stepsData.map((step, index) => (
              <ProcessingCard
                key={step.id || index}
                id={step.id}
                title={step.title}
                description={step.description}
                details={step.details}
                status={step.status}
              />
            ))}
          </div>
        </div>
      </div>
      <div className="overall-stats">
        <h3>Data Analytics & Outcomes</h3>
        <p>Review the impact and results of the processing pipeline</p>
        <MainCards data={analytics?.kpi_cards} />
        <MainCharts data={analytics?.before_after_charts} />
        <FinancialImpactChart data={analytics?.financial_impact} />
        <NextActionsTable data={analytics?.next_actions} />
      </div>
    </div>
  );
};

export default DashboardPage;
