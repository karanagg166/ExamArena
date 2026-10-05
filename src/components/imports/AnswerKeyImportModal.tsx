"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileCheck,
  FileUp,
  Loader2,
  Upload,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/axios";
import { getErrorMessage } from "@/lib/error";
import type {
  AnswerKeyImport,
  MatchedAnswer,
} from "@/types/answer-key-import";
import type { Question } from "@/types/question";
import { AnswerKeyImportReview } from "./AnswerKeyImportReview";

interface AnswerKeyImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  examId: string;
  examQuestions: Question[];
  onSuccess: () => void;
}

type ModalStep = "UPLOAD" | "PROCESSING" | "REVIEW" | "SUCCESS";

const MAX_FILE_SIZE_MB = 15;
const ALLOWED_MIME_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
];

export function AnswerKeyImportModal({
  isOpen,
  onClose,
  examId,
  examQuestions,
  onSuccess,
}: AnswerKeyImportModalProps) {
  const [step, setStep] = useState<ModalStep>("UPLOAD");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [activeImportId, setActiveImportId] = useState<string | null>(null);
  const [importData, setImportData] = useState<AnswerKeyImport | null>(null);

  const [isSaving, setIsSaving] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [updatedCount, setUpdatedCount] = useState<number>(0);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isOpen) {
      setStep("UPLOAD");
      setSelectedFile(null);
      setUploadError(null);
      setActiveImportId(null);
      setImportData(null);
      setActionError(null);
      setUpdatedCount(0);
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }
  }, [isOpen]);

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  if (!isOpen) return null;

  const handleFileChange = (file: File | undefined) => {
    setUploadError(null);
    if (!file) return;

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setUploadError(`File exceeds maximum size of ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }

    const isAllowedType = ALLOWED_MIME_TYPES.includes(file.type);
    const hasAllowedExt = /\.(pdf|png|jpg|jpeg)$/i.test(file.name);

    if (!isAllowedType && !hasAllowedExt) {
      setUploadError("Only PDF, PNG, JPG, or JPEG files are supported.");
      return;
    }

    setSelectedFile(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const startPolling = (importId: string) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    const poll = async () => {
      try {
        const res = await api.get<AnswerKeyImport>(
          `/api/v1/answer-key-imports/${importId}`
        );
        const data = res.data;
        setImportData(data);

        if (data.status === "NEEDS_REVIEW") {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setStep("REVIEW");
        } else if (data.status === "FAILED") {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setUploadError(
            data.errorMessage ||
              "AI answer key extraction failed. Please try a clearer document or digital PDF."
          );
          setStep("UPLOAD");
        }
      } catch (err) {
        console.error("Failed to poll answer key import status:", err);
      }
    };

    pollIntervalRef.current = setInterval(poll, 2000);
    poll();
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;

    setUploadError(null);
    setStep("PROCESSING");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await api.post<AnswerKeyImport>(
        `/api/v1/exams/${examId}/answer-key-imports`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      const importId = res.data.id;
      setActiveImportId(importId);
      setImportData(res.data);
      startPolling(importId);
    } catch (err) {
      setUploadError(getErrorMessage(err));
      setStep("UPLOAD");
    }
  };

  const handleSaveDraft = async (answers: MatchedAnswer[], title?: string) => {
    if (!activeImportId) return;
    setIsSaving(true);
    setActionError(null);

    try {
      const res = await api.patch<AnswerKeyImport>(
        `/api/v1/answer-key-imports/${activeImportId}`,
        {
          title,
          answers,
        }
      );
      setImportData(res.data);
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setIsSaving(false);
    }
  };

  const handleConfirm = async (
    overwriteExisting: boolean,
    answers: MatchedAnswer[]
  ) => {
    if (!activeImportId) return;
    setIsConfirming(true);
    setActionError(null);

    try {
      const res = await api.post<{
        id: string;
        examId: string;
        status: string;
        updatedQuestionsCount: number;
        confirmedAt: string;
      }>(`/api/v1/answer-key-imports/${activeImportId}/confirm`, {
        overwriteExistingAnswers: overwriteExisting,
        answers,
      });

      setUpdatedCount(res.data.updatedQuestionsCount || 0);
      setStep("SUCCESS");
    } catch (err) {
      setActionError(getErrorMessage(err));
    } finally {
      setIsConfirming(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
      <div
        className={`relative w-full bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-2xl overflow-hidden transition-all duration-300 flex flex-col ${
          step === "REVIEW" ? "max-w-4xl max-h-[90vh]" : "max-w-xl"
        }`}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold">
              <FileCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 text-base">
                Import Answer Key & Rubric
              </h3>
              <p className="text-xs text-zinc-500">
                AI extraction & deterministic question mapping
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={step === "PROCESSING" || isConfirming}
            className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-1 rounded-lg transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto">
          {/* ── STEP 1: UPLOAD ────────────────────────────────────────── */}
          {step === "UPLOAD" && (
            <div className="space-y-4">
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                  dragActive
                    ? "border-indigo-500 bg-indigo-500/5"
                    : selectedFile
                    ? "border-emerald-500/50 bg-emerald-500/5"
                    : "border-zinc-300 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-900/50"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  className="hidden"
                  onChange={(e) => handleFileChange(e.target.files?.[0])}
                />

                <div className="flex flex-col items-center justify-center space-y-2">
                  <div className="p-3 bg-white dark:bg-zinc-800 rounded-full shadow-sm text-zinc-500">
                    {selectedFile ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                    ) : (
                      <Upload className="w-6 h-6 text-indigo-500" />
                    )}
                  </div>
                  <div className="text-sm">
                    {selectedFile ? (
                      <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                        {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    ) : (
                      <>
                        <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                          Click to upload
                        </span>{" "}
                        <span className="text-zinc-500">or drag and drop</span>
                      </>
                    )}
                  </div>
                  <p className="text-xs text-zinc-400">
                    PDF, PNG, JPG or JPEG (Max 15MB)
                  </p>
                </div>
              </div>

              {uploadError && (
                <div className="p-3 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800/40 rounded-lg flex items-start gap-2 text-xs text-rose-700 dark:text-rose-300">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{uploadError}</span>
                </div>
              )}

              <div className="bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-200/50 dark:border-indigo-800/30 rounded-lg p-3 text-xs text-zinc-600 dark:text-zinc-400">
                <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                  How Answer Key Import works:
                </span>
                <ol className="list-decimal list-inside mt-1 space-y-1">
                  <li>Your file is securely stored and analyzed with Cohere AI.</li>
                  <li>Extracted answers are deterministically mapped to existing exam questions.</li>
                  <li>You review, resolve ambiguities, and confirm before any answers are applied.</li>
                </ol>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  disabled={!selectedFile}
                  onClick={handleUploadSubmit}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  <FileUp className="w-4 h-4 mr-1.5" />
                  Upload & Analyze
                </Button>
              </div>
            </div>
          )}

          {/* ── STEP 2: PROCESSING ────────────────────────────────────── */}
          {step === "PROCESSING" && (
            <div className="py-12 flex flex-col items-center justify-center space-y-4 text-center">
              <div className="relative">
                <div className="w-16 h-16 rounded-full border-4 border-indigo-100 dark:border-indigo-950 border-t-indigo-600 animate-spin flex items-center justify-center" />
                <FileCheck className="w-6 h-6 text-indigo-600 absolute inset-0 m-auto" />
              </div>

              <div className="space-y-1">
                <h4 className="font-semibold text-zinc-900 dark:text-zinc-100 text-base">
                  Analyzing Answer Key...
                </h4>
                <p className="text-xs text-zinc-500 max-w-sm">
                  Extracting solutions, option keys, and marking rubrics with Cohere AI, then mapping to exam questions.
                </p>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-zinc-400 font-mono">
                <Loader2 className="w-3 h-3 animate-spin" />
                Status: {importData?.status || "PROCESSING"}
              </div>
            </div>
          )}

          {/* ── STEP 3: REVIEW ────────────────────────────────────────── */}
          {step === "REVIEW" && importData && (
            <AnswerKeyImportReview
              importData={importData}
              examQuestions={examQuestions}
              onSaveDraft={handleSaveDraft}
              onConfirm={handleConfirm}
              onCancel={onClose}
              isConfirming={isConfirming}
              isSaving={isSaving}
              error={actionError}
            />
          )}

          {/* ── STEP 4: SUCCESS ───────────────────────────────────────── */}
          {step === "SUCCESS" && (
            <div className="py-8 flex flex-col items-center justify-center space-y-4 text-center">
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <div className="space-y-1">
                <h4 className="font-semibold text-zinc-900 dark:text-zinc-100 text-lg">
                  Answer Key Successfully Applied!
                </h4>
                <p className="text-xs text-zinc-500 max-w-sm">
                  Successfully updated answer keys, model answers, and rubrics on{" "}
                  <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                    {updatedCount} question{updatedCount === 1 ? "" : "s"}
                  </span>.
                </p>
              </div>
              <Button
                onClick={() => {
                  onSuccess();
                  onClose();
                }}
                className="bg-indigo-600 hover:bg-indigo-700 text-white mt-2"
              >
                Done
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
