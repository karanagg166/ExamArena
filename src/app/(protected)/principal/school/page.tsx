// src/app/(protected)/principal/school/page.tsx
"use client"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"        // ✅ added
import { useSchoolStore, useSchoolClassStore } from "@/stores"
import { NewClass } from "@/components/school-class/NewClass"

export default function PrincipalSchoolPage() {
    const router = useRouter()                        // ✅ added
    const [showModal, setShowModal] = useState(false)
    const { school, loading, error, fetchSchool } = useSchoolStore()
    const { classes, fetchClasses } = useSchoolClassStore()

    useEffect(() => { fetchSchool() }, [])
    useEffect(() => { if (school?.id) fetchClasses(school.id) }, [school?.id])

    if (loading) return <p>Loading...</p>
    if (error) return <p style={{ color: "red" }}>{error}</p>
    if (!school) return null

    return (
        <div>
            <h1>{school.name}</h1>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
                <h2>Classes ({classes.length})</h2>
                <button onClick={() => setShowModal(true)}>+ Add Class</button>
            </div>

            <button onClick={() => router.push("/principal/school/school-class")}>
                View All Classes →
            </button>

            {showModal && <NewClass onClose={() => setShowModal(false)} />}
        </div>
    )
}