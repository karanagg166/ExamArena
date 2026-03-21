"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import { SignUpForm } from "@/types/user";

const SignUpPage = () => {
    const [form, setForm] = useState<SignUpForm>({
        name: "",
        email: "",
        password: "",
        confirmPassword: "",
        phoneNo: "",
        role: "student",
        pincode: "",
        city: "",
        state: "",
        country: "",
    });

    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);

    const router = useRouter();

    // Handle input change
    const handleChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
    ) => {
        const { name, value } = e.target;

        setForm((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    // Submit handler
    const onSubmit = async () => {
        if (loading) return;

        const { name, email, password, confirmPassword } = form;

        // Validation
        if (!name || !email || !password) {
            setError("Please fill all required fields");
            return;
        }

        if (password.length < 6) {
            setError("Password must be at least 6 characters");
            return;
        }

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        setLoading(true);
        setError("");

        try {
            // Remove confirmPassword before sending
            const { confirmPassword, ...payload } = form;

            await api.post("/auth/signup", payload);

            setSuccess(true);


            router.push("/login");

        } catch (err: unknown) {
            if (axios.isAxiosError(err)) {
                setError(
                    err.response?.data?.detail ||
                    "Something went wrong during signup."
                );
            } else {
                setError("Unexpected error occurred");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-gray-100 px-4">
            <div className="w-full max-w-2xl bg-white p-8 rounded-2xl shadow-xl">
                <h1 className="text-3xl font-bold text-center mb-2">
                    Create your account
                </h1>
                <p className="text-gray-500 text-center mb-6 text-sm">
                    Start your journey in seconds 🚀
                </p>

                {error && (
                    <div className="bg-red-100 text-red-600 text-sm p-2 rounded mb-3 text-center">
                        {error}
                    </div>
                )}

                {success && (
                    <div className="bg-green-100 text-green-600 text-sm p-2 rounded mb-3 text-center">
                        Signup successful!
                    </div>
                )}

                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        onSubmit();
                    }}
                    className="space-y-4"
                >
                    {/* Name */}
                    <div>
                        <label className="label">Full Name</label>
                        <input
                            name="name"
                            value={form.name}
                            onChange={handleChange}
                            className="input"
                        />
                    </div>

                    {/* Email */}
                    <div>
                        <label className="label">Email</label>
                        <input
                            name="email"
                            type="email"
                            value={form.email}
                            onChange={handleChange}
                            className="input"
                        />
                    </div>

                    {/* Password Row */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="label">Password</label>
                            <input
                                name="password"
                                type="password"
                                value={form.password}
                                onChange={handleChange}
                                className="input"
                            />
                        </div>

                        <div>
                            <label className="label">Confirm</label>
                            <input
                                name="confirmPassword"
                                type="password"
                                value={form.confirmPassword}
                                onChange={handleChange}
                                className="input"
                            />
                        </div>
                    </div>

                    {/* Phone + Role */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="label">Phone</label>
                            <input
                                name="phoneNo"
                                value={form.phoneNo}
                                onChange={handleChange}
                                className="input"
                            />
                        </div>

                        <div>
                            <label className="label">Role</label>
                            <select
                                name="role"
                                value={form.role}
                                onChange={handleChange}
                                className="input"
                            >
                                <option value="student">Student</option>
                                <option value="teacher">Teacher</option>
                            </select>
                        </div>
                    </div>

                    {/* Location */}
                    <div className="grid grid-cols-2 gap-3">
                        <input
                            name="pincode"
                            placeholder="Pincode"
                            value={form.pincode}
                            onChange={handleChange}
                            className="input"
                        />
                        <input
                            name="city"
                            placeholder="City"
                            value={form.city}
                            onChange={handleChange}
                            className="input"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <input
                            name="state"
                            placeholder="State"
                            value={form.state}
                            onChange={handleChange}
                            className="input"
                        />
                        <input
                            name="country"
                            placeholder="Country"
                            value={form.country}
                            onChange={handleChange}
                            className="input"
                        />
                    </div>

                    {/* Button */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 transition-all active:scale-[0.98] disabled:opacity-50"
                    >
                        {loading ? "Creating account..." : "Create Account"}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default SignUpPage;