"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileUp,
  Loader2,
  Upload,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/axios";
import { getErrorMessage } from "@/lib/error";
import type {
  ExtractedQuestion,
  QuestionImport,
} from "@/types/question-import";
import { QuestionImportReview } from "./QuestionImportReview";

interface QuestionImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  examId: string;
  onSuccess: () => void;
}

type ModalStep = "UPLOAD" | "PROCESSING" | "REVIEW" | "SUCCESS";

const MAX_FILE_SIZE_MB = 15;
const ALLOWED_MIME_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
];

export function QuestionImportModal({
  isOpen,
  onClose,
  examId,
  onSuccess,
}: QuestionImportModalProps) {
  const [step, setStep] = useState<ModalStep>("UPLOAD");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [activeImportId, setActiveImportId] = useState<string | null>(null);
  const [importData, setImportData] = useState<QuestionImport | null>(null);

  const [isSaving, setIsSaving] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Clean state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setStep("UPLOAD");
      setSelectedFile(null);
      setUploadError(null);
      setActiveImportId(null);
      setImportData(null);
      setActionError(null);
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }
  }, [isOpen]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  if (!isOpen) return null;

  // ── File Selection & Validation ──────────────────────────────────────────
  const handleFileChange = (file: File | undefined) => {
    setUploadError(null);
    if (!file) return;

    // Size limit
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setUploadError(`File exceeds maximum size of ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }

    // Type limit
    const isAllowedType = ALLOWED_MIME_TYPES.includes(file.type);
    const hasAllowedExt = /\.(pdf|png|jpg|jpeg)$/i.test(file.name);
    if (!isAllowedType && !hasAllowedExt) {
      setUploadError(
        "Unsupported file format. Please upload a PDF, PNG, JPG, or JPEG file."
      );
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

  // ── Polling logic ────────────────────────────────────────────────────────
  const startPolling = (importId: string) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await api.get<QuestionImport>(
          `/api/v1/question-imports/${importId}`
        );
        const data = res.data;
        setImportData(data);

        if (data.status === "NEEDS_REVIEW") {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setStep("REVIEW");
        } else if (data.status === "FAILED") {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          setUploadError(
            data.errorMessage ||
              "AI extraction failed to parse the question paper. Please try again or check the file."
          );
          setStep("UPLOAD");
        }
      } catch (err) {
        // Log silently during polling
        console.warn("Polling question import status error:", err);
      }
    }, 2500);
  };

  // ── Start Upload ─────────────────────────────────────────────────────────
  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploadError(null);
    setStep("PROCESSING");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await api.post<QuestionImport>(
        `/api/v1/exams/${examId}/question-imports`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      const newImport = res.data;
      setActiveImportId(newImport.id);
      setImportData(newImport);

      // Start status polling
      startPolling(newImport.id);
    } catch (err: unknown) {
      setUploadError(getErrorMessage(err));
      setStep("UPLOAD");
    }
  };

  // ── Save Draft ───────────────────────────────────────────────────────────
  const handleSaveDraft = async (
    updatedQuestions: ExtractedQuestion[],
    title?: string
  ) => {
    if (!activeImportId) return;
    setIsSaving(true);
    setActionError(null);

    try {
      const res = await api.patch<QuestionImport>(
        `/api/v1/question-imports/${activeImportId}`,
        {
          title,
          questions: updatedQuestions,
        }
      );
      setImportData(res.data);
    } catch (err: unknown) {
      setActionError(getErrorMessage(err));
    } finally {
      setIsSaving(false);
    }
  };

  // ── Confirm Import ───────────────────────────────────────────────────────
  const handleConfirm = async () => {
    if (!activeImportId) return;
    setIsConfirming(true);
    setActionError(null);

    try {
      await api.post(`/api/v1/question-imports/${activeImportId}/confirm`);
      setStep("SUCCESS");
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: unknown) {
      setActionError(getErrorMessage(err));
    } finally {
      setIsConfirming(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div
        className={`w-full bg-[#10121a] border border-[var(--border-subtle)] rounded-2xl shadow-2xl overflow-hidden flex flex-col transition-all ${
          step === "REVIEW" ? "max-w-4xl max-h-[90vh]" : "max-w-xl max-h-[85vh]"
        }`}
      >
        {/* ── Modal Header ─────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between p-5 border-b border-[var(--border-subtle)] bg-[var(--surface-1)]">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <FileUp className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">
                {step === "REVIEW"
                  ? "Review Extracted Questions"
                  : step === "PROCESSING"
                  ? "Analyzing Question Paper"
                  : step === "SUCCESS"
                  ? "Import Confirmed"
                  : "Import Question Paper with AI"}
              </h2>
              <p className="text-xs text-[var(--text-muted)]">
                {step === "REVIEW"
                  ? "Edit question prompts, types, and marks before creating them in ExamArena."
                  : "Upload a PDF or image paper to extract questions into draft data."}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            disabled={isConfirming}
            className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-[var(--surface-2)] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* ── Modal Body ───────────────────────────────────────────────────── */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {/* STEP 1: UPLOAD */}
          {step === "UPLOAD" && (
            <div className="space-y-6">
              {uploadError && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-start gap-2.5">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{uploadError}</span>
                </div>
              )}

              {/* Drag & Drop Zone */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-2xl cursor-pointer transition-all ${
                  dragActive
                    ? "border-indigo-500 bg-indigo-500/10"
                    : selectedFile
                    ? "border-indigo-500/50 bg-[var(--surface-2)]/60"
                    : "border-[var(--border-subtle)] hover:border-indigo-500/40 bg-[var(--surface-1)]"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
                  className="hidden"
                  onChange={(e) => handleFileChange(e.target.files?.[0])}
                />

                <div className="w-14 h-14 rounded-full bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-3 shadow-glow">
                  <Upload className="w-6 h-6" />
                </div>

                {selectedFile ? (
                  <div className="text-center space-y-1">
                    <p className="font-semibold text-white text-sm">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-[var(--text-muted)]">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Click or drag to replace
                    </p>
                  </div>
                ) : (
                  <div className="text-center space-y-1">
                    <p className="font-semibold text-white text-sm">
                      Click to upload or drag & drop paper
                    </p>
                    <p className="text-xs text-[var(--text-dimmed)]">
                      Supports PDF, PNG, JPG, or JPEG (up to {MAX_FILE_SIZE_MB}MB)
                    </p>
                  </div>
                )}
              </div>

              {/* Upload Tips */}
              <div className="p-4 rounded-xl bg-[var(--surface-2)]/50 border border-[var(--border-subtle)] space-y-1 text-xs text-[var(--text-muted)]">
                <p className="font-semibold text-zinc-300">Phase 1 AI Import Guidelines:</p>
                <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                  <li>Digital PDFs with selectable text yield the best extraction accuracy.</li>
                  <li>Questions will be parsed into editable drafts for your explicit review.</li>
                  <li>Answer keys are not guessed; you have final editorial control.</li>
                </ul>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button variant="ghost" onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={handleUpload}
                  disabled={!selectedFile}
                  className="shadow-glow"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Upload & Extract
                </Button>
              </div>
            </div>
          )}

          {/* STEP 2: PROCESSING */}
          {step === "PROCESSING" && (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-indigo-600/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 animate-pulse">
                <Loader2 className="w-8 h-8 animate-spin" />
              </div>
              <div className="space-y-1.5 max-w-sm">
                <h3 className="font-bold text-white text-base">
                  Analyzing Question Paper...
                </h3>
                <p className="text-xs text-[var(--text-muted)]">
                  ExamArena is extracting questions, options, marks, and sections via Cohere. This typically takes 5–15 seconds.
                </p>
              </div>
            </div>
          )}

          {/* STEP 3: REVIEW */}
          {step === "REVIEW" && importData && (
            <QuestionImportReview
              importData={importData}
              onSaveDraft={handleSaveDraft}
              onConfirm={handleConfirm}
              onCancel={onClose}
              isSaving={isSaving}
              isConfirming={isConfirming}
              error={actionError}
            />
          )}

          {/* STEP 4: SUCCESS */}
          {step === "SUCCESS" && (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-4 animate-fade-in">
              <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <h3 className="font-bold text-white text-lg">
                  Questions Imported Successfully!
                </h3>
                <p className="text-xs text-[var(--text-muted)]">
                  The questions have been added to your exam. Loading updated questions...
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
