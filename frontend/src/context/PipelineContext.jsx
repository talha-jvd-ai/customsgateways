"use client";
import { createContext, useContext, useState, useCallback, useRef } from "react";
import { pipelineAPI } from "@/services/api";

const PipelineContext = createContext(null);

export function PipelineProvider({ children }) {
  const [runId, setRunId] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);
  const [enabledSteps, setEnabledSteps] = useState([
    "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9",
  ]);
  const pollingRef = useRef(null);

  /** Upload a file and store the run ID */
  const uploadFile = useCallback(async (file) => {
    setError(null);
    setIsUploading(true);
    try {
      const result = await pipelineAPI.upload(file);
      setRunId(result.run_id);
      setUploadResult(result);
      setPipelineStatus(null);
      setAnalytics(null);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsUploading(false);
    }
  }, []);

  /** Start pipeline execution and begin polling */
  const startPipeline = useCallback(async (customSteps) => {
    if (!runId) return;
    setError(null);
    const stepsToRun = customSteps || enabledSteps;
    try {
      await pipelineAPI.execute(runId, stepsToRun);
      setIsProcessing(true);
      // Start polling
      pollingRef.current = setInterval(async () => {
        try {
          const status = await pipelineAPI.getStatus(runId);
          setPipelineStatus(status);

          if (status.status === "completed" || status.status === "failed") {
            stopPolling();
            setIsProcessing(false);
            // Fetch analytics
            try {
              const analyticsData = await pipelineAPI.getAnalytics(runId);
              setAnalytics(analyticsData);
            } catch {
              // Analytics may not be available yet
            }
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 2000);
    } catch (err) {
      setError(err.message);
      setIsProcessing(false);
    }
  }, [runId, enabledSteps]);

  /** Stop polling */
  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  /** Download step result */
  const downloadResult = useCallback(async (stepId) => {
    if (!runId) return;
    try {
      await pipelineAPI.download(runId, stepId);
    } catch (err) {
      setError(err.message);
    }
  }, [runId]);

  /** Upload corrected data for a step */
  const uploadStepData = useCallback(async (stepId, file) => {
    if (!runId) return;
    try {
      return await pipelineAPI.uploadStepData(runId, stepId, file);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [runId]);

  /** Toggle a step on/off */
  const toggleStep = useCallback((stepTag) => {
    setEnabledSteps((prev) => {
      if (prev.includes(stepTag)) {
        return prev.filter((s) => s !== stepTag);
      }
      return [...prev, stepTag];
    });
  }, []);

  /** Reset pipeline state */
  const resetPipeline = useCallback(() => {
    stopPolling();
    setRunId(null);
    setPipelineStatus(null);
    setAnalytics(null);
    setIsProcessing(false);
    setUploadResult(null);
    setError(null);
  }, [stopPolling]);

  return (
    <PipelineContext.Provider
      value={{
        runId,
        pipelineStatus,
        analytics,
        isProcessing,
        isUploading,
        uploadResult,
        error,
        enabledSteps,
        uploadFile,
        startPipeline,
        stopPolling,
        downloadResult,
        uploadStepData,
        toggleStep,
        setEnabledSteps,
        resetPipeline,
      }}
    >
      {children}
    </PipelineContext.Provider>
  );
}

export const usePipeline = () => {
  const ctx = useContext(PipelineContext);
  if (!ctx) throw new Error("usePipeline must be used within PipelineProvider");
  return ctx;
};
