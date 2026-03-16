"use client";
import React, { useState, useRef } from "react";
import "./page.css";
import { usePipeline } from "@/context/PipelineContext";

const FileUpload = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);
  const {
    uploadFile,
    startPipeline,
    resetPipeline,
    isProcessing,
    isUploading,
    uploadResult,
    runId,
    error,
    enabledSteps,
  } = usePipeline();

  const handleFileSelect = async (file) => {
    if (!file) return;
    setSelectedFile(file);
    // Upload immediately on file selection
    try {
      await uploadFile(file);
    } catch (err) {
      console.error("Upload failed:", err);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) handleFileSelect(file);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  };

  const handleStartProcess = async () => {
    if (!runId) return;
    try {
      await startPipeline(enabledSteps);
    } catch (err) {
      console.error("Process failed:", err);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    resetPipeline();
  };

  const isUploaded = !!uploadResult;
  const canStart = isUploaded && !isProcessing && !isUploading;

  return (
    <div className="file-upload-container">
      <div className="file-upload-header">
        <h3>Document Ingestion</h3>
        <p>Upload and preview your shipping documents</p>
      </div>

      {!isUploaded ? (
        <div
          className={`drop-zone ${isDragging ? "dragging" : ""}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="upload-icon">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M37.0999 14.7667C36.7499 8.50002 32.0999 3.60002 26.4833 3.60002H18.1499C17.6462 3.07767 17.0432 2.66118 16.3764 2.37498C15.7095 2.08878 14.9922 1.93863 14.2666 1.93335H10.9333C9.76464 1.93551 8.60798 2.16867 7.52979 2.6194C6.4516 3.07014 5.47314 3.72957 4.65068 4.55977C3.82823 5.38997 3.178 6.37456 2.73739 7.45693C2.29677 8.53931 2.07447 9.6981 2.08326 10.8667V27.8667C2.08326 30.5188 3.13683 33.0624 5.01219 34.9378C6.88755 36.8131 9.43109 37.8667 12.0833 37.8667H27.8833C30.5354 37.8667 33.079 36.8131 34.9543 34.9378C36.8297 33.0624 37.8833 30.5188 37.8833 27.8667V18.9333C37.761 17.5219 37.4986 16.1261 37.0999 14.7667Z" fill="#4B5779" />
              <path d="M25.867 21.4333C25.7611 21.5596 25.6313 21.6637 25.4851 21.7396C25.3388 21.8156 25.179 21.8618 25.0148 21.8758C24.8506 21.8897 24.6853 21.871 24.5284 21.8209C24.3714 21.7707 24.2259 21.6899 24.1003 21.5833L21.4336 19.25V27.7667C21.4336 28.0982 21.3019 28.4161 21.0675 28.6505C20.8331 28.885 20.5151 29.0167 20.1836 29.0167C19.8521 29.0167 19.5342 28.885 19.2997 28.6505C19.0653 28.4161 18.9336 28.0982 18.9336 27.7667V19.1333L15.8503 21.6667C15.6 21.8538 15.2872 21.9374 14.9769 21.9001C14.6666 21.8629 14.3826 21.7077 14.1836 21.4667C13.9773 21.2022 13.8827 20.8675 13.9201 20.5342C13.9575 20.2009 14.1239 19.8955 14.3836 19.6833L19.4003 15.5L19.5836 15.4L19.7336 15.3167C20.0232 15.2049 20.344 15.2049 20.6336 15.3167L20.8003 15.4167L21.0003 15.5333L25.7336 19.65C25.9835 19.8715 26.1372 20.1816 26.1621 20.5146C26.187 20.8476 26.0811 21.1771 25.867 21.4333Z" fill="#4B5779" />
            </svg>
          </div>
          <h3 className="upload-title">Upload Document</h3>
          <p className="upload-subtitle">Choose file or drag and drop</p>
          <input
            type="file"
            id="file-input"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".csv,.xlsx,.xls,.txt"
            style={{ display: "none" }}
          />
          <label htmlFor="file-input" className="choose-file-btn">
            {isUploading ? "Uploading..." : "Choose File"}
          </label>
          {selectedFile && !uploadResult && !isUploading && (
            <p className="selected-file">Selected: {selectedFile.name}</p>
          )}
          {isUploading && (
            <p className="selected-file">Uploading {selectedFile?.name}...</p>
          )}
        </div>
      ) : (
        <div className="uploaded-state">
          <div className="uploaded-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="#4B5779" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M14 2V8H20" stroke="#4B5779" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <p className="uploaded-filename">
            {uploadResult?.filename || selectedFile?.name}
          </p>
          <p className="uploaded-info">
            {uploadResult.total_rows} rows detected
          </p>
          <button className="upload-again-btn" onClick={handleReset}>
            Upload Again
          </button>
        </div>
      )}

      {error && <p className="error-text">{error}</p>}

      <button
        className="start-process-btn"
        disabled={!canStart}
        onClick={handleStartProcess}
      >
        {isUploading
          ? "Uploading..."
          : isProcessing
            ? "Processing..."
            : canStart
              ? "Start process"
              : "Upload a file first"}
      </button>
    </div>
  );
};

export default FileUpload;