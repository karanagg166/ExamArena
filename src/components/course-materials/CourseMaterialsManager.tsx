"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Upload,
  FileText,
  RefreshCw,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Clock,
  BookOpen,
  Plus,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/loading";
import {
  courseMaterialsApi,
} from "@/lib/api/course-materials";
import type {
  CourseMaterialItem,
  CourseMaterialDocumentType,
} from "@/types/course-materials";
import { useSchoolStore, useSchoolClassStore } from "@/stores";
import { getErrorMessage } from "@/lib/error";

const SUBJECTS = [
  { value: "SCIENCE", label: "Science (Physics, Chemistry, Biology)" },
  { value: "MATHS", label: "Mathematics" },
  { value: "LITERATURE", label: "Literature / English" },
  { value: "HISTORY", label: "History & Social Studies" },
  { value: "ART", label: "Art & Design" },
  { value: "MUSIC", label: "Music" },
  { value: "PHYSICAL_EDUCATION", label: "Physical Education" },
  { value: "OTHER", label: "Other Materials" },
];

const DOC_TYPES: { value: CourseMaterialDocumentType; label: string }[] = [
  { value: "TEXTBOOK", label: "Textbook / Reference Book" },
  { value: "NOTES", label: "Teacher Notes / Handouts" },
  { value: "SYLLABUS", label: "Curriculum Syllabus" },
  { value: "ASSIGNMENT", label: "Assignment / Homework" },
  { value: "OTHER", label: "Other Resource" },
];

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

export function CourseMaterialsManager() {
  const { school } = useSchoolStore();
  const { classes, fetchClassesBySchool } = useSchoolClassStore();

  const [materials, setMaterials] = useState<CourseMaterialItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterSubject, setFilterSubject] = useState<string>("ALL");
  const [refreshingId, setRefreshingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Upload modal state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("SCIENCE");
  const [docType, setDocType] = useState<CourseMaterialDocumentType>("TEXTBOOK");
  const [classId, setClassId] = useState<string>("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    if (school?.id) {
      fetchClassesBySchool(school.id);
    }
  }, [school?.id, fetchClassesBySchool]);

  const loadMaterials = useCallback(async () => {
    try {
      setLoading(true);
      setActionError(null);
      const params = filterSubject !== "ALL" ? { subject: filterSubject } : undefined;
      const res = await courseMaterialsApi.list(params);
      setMaterials(res.items || []);
    } catch (err: unknown) {
      setActionError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [filterSubject]);

  useEffect(() => {
    loadMaterials();
  }, [loadMaterials]);

  const handleRefreshStatus = async (item: CourseMaterialItem) => {
    setRefreshingId(item.id);
    setActionError(null);
    setActionSuccess(null);
    try {
      const refreshed = await courseMaterialsApi.refreshStatus(item.id);
      setMaterials((prev) =>
        prev.map((m) =>
          m.id === item.id
            ? {
                ...m,
                status: refreshed.status,
                processingError: refreshed.processing_error,
                searchSphereDocumentId: refreshed.search_sphere_document_id ?? m.searchSphereDocumentId,
              }
            : m,
        ),
      );
      setActionSuccess(`Status for "${item.title}" updated to ${refreshed.status}.`);
    } catch (err: unknown) {
      setActionError(getErrorMessage(err));
    } finally {
      setRefreshingId(null);
    }
  };

  const handleDelete = async (item: CourseMaterialItem) => {
    if (!window.confirm(`Are you sure you want to delete "${item.title}"? This will also remove it from the Search-Sphere index.`)) {
      return;
    }

    setDeletingId(item.id);
    setActionError(null);
    setActionSuccess(null);
    try {
      await courseMaterialsApi.delete(item.id);
      setMaterials((prev) => prev.filter((m) => m.id !== item.id));
      setActionSuccess(`"${item.title}" was successfully deleted.`);
    } catch (err: unknown) {
      setActionError(getErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setUploadError("Please select a PDF document to upload.");
      return;
    }
    if (!title.trim()) {
      setUploadError("Please provide a title for the material.");
      return;
    }

    setUploading(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title.trim());
      formData.append("subject", subject);
      formData.append("document_type", docType);
      if (classId) formData.append("class_id", classId);
      if (description.trim()) formData.append("description", description.trim());

      const newItem = await courseMaterialsApi.upload(formData);
      setMaterials((prev) => [newItem, ...prev]);
      setActionSuccess(`Successfully uploaded "${newItem.title}". Search-Sphere is now indexing the document.`);
      setIsUploadOpen(false);
      // Reset form
      setTitle("");
      setDescription("");
      setFile(null);
      setClassId("");
    } catch (err: unknown) {
      setUploadError(getErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label htmlFor="subject-filter" className="text-xs font-semibold text-muted-foreground whitespace-nowrap">
            Filter by Subject:
          </label>
          <select
            id="subject-filter"
            value={filterSubject}
            onChange={(e) => setFilterSubject(e.target.value)}
            className="rounded-lg border border-input bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="ALL">All Subjects</option>
            {SUBJECTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <Button
          onClick={() => setIsUploadOpen(true)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs sm:text-sm flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="h-4 w-4" />
          <span>Upload Material</span>
        </Button>
      </div>

      {/* Notifications */}
      {actionError && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3.5 flex items-start gap-3 text-red-300 text-xs sm:text-sm">
          <AlertCircle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-red-200">Action Failed</p>
            <p className="mt-0.5 text-red-300/90">{actionError}</p>
          </div>
          <button onClick={() => setActionError(null)} className="text-red-400 hover:text-red-200">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {actionSuccess && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3.5 flex items-start gap-3 text-emerald-300 text-xs sm:text-sm">
          <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-emerald-200">Success</p>
            <p className="mt-0.5 text-emerald-300/90">{actionSuccess}</p>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-emerald-200">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Materials List */}
      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Spinner className="h-8 w-8 text-indigo-500" />
        </div>
      ) : materials.length === 0 ? (
        <Card className="border border-dashed border-border p-8 text-center bg-card/40">
          <div className="flex flex-col items-center justify-center space-y-3">
            <BookOpen className="h-10 w-10 text-muted-foreground/60" />
            <div className="space-y-1">
              <h3 className="font-semibold text-foreground text-sm">No course materials found</h3>
              <p className="text-xs text-muted-foreground max-w-sm">
                Upload PDFs such as textbooks, teacher notes, or syllabi so students and staff can perform AI-grounded Q&A.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsUploadOpen(true)}
              className="mt-2 text-xs"
            >
              Upload your first document
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {materials.map((item) => {
            const isProcessing = item.status === "PROCESSING";
            const isFailed = item.status === "FAILED";
            const isReady = item.status === "READY";

            return (
              <Card
                key={item.id}
                className="border border-border/80 bg-card hover:border-border transition-colors shadow-sm"
              >
                <CardContent className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-start gap-3.5 min-w-0">
                    <div className="rounded-lg bg-indigo-500/10 p-2.5 text-indigo-400 shrink-0 mt-0.5">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div className="space-y-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h4 className="font-semibold text-foreground text-sm truncate" title={item.title}>
                          {item.title}
                        </h4>
                        <Badge variant="outline" className="text-[10px] uppercase font-mono tracking-wider">
                          {item.subject}
                        </Badge>
                        <Badge variant="secondary" className="text-[10px]">
                          {item.documentType}
                        </Badge>
                      </div>

                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                        <span className="truncate max-w-[200px]" title={item.originalFileName}>
                          {item.originalFileName}
                        </span>
                        <span>•</span>
                        <span>{formatBytes(item.fileSize)}</span>
                        <span>•</span>
                        <span>{new Date(item.createdAt).toLocaleDateString()}</span>
                      </div>

                      {item.description && (
                        <p className="text-xs text-muted-foreground/90 line-clamp-1 mt-1">
                          {item.description}
                        </p>
                      )}

                      {isFailed && item.processingError && (
                        <p className="text-xs text-red-400 mt-1 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3 shrink-0" />
                          <span>{item.processingError}</span>
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Status & Actions */}
                  <div className="flex items-center gap-2.5 sm:self-center shrink-0 border-t sm:border-t-0 pt-3 sm:pt-0">
                    {isReady && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Ready</span>
                      </span>
                    )}

                    {isProcessing && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        <Clock className="h-3.5 w-3.5 animate-pulse" />
                        <span>Indexing...</span>
                      </span>
                    )}

                    {isFailed && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">
                        <AlertCircle className="h-3.5 w-3.5" />
                        <span>Failed</span>
                      </span>
                    )}

                    {/* Refresh status button for non-ready items */}
                    {isProcessing && (
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={refreshingId === item.id}
                        onClick={() => handleRefreshStatus(item)}
                        title="Check Search-Sphere processing status"
                        className="h-8 px-2 text-xs text-muted-foreground hover:text-foreground"
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${refreshingId === item.id ? "animate-spin" : ""}`} />
                        <span className="sr-only">Refresh status</span>
                      </Button>
                    )}

                    {/* Delete button */}
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={deletingId === item.id}
                      onClick={() => handleDelete(item)}
                      title="Delete material"
                      className="h-8 px-2 text-xs text-muted-foreground hover:text-red-400"
                    >
                      {deletingId === item.id ? (
                        <Spinner className="h-3.5 w-3.5" />
                      ) : (
                        <Trash2 className="h-3.5 w-3.5" />
                      )}
                      <span className="sr-only">Delete</span>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Upload Modal Dialog */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-foreground flex items-center gap-2">
                <Upload className="h-5 w-5 text-indigo-500" />
                Upload Course Material
              </h3>
              <button
                onClick={() => !uploading && setIsUploadOpen(false)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="text-xs text-muted-foreground">
              Uploaded PDFs will be indexed in Search-Sphere to power AI question answering with citations.
            </p>

            {uploadError && (
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-red-300 text-xs">
                {uploadError}
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="space-y-4 pt-1">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Document Title *</label>
                <Input
                  type="text"
                  placeholder="e.g. Physics Grade 10 - Unit 2"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={uploading}
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Subject *</label>
                  <select
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    disabled={uploading}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    {SUBJECTS.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Document Type *</label>
                  <select
                    value={docType}
                    onChange={(e) => setDocType(e.target.value as CourseMaterialDocumentType)}
                    disabled={uploading}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    {DOC_TYPES.map((d) => (
                      <option key={d.value} value={d.value}>
                        {d.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {classes && classes.length > 0 && (
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">Class Scope (Optional)</label>
                  <select
                    value={classId}
                    onChange={(e) => setClassId(e.target.value)}
                    disabled={uploading}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="">All School Students</option>
                    {classes.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} {c.section ? `(Sec ${c.section})` : ""}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Description (Optional)</label>
                <Input
                  type="text"
                  placeholder="Brief description or chapter notes"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={uploading}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">PDF Document * (Max 50MB)</label>
                <Input
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  disabled={uploading}
                  required
                  className="cursor-pointer text-xs"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsUploadOpen(false)}
                  disabled={uploading}
                  className="text-muted-foreground"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={uploading || !file || !title.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium"
                >
                  {uploading ? (
                    <span className="flex items-center gap-2">
                      <Spinner className="h-3.5 w-3.5" />
                      <span>Uploading & Indexing...</span>
                    </span>
                  ) : (
                    "Upload & Index"
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
