"use client"
import React, { useEffect, useState } from 'react'
import { useRouter } from "next/navigation"
import { api } from "@/lib/axios"
import { SchoolClass } from "@/types/school-class"

export const Page = () => {
    const router = useRouter()
    const [classes, setClasses] = useState<SchoolClass[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState("")

    useEffect(() => {
        const fetchClasses = async () => {
            try {
                const schoolResponse = await api.get("/api/v1/schools/me")
                const response = await api.get(
                    `/api/v1/classes/school/${schoolResponse.data.id}`
                )
                setClasses(response.data)
            } catch (error) {
                console.error("Failed to fetch classes:", error)
                setError("Failed to load classes")
            } finally {
                setLoading(false)
            }
        }

        fetchClasses()
    }, [])

    if (loading) return <p>Loading classes...</p>
    if (error) return <p style={{ color: "red" }}>{error}</p>

    return (
        <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h1>Classes</h1>
                <button onClick={() => router.push("/principal/school/school-class")}>
                    + New Class
                </button>
            </div>

            {classes.length === 0 ? (
                <p>No classes found. Create one to get started.</p>
            ) : (
                <ul>
                    {classes.map((schoolClass) => (
                        <li key={schoolClass.id}>
                            {schoolClass.name}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}
