"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { User, Shield, Edit2, Save, X } from "lucide-react";
import { api } from "@/lib/axios";
import { toast } from "sonner";
import { Spinner } from "@/components/ui/loading";

export default function AdminDashboard() {
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phoneNo: "",
    city: "",
    state: "",
    country: "",
    pincode: "",
  });
  const router = useRouter();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await api.get("/api/v1/auth/me", {
          withCredentials: true,
        });
        const userData = response.data;
        setFormData({
          name: userData.name || "",
          email: userData.email || "",
          phoneNo: userData.phoneNo || "",
          city: userData.city || "",
          state: userData.state || "",
          country: userData.country || "",
          pincode: userData.pincode || "",
        });
      } catch (error) {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [router]);

  const handleSave = async () => {
    try {
      // Update user data
      await api.put(
        "/api/v1/auth/me",
        {
          name: formData.name,
          email: formData.email,
          phoneNo: formData.phoneNo,
          city: formData.city,
          state: formData.state,
          country: formData.country,
          pincode: formData.pincode,
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
            <h1 className="text-3xl font-bold">Admin Dashboard</h1>
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
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  disabled={!isEditing}
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
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
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
              </div>
              <div>
                <label className="text-sm text-zinc-400">Phone Number</label>
                <input
                  type="text"
                  value={formData.phoneNo}
                  onChange={(e) =>
                    setFormData({ ...formData, phoneNo: e.target.value })
                  }
                  disabled={!isEditing}
                  className="w-full mt-1 bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 disabled:opacity-50"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
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
              </div>
            </div>
          </div>

          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-indigo-400" />
              Admin Privileges
            </h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-zinc-900 rounded-lg">
                <span className="text-sm">Manage Users</span>
                <span className="text-xs text-green-400">Active</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-zinc-900 rounded-lg">
                <span className="text-sm">System Settings</span>
                <span className="text-xs text-green-400">Active</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-zinc-900 rounded-lg">
                <span className="text-sm">View Reports</span>
                <span className="text-xs text-green-400">Active</span>
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
