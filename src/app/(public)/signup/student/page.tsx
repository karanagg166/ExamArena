"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import { Student} from "@/types/student";
type School = { id: string; name: string; city: string };
type SchoolClass = { id: string; name: string };

const INPUT_CLS = "w-full bg-zinc-900 border border-zinc-800 text-white rounded-xl py-2.5 px-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all";

export default function SignupStudentPage() {
    const router = useRouter();
    const [schools, setSchools] = useState<School[]>([]);
    const [classes, setClasses] = useState<SchoolClass[]>([]);
    const [form, setForm] = useState({
        rollNo: "",
        dob: "",
        parentName: "",
        parentEmail: "",
        dateOfAdmission: new Date().toISOString().split("T")[0],
        schoolId: "",
        classId: "",
    });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        api.get("/api/v1/schools/").then((r) => setSchools(r.data)).catch(() => {});
    }, []);

    useEffect(() => {
        if (!form.schoolId) { setClasses([]); return; }
        setForm((p) => ({ ...p, classId: "" }));
        api.get(`/api/v1/schools/${form.schoolId}/classes`)
            .then((r) => setClasses(r.data))
            .catch(() => setClasses([]));
    }, [form.schoolId]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setForm((p) => ({ ...p, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!form.classId) { setError("Please select a class."); return; }
        setSaving(true);
        setError("");
        try {
            await api.post("/api/v1/students/", {
                rollNo: form.rollNo,
                dob: new Date(form.dob).toISOString(),
                parentName: form.parentName,
                parentEmail: form.parentEmail,
                dateOfAdmission: new Date(form.dateOfAdmission).toISOString(),
                classId: form.classId,
            });
            router.push("/dashboard");
        } catch (err: unknown) {
            if (axios.isAxiosError(err)) {
                const detail = err.response?.data?.detail;
                setError(typeof detail === "string" ? detail : "Failed to create profile.");
            }
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-black px-4 text-white py-12">
            <div className="w-full max-w-xl bg-zinc-950 border border-zinc-800 p-8 rounded-3xl shadow-2xl">
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-widest">Step 2 of 2</span>
                <h1 className="text-2xl font-bold mt-1 mb-1">Complete your Student profile</h1>
                <p className="text-zinc-400 text-sm mb-6">Select your school and class to get started.</p>

                {error && (
                    <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm p-3 rounded-lg mb-4">{error}</div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="text-sm font-medium text-zinc-300 block mb-1.5">Select School</label>
                        <select name="schoolId" value={form.schoolId} onChange={handleChange} required className={INPUT_CLS + " appearance-none"}>
                            <option value="">— Choose your school —</option>
                            {schools.map((s) => (
                                <option key={s.id} value={s.id}>{s.name}{s.city ? ` — ${s.city}` : ""}</option>
                            ))}
                        </select>
                    </div>

                    {form.schoolId && (
                        <div>
                            <label className="text-sm font-medium text-zinc-300 block mb-1.5">Select Class</label>
                            <select name="classId" value={form.classId} onChange={handleChange} required className={INPUT_CLS + " appearance-none"}>
                                <option value="">— Choose your class —</option>
                                {classes.length === 0
                                    ? <option disabled>No classes available for this school yet</option>
                                    : classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)
                                }
                            </select>
                        </div>
                    )}

                    <div>
                        <label className="text-sm font-medium text-zinc-300 block mb-1.5">Roll Number</label>
                        <input name="rollNo" value={form.rollNo} onChange={handleChange} required className={INPUT_CLS} />
                    </div>

                    <div>
                        <label className="text-sm font-medium text-zinc-300 block mb-1.5">Date of Birth</label>
                        <input type="date" name="dob" value={form.dob} onChange={handleChange} required className={INPUT_CLS} />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm font-medium text-zinc-300 block mb-1.5">Parent Name</label>
                            <input name="parentName" value={form.parentName} onChange={handleChange} required className={INPUT_CLS} />
                        </div>
                        <div>
                            <label className="text-sm font-medium text-zinc-300 block mb-1.5">Parent Email</label>
                            <input type="email" name="parentEmail" value={form.parentEmail} onChange={handleChange} required className={INPUT_CLS} />
                        </div>
                    </div>

                    <button type="submit" disabled={saving}
                        className="w-full bg-indigo-600 text-white py-3 rounded-xl font-semibold hover:bg-indigo-500 transition-all disabled:opacity-50 mt-2 shadow-lg shadow-indigo-600/20">
                        {saving ? "Setting up…" : "Complete Setup →"}
                    </button>
                </form>
            </div>
        </div>
    );
}
