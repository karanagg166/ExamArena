"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAxiosError } from "axios";
import { User, Award, Edit2, Save, X } from "lucide-react";
import { api } from "@/lib/axios";
import { toast } from "sonner";
import { Spinner } from "@/components/ui/loading";
import { IndiaStateCitySelect } from "@/components/ui/IndiaStateCitySelect";

import {
  blockNonAlpha,
  blockNonPhone,
  blockNonDigits,
  sanitizeAlpha,
  sanitizePhoneNo,
  validateEmailField,
  validatePhoneField,
  validateNameField,
} from "@/lib/utils";

export default function PrincipalDashboard() {
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [touched, setTouched] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phoneNo: "",
    dateOfBirth: "",
    city: "",
    state: "",
    country: "",
    pincode: "",
    qualification: "",
    experience: 0,
  });
  const router = useRouter();

  const getFieldErrors = () => {
    return {
      name: validateNameField(formData.name, "Full Name", false),
      email: validateEmailField(formData.email, false),
      phoneNo: validatePhoneField(formData.phoneNo, false),
    };
  };

  const fieldErrors = getFieldErrors();

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch principal data (includes user data)
        const response = await api.get("/api/v1/principals/me", {
          withCredentials: true,
        });
        const data = response.data;
        const teacher = data?.teacher ?? {};
        const teacherUser = teacher?.user ?? {};

        setFormData({
          name: teacherUser.name || "",
          email: teacherUser.email || "",
          phoneNo: teacherUser.phoneNo || "",
          dateOfBirth: teacherUser.dateOfBirth
            ? teacherUser.dateOfBirth.split("T")[0]
            : "",
          city: teacherUser.city || "",
          state: teacherUser.state || "",
          country: teacherUser.country || "",
          pincode: teacherUser.pincode || "",
          qualification: (teacher.qualifications || []).join(", "),
          experience: data?.experience || 0,
        });
      } catch (error: unknown) {
        console.error("Error fetching principal data:", error);
        if (isAxiosError(error)) {
          if (error.response?.status === 401) {
            router.push("/login");
            return;
          }
          if (error.response?.status === 403) {
            router.push("/dashboard");
            return;
          }
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [router]);

  const handleSave = async () => {
    setTouched(true);

    const currentErrors = getFieldErrors();
    if (Object.values(currentErrors).some(Boolean)) {
      toast.error("Please fix invalid fields before saving.");
      return;
    }

    try {
      await api.put(
        "/api/v1/teachers/me",
        {
          user: {
            name: formData.name,
            email: formData.email,
            phoneNo: formData.phoneNo,
            dateOfBirth: formData.dateOfBirth
              ? new Date(formData.dateOfBirth).toISOString()
              : undefined,
            city: formData.city,
            state: formData.state,
            country: formData.country,
            pincode: formData.pincode,
          },
          qualifications: formData.qualification
            .split(",")
            .map((item: string) => item.trim())
            .filter(Boolean),
        },
        { withCredentials: true },
      );

      await api.put(
        "/api/v1/principals/me",
        {
          experience: formData.experience,
        },
        { withCredentials: true },
      );

      setIsEditing(false);
      toast.success("Profile updated successfully!");
    } catch (error) {
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

  return (
    <div className="page-shell text-white">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Principal Dashboard</h1>
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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-indigo-400" />
              Personal Information
            </h2>
            <div className="space-y-4">
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
                <label className="text-sm text-zinc-400">Date of Birth</label>
                <input
                  type="date"
                  value={formData.dateOfBirth}
                  onChange={(e) =>
                    setFormData({ ...formData, dateOfBirth: e.target.value })
                  }
                  disabled={!isEditing}
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
              </div>
              <IndiaStateCitySelect
                selectedState={formData.state}
                selectedCity={formData.city}
                onStateChange={(state) => setFormData((prev) => ({ ...prev, state }))}
                onCityChange={(city) => setFormData((prev) => ({ ...prev, city }))}
                disabled={!isEditing}
                stateClassName="bg-zinc-900 border-zinc-800 text-white"
                cityClassName="bg-zinc-900 border-zinc-800 text-white"
              />
            </div>
          </div>

          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-indigo-400" />
              Professional Details
            </h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-zinc-400">Qualification</label>
                <input
                  type="text"
                  value={formData.qualification}
                  onChange={(e) =>
                    setFormData({ ...formData, qualification: e.target.value })
                  }
                  disabled={!isEditing}
                  placeholder="e.g., M.Ed, Ph.D"
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400">
                  Experience (years)
                </label>
                <input
                  type="number"
                  min="0"
                  onKeyDown={blockNonDigits}
                  value={formData.experience}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      experience: parseInt(e.target.value) || 0,
                    })
                  }
                  disabled={!isEditing}
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
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
