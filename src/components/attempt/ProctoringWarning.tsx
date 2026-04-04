// src/components/attempt/ProctoringWarning.tsx
"use client"
import { AlertTriangle } from "lucide-react"

interface Props {
    count: number
    max: number
    reason: string
    onDismiss: () => void
}

export const ProctoringWarning = ({ count, max, reason, onDismiss }: Props) => {
    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm">
            <div className="bg-red-950/90 border border-red-500/50 rounded-2xl p-8 max-w-md w-full mx-4 text-center">

                <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />

                <h2 className="text-2xl font-bold text-white mb-2">
                    Warning {count}/{max}
                </h2>

                <p className="text-red-300 mb-2 font-medium">{reason}</p>

                <p className="text-zinc-400 text-sm mb-6">
                    {count >= max
                        ? "Maximum violations reached. Your exam will be auto-submitted."
                        : `${max - count} warning(s) remaining before auto-submission.`
                    }
                </p>

                {count < max && (
                    <button
                        onClick={onDismiss}
                        className="bg-red-600 hover:bg-red-500 text-white px-6 py-3 rounded-xl font-medium w-full transition"
                    >
                        I Understand — Return to Exam
                    </button>
                )}
            </div>
        </div>
    )
}