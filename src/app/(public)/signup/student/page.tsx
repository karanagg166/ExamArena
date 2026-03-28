"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { api } from "@/lib/axios";
import { School } from "@/types/school";
import { useAuthStore } from "@/stores";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FormMessage } from "@/components/ui/form-message";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
type SchoolClass = { id: string; name: string };

export default function SignupStudentPage() {
    const router = useRouter();
    const [schools, setSchools] = useState<School[]>([]);
    const [classes, setClasses] = useState<SchoolClass[]>([]);
    const user = useAuthStore((s) => s.user);
    console.log("Current user in signup page:", user);
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
        api.get("/api/v1/schools/").then((r) => setSchools(r.data)).catch(() => { });
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
        if (!form.classId) {
            const message = "Please select a class.";
            setError(message);
            toast.error(message);
            return;
        }
        setSaving(true);
        setError("");
        try {
            await api.post("/api/v1/students/", {
                rollNo: form.rollNo,
                dob: new Date(form.dob).toISOString(),
                parentName: form.parentName,
                parentEmail: form.parentEmail,
                dateOfAdmission: new Date(form.dateOfAdmission).toISOString(),
                schoolId: form.schoolId,
                classId: form.classId,
            });
            toast.success("Student profile completed");
            router.push("/dashboard");
        } catch (err: unknown) {
            if (axios.isAxiosError(err)) {
                const detail = err.response?.data?.detail;
                const message = typeof detail === "string" ? detail : "Failed to create profile.";
                setError(message);
                toast.error(message);
            }
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="page-shell flex min-h-screen items-center justify-center py-12 text-white">
            <Card className="w-full max-w-xl shadow-2xl shadow-indigo-950/20">
                <CardHeader>
                    <Badge className="w-fit uppercase tracking-widest">Step 2 of 2</Badge>
                    <CardTitle className="text-2xl">Complete your Student profile</CardTitle>
                    <CardDescription>Select your school and class to get started.</CardDescription>
                </CardHeader>

                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <FormMessage message={error} type="error" />

                    <div>
                        <Label className="mb-1.5 block">Select School</Label>
                        <select
                            name="schoolId"
                            value={form.schoolId}
                            onChange={handleChange}
                            required
                            className="flex h-10 w-full appearance-none rounded-xl border border-zinc-700 bg-zinc-900/80 px-3 py-2 text-sm text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                        >
                            <option value="">— Choose your school —</option>
                            {schools.map((s) => (
                                <option key={s.id} value={s.id}>{s.name}{s.city ? ` — ${s.city}` : ""}</option>
                            ))}
                        </select>
                    </div>

                    {form.schoolId && (
                        <div>
                            <Label className="mb-1.5 block">Select Class</Label>
                            <select
                                name="classId"
                                value={form.classId}
                                onChange={handleChange}
                                required
                                className="flex h-10 w-full appearance-none rounded-xl border border-zinc-700 bg-zinc-900/80 px-3 py-2 text-sm text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                            >
                                <option value="">— Choose your class —</option>
                                {classes.length === 0
                                    ? <option disabled>No classes available for this school yet</option>
                                    : classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)
                                }
                            </select>
                        </div>
                    )}

                    <div>
                        <Label className="mb-1.5 block">Roll Number</Label>
                        <Input name="rollNo" value={form.rollNo} onChange={handleChange} required />
                    </div>

                    <div>
                        <Label className="mb-1.5 block">Date of Birth</Label>
                        <Input type="date" name="dob" value={form.dob} onChange={handleChange} required />
                    </div>

                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                        <div>
                            <Label className="mb-1.5 block">Parent Name</Label>
                            <Input name="parentName" value={form.parentName} onChange={handleChange} required />
                        </div>
                        <div>
                            <Label className="mb-1.5 block">Parent Email</Label>
                            <Input type="email" name="parentEmail" value={form.parentEmail} onChange={handleChange} required />
                        </div>
                    </div>

                    <Button type="submit" disabled={saving} className="mt-2 w-full">
                        {saving ? "Setting up…" : "Complete Setup →"}
                    </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
