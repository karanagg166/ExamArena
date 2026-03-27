// src/components/school-class/NewClass.tsx — accept onClose prop
"use client"
import React, { useState } from "react"
import { useSchoolStore, useSchoolClassStore } from "@/stores/index"

interface Props {
  onClose: () => void
}

export const NewClass = ({ onClose }: Props) => {
  const [name, setName] = useState("")
  const { school } = useSchoolStore()
  const { createClass, loading, error } = useSchoolClassStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !school?.id) return

    const success = await createClass({ name: name.trim(), schoolId: school.id })
    if (success) onClose()   // ✅ just close modal, no redirect needed
  }

  return (
    <div>
      <h1>Create New Class</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Class Name"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !name.trim()}>
          {loading ? "Creating..." : "Create Class"}
        </button>
        <button type="button" onClick={onClose}>Cancel</button>
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  )
}
