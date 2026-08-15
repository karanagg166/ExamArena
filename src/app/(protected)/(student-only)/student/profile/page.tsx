"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAxiosError } from "axios";
import {
  User,
  BookOpen,
  Mail,
  Edit2,
  Save,
  X,
  KeyRound,
  Clock3,
  CircleCheck,
  CircleX,
} from "lucide-react";
import { api } from "@/lib/axios";
import { toast } from "sonner";
import { Spinner } from "@/components/ui/loading";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useJoinRequestStore } from "@/stores";
import {
  blockNonAlpha,
  blockNonPhone,
  sanitizeAlpha,
  sanitizePhoneNo,
  validateEmailField,
  validatePhoneField,
  validateNameField,
} from "@/lib/utils";

export default function StudentDashboard() {
  const [loading, setLoading] = useState(true);
  const [hasStudentProfile, setHasStudentProfile] = useState<boolean | null>(null);
  const [joinCode, setJoinCode] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [touched, setTouched] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phoneNo: "",
    city: "",
    state: "",
    country: "",
    pincode: "",
    rollNo: "",
    dob: "",
    class: "",
    parentName: "",
    parentEmail: "",
    fatherName: "",
    fatherEmail: "",
    fatherPhoneNo: "",
    motherName: "",
    motherEmail: "",
    motherPhoneNo: "",
    guardianName: "",
    guardianRelation: "",
    guardianEmail: "",
    guardianPhoneNo: "",
  });
  const router = useRouter();
  const {
    myRequests,
    loading: joinRequestLoading,
    error: joinRequestError,
    fetchMyRequests,
    joinByCode,
  } = useJoinRequestStore();

  const getFieldErrors = () => {
    return {
      name: validateNameField(formData.name, "Full Name", false),
      email: validateEmailField(formData.email, false),
      phoneNo: validatePhoneField(formData.phoneNo, false),
      fatherName: validateNameField(formData.fatherName, "Father's Name", false),
      fatherEmail: validateEmailField(formData.fatherEmail, false),
      fatherPhoneNo: validatePhoneField(formData.fatherPhoneNo, false),
      motherName: validateNameField(formData.motherName, "Mother's Name", false),
      motherEmail: validateEmailField(formData.motherEmail, false),
      motherPhoneNo: validatePhoneField(formData.motherPhoneNo, false),
      guardianName: validateNameField(formData.guardianName, "Guardian Name", false),
      guardianEmail: validateEmailField(formData.guardianEmail, false),
      guardianPhoneNo: validatePhoneField(formData.guardianPhoneNo, false),
    };
  };

  const fieldErrors = getFieldErrors();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get("/api/v1/students/me", {
          withCredentials: true,
        });
        const data = response.data;
        setHasStudentProfile(true);
        const userObj = data?.user || {};

        let displayClass = data?.className || "";
        if (!displayClass && data?.classId) {
          try {
            const classRes = await api.get(`/api/v1/classes/${data.classId}`);
            displayClass = classRes.data?.name || "Assigned Class";
          } catch {
            displayClass = "Assigned Class";
          }
        }

        setFormData({
          name: userObj.name || "",
          email: userObj.email || "",
          phoneNo: userObj.phoneNo || "",
          city: userObj.city || "",
          state: userObj.state || "",
          country: userObj.country || "",
          pincode: userObj.pincode || "",
          rollNo: data?.rollNo || "",
          dob: data?.dob ? data.dob.split("T")[0] : (data?.dateOfAdmission ? data.dateOfAdmission.split("T")[0] : ""),
          class: displayClass,
          parentName: data?.parentName || "",
          parentEmail: data?.parentEmail || "",
          fatherName: data?.fatherName || "",
          fatherEmail: data?.fatherEmail || "",
          fatherPhoneNo: data?.fatherPhoneNo || "",
          motherName: data?.motherName || "",
          motherEmail: data?.motherEmail || "",
          motherPhoneNo: data?.motherPhoneNo || "",
          guardianName: data?.guardianName || "",
          guardianRelation: data?.guardianRelation || "",
          guardianEmail: data?.guardianEmail || "",
          guardianPhoneNo: data?.guardianPhoneNo || "",
        });
      } catch (error: unknown) {
        console.error("Error fetching student data:", error);
        if (isAxiosError(error)) {
          const status = error.response?.status;
          if (status === 404) {
            await fetchMyRequests();
            setHasStudentProfile(false);
            return;
          }
          if (status === 403) {
            toast.error("Access restricted. Redirecting to dashboard.");
            router.push("/dashboard");
            return;
          }
          if (status === 401) {
            toast.error("Session expired. Please log in again.");
            router.push("/login");
            return;
          }
        }
        toast.error("Failed to load student profile. Please refresh.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [fetchMyRequests, router]);

  const handleJoinClass = async (event: React.FormEvent) => {
    event.preventDefault();
    const result = await joinByCode(joinCode.trim().toUpperCase());
    if (!result.success) {
      toast.error(result.error ?? "Unable to submit the join request.");
      return;
    }
    setJoinCode("");
    toast.success("Join request sent to your teacher.");
  };

  const handleSave = async () => {
    setTouched(true);

    const currentErrors = getFieldErrors();
    if (Object.values(currentErrors).some(Boolean)) {
      toast.error("Please fix invalid fields before saving.");
      return;
    }

    try {
      const computedParentName =
        formData.fatherName ||
        formData.motherName ||
        formData.guardianName ||
        formData.parentName;

      const computedParentEmail =
        formData.fatherEmail ||
        formData.motherEmail ||
        formData.guardianEmail ||
        formData.parentEmail;

      // Update student data (includes user data)
      await api.put(
        "/api/v1/students/me",
        {
          user: {
            name: formData.name,
            email: formData.email,
            phoneNo: formData.phoneNo,
            city: formData.city,
            state: formData.state,
            country: formData.country,
            pincode: formData.pincode,
          },
          dob: formData.dob,
          parentName: computedParentName,
          parentEmail: computedParentEmail,
          fatherName: formData.fatherName || undefined,
          fatherEmail: formData.fatherEmail || undefined,
          fatherPhoneNo: formData.fatherPhoneNo || undefined,
          motherName: formData.motherName || undefined,
          motherEmail: formData.motherEmail || undefined,
          motherPhoneNo: formData.motherPhoneNo || undefined,
          guardianName: formData.guardianName || undefined,
          guardianRelation: formData.guardianRelation || undefined,
          guardianEmail: formData.guardianEmail || undefined,
          guardianPhoneNo: formData.guardianPhoneNo || undefined,
        },
        { withCredentials: true },
      );

      setIsEditing(false);
      toast.success("Profile updated successfully!");
    } catch (error: unknown) {
      console.error("Error saving data:", error);
      toast.error("Failed to update profile. Please try again.");
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-8 w-8 border-4" />
      </div>
    );
  }

  if (!hasStudentProfile) {
    const latestRequest = myRequests[0];
    const requestIcon =
      latestRequest?.status === "APPROVED" ? (
        <CircleCheck className="h-6 w-6 text-emerald-400" />
      ) : latestRequest?.status === "REJECTED" ? (
        <CircleX className="h-6 w-6 text-red-400" />
      ) : (
        <Clock3 className="h-6 w-6 text-amber-300" />
      );

    return (
      <div className="page-shell text-white">
        <div className="mx-auto max-w-2xl space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Class enrollment</h1>
            <p className="mt-1 text-zinc-400">Join a class with the code shared by your teacher.</p>
          </div>

          {latestRequest && latestRequest.status !== "REJECTED" ? (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-xl">
              <div className="flex items-start gap-4">
                <div className="rounded-xl bg-zinc-900 p-3">{requestIcon}</div>
                <div>
                  <p className="text-sm font-medium uppercase tracking-wider text-zinc-500">{latestRequest.status}</p>
                  <h2 className="mt-1 text-xl font-semibold">{latestRequest.className}</h2>
                  <p className="mt-2 text-sm text-zinc-400">
                    {latestRequest.status === "PENDING"
                      ? "Your teacher will review your request. You will be enrolled automatically after approval."
                      : "Your enrollment was approved. Refresh this page in a moment to see your assigned profile."}
                  </p>
                </div>
              </div>
              {latestRequest.status === "APPROVED" && (
                <Button className="mt-5" variant="outline" onClick={() => window.location.reload()}>
                  Refresh enrollment
                </Button>
              )}
            </div>
          ) : (
            <form onSubmit={handleJoinClass} className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-xl">
              {latestRequest?.status === "REJECTED" && (
                <div className="mb-5 flex gap-3 rounded-xl border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-200">
                  {requestIcon}
                  Your request for {latestRequest.className} was rejected. Check the code with your teacher and submit a new request if appropriate.
                </div>
              )}
              <label htmlFor="profile-join-code" className="mb-2 flex items-center gap-2 text-sm font-medium text-zinc-200">
                <KeyRound className="h-4 w-4 text-indigo-300" /> Class join code
              </label>
              <div className="flex flex-col gap-3 sm:flex-row">
                <Input
                  id="profile-join-code"
                  value={joinCode}
                  onChange={(event) => setJoinCode(event.target.value.toUpperCase())}
                  placeholder="e.g. 8F2KQ9XA"
                  autoCapitalize="characters"
                  className="font-mono uppercase tracking-[0.14em]"
                  required
                />
                <Button type="submit" disabled={joinRequestLoading || !joinCode.trim()}>
                  {joinRequestLoading ? "Sending…" : "Request to join"}
                </Button>
              </div>
              {joinRequestError && <p className="mt-3 text-sm text-red-300">{joinRequestError}</p>}
            </form>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="page-shell text-white">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Student Dashboard</h1>
            <p className="text-zinc-400 mt-1">Welcome back, {formData.name}!</p>
          </div>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
          >
            {isEditing ? (
              <X className="w-4 h-4" />
            ) : (
              <Edit2 className="w-4 h-4" />
            )}
            {isEditing ? "Cancel" : "Edit Profile"}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Personal Information */}
          <div className="lg:col-span-2 bg-zinc-950 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-indigo-400" />
              Personal Information
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-zinc-400">Full Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onKeyDown={blockNonAlpha}
                  onChange={(e) =>
                    setFormData({ ...formData, name: sanitizeAlpha(e.target.value) })
                  }
                  disabled={!isEditing}
                  className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-2 disabled:opacity-50 ${isEditing && (touched || formData.name) && fieldErrors.name ? "border-red-500" : "border-zinc-800"}`}
                />
                {isEditing && (touched || formData.name) && fieldErrors.name && (
                  <p className="text-xs text-red-400 mt-1">{fieldErrors.name}</p>
                )}
              </div>
              <div>
                <label className="text-sm text-zinc-400">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  disabled={!isEditing}
                  className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-2 disabled:opacity-50 ${isEditing && (touched || formData.email) && fieldErrors.email ? "border-red-500" : "border-zinc-800"}`}
                />
                {isEditing && (touched || formData.email) && fieldErrors.email && (
                  <p className="text-xs text-red-400 mt-1">{fieldErrors.email}</p>
                )}
              </div>
              <div>
                <label className="text-sm text-zinc-400">Phone Number</label>
                <input
                  type="tel"
                  value={formData.phoneNo}
                  onKeyDown={blockNonPhone}
                  onChange={(e) =>
                    setFormData({ ...formData, phoneNo: sanitizePhoneNo(e.target.value) })
                  }
                  disabled={!isEditing}
                  className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-2 disabled:opacity-50 ${isEditing && (touched || formData.phoneNo) && fieldErrors.phoneNo ? "border-red-500" : "border-zinc-800"}`}
                />
                {isEditing && (touched || formData.phoneNo) && fieldErrors.phoneNo && (
                  <p className="text-xs text-red-400 mt-1">{fieldErrors.phoneNo}</p>
                )}
              </div>
              <div>
                <label className="text-sm text-zinc-400">City</label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) =>
                    setFormData({ ...formData, city: e.target.value })
                  }
                  disabled={!isEditing}
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400">State</label>
                <input
                  type="text"
                  value={formData.state}
                  onChange={(e) =>
                    setFormData({ ...formData, state: e.target.value })
                  }
                  disabled={!isEditing}
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400">Country</label>
                <input
                  type="text"
                  value={formData.country}
                  onChange={(e) =>
                    setFormData({ ...formData, country: e.target.value })
                  }
                  disabled={!isEditing}
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
              </div>
            </div>
          </div>

          {/* Student Specific Info */}
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-400" />
              Student Details
            </h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-zinc-400">Roll Number (Read-only)</label>
                <input
                  type="text"
                  value={formData.rollNo}
                  disabled
                  readOnly
                  className="w-full mt-1 bg-zinc-900/60 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-400 cursor-not-allowed opacity-75"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400">Date of Birth</label>
                <input
                  type="date"
                  value={formData.dob}
                  onChange={(e) =>
                    setFormData({ ...formData, dob: e.target.value })
                  }
                  disabled={!isEditing}
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400">Class (Read-only)</label>
                <input
                  type="text"
                  value={formData.class}
                  disabled
                  readOnly
                  className="w-full mt-1 bg-zinc-900/60 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-400 cursor-not-allowed opacity-75"
                />
              </div>
            </div>
          </div>

          {/* Parent & Guardian Information */}
          <div className="lg:col-span-3 bg-zinc-950 border border-zinc-800 rounded-xl p-6 space-y-6">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Mail className="w-5 h-5 text-indigo-400" />
              Parent & Guardian Information
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Father Details */}
              <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800 space-y-3">
                <h3 className="text-sm font-semibold text-indigo-400 uppercase tracking-wider">
                  👨 Father&apos;s Details
                </h3>
                <div>
                  <label className="text-xs text-zinc-400">Father&apos;s Name</label>
                  <input
                    type="text"
                    value={formData.fatherName}
                    onKeyDown={blockNonAlpha}
                    onChange={(e) =>
                      setFormData({ ...formData, fatherName: sanitizeAlpha(e.target.value) })
                    }
                    disabled={!isEditing}
                    placeholder="e.g. John Doe"
                    className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-1.5 text-sm disabled:opacity-50 ${isEditing && fieldErrors.fatherName ? "border-red-500" : "border-zinc-800"}`}
                  />
                  {isEditing && fieldErrors.fatherName && (
                    <p className="text-xs text-red-400 mt-1">{fieldErrors.fatherName}</p>
                  )}
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Father&apos;s Email</label>
                  <input
                    type="email"
                    value={formData.fatherEmail}
                    onChange={(e) =>
                      setFormData({ ...formData, fatherEmail: e.target.value })
                    }
                    disabled={!isEditing}
                    placeholder="father@example.com"
                    className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-1.5 text-sm disabled:opacity-50 ${isEditing && fieldErrors.fatherEmail ? "border-red-500" : "border-zinc-800"}`}
                  />
                  {isEditing && fieldErrors.fatherEmail && (
                    <p className="text-xs text-red-400 mt-1">{fieldErrors.fatherEmail}</p>
                  )}
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Father&apos;s Phone Number</label>
                  <input
                    type="tel"
                    value={formData.fatherPhoneNo}
                    onKeyDown={blockNonPhone}
                    onChange={(e) =>
                      setFormData({ ...formData, fatherPhoneNo: sanitizePhoneNo(e.target.value) })
                    }
                    disabled={!isEditing}
                    placeholder="+1 234 567 890"
                    className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-1.5 text-sm disabled:opacity-50 ${isEditing && fieldErrors.fatherPhoneNo ? "border-red-500" : "border-zinc-800"}`}
                  />
                  {isEditing && fieldErrors.fatherPhoneNo && (
                    <p className="text-xs text-red-400 mt-1">{fieldErrors.fatherPhoneNo}</p>
                  )}
                </div>
              </div>

              {/* Mother Details */}
              <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800 space-y-3">
                <h3 className="text-sm font-semibold text-indigo-400 uppercase tracking-wider">
                  👩 Mother&apos;s Details
                </h3>
                <div>
                  <label className="text-xs text-zinc-400">Mother&apos;s Name</label>
                  <input
                    type="text"
                    value={formData.motherName}
                    onKeyDown={blockNonAlpha}
                    onChange={(e) =>
                      setFormData({ ...formData, motherName: sanitizeAlpha(e.target.value) })
                    }
                    disabled={!isEditing}
                    placeholder="e.g. Jane Doe"
                    className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-1.5 text-sm disabled:opacity-50 ${isEditing && fieldErrors.motherName ? "border-red-500" : "border-zinc-800"}`}
                  />
                  {isEditing && fieldErrors.motherName && (
                    <p className="text-xs text-red-400 mt-1">{fieldErrors.motherName}</p>
                  )}
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Mother&apos;s Email</label>
                  <input
                    type="email"
                    value={formData.motherEmail}
                    onChange={(e) =>
                      setFormData({ ...formData, motherEmail: e.target.value })
                    }
                    disabled={!isEditing}
                    placeholder="mother@example.com"
                    className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-1.5 text-sm disabled:opacity-50 ${isEditing && fieldErrors.motherEmail ? "border-red-500" : "border-zinc-800"}`}
                  />
                  {isEditing && fieldErrors.motherEmail && (
                    <p className="text-xs text-red-400 mt-1">{fieldErrors.motherEmail}</p>
                  )}
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Mother&apos;s Phone Number</label>
                  <input
                    type="tel"
                    value={formData.motherPhoneNo}
                    onKeyDown={blockNonPhone}
                    onChange={(e) =>
                      setFormData({ ...formData, motherPhoneNo: sanitizePhoneNo(e.target.value) })
                    }
                    disabled={!isEditing}
                    placeholder="+1 234 567 890"
                    className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-1.5 text-sm disabled:opacity-50 ${isEditing && fieldErrors.motherPhoneNo ? "border-red-500" : "border-zinc-800"}`}
                  />
                  {isEditing && fieldErrors.motherPhoneNo && (
                    <p className="text-xs text-red-400 mt-1">{fieldErrors.motherPhoneNo}</p>
                  )}
                </div>
              </div>

              {/* Guardian Details */}
              <div className="p-4 rounded-xl bg-zinc-900/50 border border-zinc-800 space-y-3">
                <h3 className="text-sm font-semibold text-indigo-400 uppercase tracking-wider">
                  🛡️ Guardian Details (Optional)
                </h3>
                <div>
                  <label className="text-xs text-zinc-400">Guardian Name</label>
                  <input
                    type="text"
                    value={formData.guardianName}
                    onKeyDown={blockNonAlpha}
                    onChange={(e) =>
                      setFormData({ ...formData, guardianName: sanitizeAlpha(e.target.value) })
                    }
                    disabled={!isEditing}
                    placeholder="e.g. Robert Smith"
                    className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-1.5 text-sm disabled:opacity-50 ${isEditing && fieldErrors.guardianName ? "border-red-500" : "border-zinc-800"}`}
                  />
                  {isEditing && fieldErrors.guardianName && (
                    <p className="text-xs text-red-400 mt-1">{fieldErrors.guardianName}</p>
                  )}
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Relation to Student</label>
                  <input
                    type="text"
                    value={formData.guardianRelation}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        guardianRelation: e.target.value,
                      })
                    }
                    disabled={!isEditing}
                    placeholder="e.g. Uncle / Grandparent"
                    className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-sm disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Guardian Email</label>
                  <input
                    type="email"
                    value={formData.guardianEmail}
                    onChange={(e) =>
                      setFormData({ ...formData, guardianEmail: e.target.value })
                    }
                    disabled={!isEditing}
                    placeholder="guardian@example.com"
                    className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-1.5 text-sm disabled:opacity-50 ${isEditing && fieldErrors.guardianEmail ? "border-red-500" : "border-zinc-800"}`}
                  />
                  {isEditing && fieldErrors.guardianEmail && (
                    <p className="text-xs text-red-400 mt-1">{fieldErrors.guardianEmail}</p>
                  )}
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Guardian Phone Number</label>
                  <input
                    type="tel"
                    value={formData.guardianPhoneNo}
                    onKeyDown={blockNonPhone}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        guardianPhoneNo: sanitizePhoneNo(e.target.value),
                      })
                    }
                    disabled={!isEditing}
                    placeholder="+1 234 567 890"
                    className={`w-full mt-1 bg-zinc-900 border rounded-lg px-3 py-1.5 text-sm disabled:opacity-50 ${isEditing && fieldErrors.guardianPhoneNo ? "border-red-500" : "border-zinc-800"}`}
                  />
                  {isEditing && fieldErrors.guardianPhoneNo && (
                    <p className="text-xs text-red-400 mt-1">{fieldErrors.guardianPhoneNo}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {isEditing && (
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
            >
              <Save className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
