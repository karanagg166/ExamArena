// src/app/(protected)/principal/school/page.tsx
"use client"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"        // ✅ added
import { useSchoolStore, useSchoolClassStore } from "@/stores"
import { NewClass } from "@/components/school-class/NewClass"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Spinner } from "@/components/ui/loading"

export default function PrincipalSchoolPage() {
    const router = useRouter()                        // ✅ added
    const [showModal, setShowModal] = useState(false)
    const { school, loading, error, fetchSchool } = useSchoolStore()
    const { classes, fetchClasses } = useSchoolClassStore()

    useEffect(() => {
        fetchSchool();
        console.log("Fetching school data...");


    }, [])
    useEffect(() => { if (school?.id) fetchClasses(school.id) }, [school?.id])

    if (loading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <Spinner className="h-8 w-8 border-4" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="page-shell text-white">
                <p className="text-sm text-red-300">{error}</p>
            </div>
        )
    }

    if (!school) return null

    return (
        <div className="page-shell text-white">
            <Card className="mb-6">
                <CardHeader>
                    <CardTitle>{school.name}</CardTitle>
                    <CardDescription>Manage classes for your school.</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-wrap items-center justify-between gap-3">
                    <h2 className="text-lg font-semibold">Classes ({classes.length})</h2>
                    <div className="flex flex-wrap gap-2">
                        <Button onClick={() => setShowModal(true)}>Add Class</Button>
                        <Button variant="secondary" onClick={() => router.push("/principal/school/school-class")}>View All Classes</Button>
                    </div>
                </CardContent>
            </Card>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {classes.map((schoolClass) => (
                    <Card key={schoolClass.id}>
                        <CardContent className="pt-5">
                            <p className="text-sm font-medium text-zinc-200">{schoolClass.name}</p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {classes.length === 0 && <p className="text-sm text-zinc-400">No classes found. Create one to get started.</p>}

            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
                    <NewClass onClose={() => setShowModal(false)} />
                </div>
            )}
        </div>
    )
}