// src/components/school-class/NewClass.tsx — accept onClose prop
"use client"
import React, { useState } from "react"
import { useSchoolClassStore } from "@/stores/index"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { FormMessage } from "@/components/ui/form-message"
import { Input } from "@/components/ui/input"
// import {api}  from "@/lib/axios"
interface Props {
  onClose?: () => void
}

export const NewClass = ({ onClose }: Props) => {
  const [name, setName] = useState("")

  const { createClass, loading, error } = useSchoolClassStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // const data=await api.post("/api/v1/classes/", { name })
    // console.log("Create class response:", data)
    console.log("Submitting new class with name:", name, "and schoolId:");
    if (!name.trim()) return

    const success = await createClass({ name: name.trim() });
    console.log("Create class success:", success);
    // console.log("Create class success:",);
    if (success) {
      toast.success("Class created successfully")
      setName("")
      onClose?.()
    } else {
      toast.error("Failed to create class")
    }
  }

  return (
    <Card className="w-full max-w-xl">
      <CardHeader>
        <CardTitle>Create New Class</CardTitle>
        <CardDescription>Add a class under your current school.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Class Name"
            disabled={loading}
          />
          <FormMessage message={error} type="error" />
          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={loading || !name.trim()}>
              {loading ? "Creating..." : "Create Class"}
            </Button>
            {onClose && (
              <Button type="button" variant="secondary" onClick={onClose}>
                Cancel
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
