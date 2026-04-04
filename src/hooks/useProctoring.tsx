/* eslint-disable react-hooks/exhaustive-deps */
// src/hooks/useProctoring.ts
import { useEffect, useRef, useCallback, useState } from "react"

interface ProctoringConfig {
    maxWarnings: number          // auto-submit after X violations
    onWarning: (count: number, reason: string) => void
    onAutoSubmit: () => void     // called when max warnings reached
    onFullscreenExit: () => void
    enabled: boolean             // false when exam submitted
}

export const useProctoring = ({
    maxWarnings = 3,
    onWarning,
    onAutoSubmit,
    onFullscreenExit,
    enabled,
}: ProctoringConfig) => {
    const [warningCount, setWarningCount] = useState(0)
    const [isFullscreen, setIsFullscreen] = useState(false)
    const warningRef = useRef(0)
    const enabledRef = useRef(enabled)

    // Keep ref in sync so event handlers always see the latest value
    useEffect(() => {
        enabledRef.current = enabled
    }, [enabled])

    // ── Enter Fullscreen ───────────────────────────────────────────
    const enterFullscreen = useCallback(async () => {
        try {
            if (!document.fullscreenElement) {
                await document.documentElement.requestFullscreen()
            }
            setIsFullscreen(true)
        } catch {
            console.warn("Fullscreen request denied or failed")
        }
    }, [])

    // ── Trigger Warning ───────────────────────────────────────────
    const triggerWarning = useCallback((reason: string) => {
        if (!enabledRef.current) return
        warningRef.current += 1
        const newCount = warningRef.current
        setWarningCount(newCount)
        onWarning(newCount, reason)

        if (newCount >= maxWarnings) {
            onAutoSubmit()
        }
    }, [maxWarnings, onWarning, onAutoSubmit])

    useEffect(() => {
        if (!enabled) return

        // ── 1. Fullscreen Change ─────────────────────────────────────
        const handleFullscreenChange = () => {
            if (!document.fullscreenElement) {
                setIsFullscreen(false)
                onFullscreenExit()
                triggerWarning("Exited fullscreen")
            } else {
                setIsFullscreen(true)
            }
        }

        // ── 2. Tab Visibility ────────────────────────────────────────
        const handleVisibilityChange = () => {
            if (document.hidden) {
                triggerWarning("Switched tab or minimized window")
            }
        }

        // ── 3. Window Blur (Alt+Tab, clicked outside) ────────────────
        const handleWindowBlur = () => {
            triggerWarning("Window lost focus")
        }

        // ── 4. Right Click Disabled ──────────────────────────────────
        const handleContextMenu = (e: MouseEvent) => {
            e.preventDefault()
        }

        // ── 5. Keyboard Shortcuts Blocked ───────────────────────────
        const handleKeyDown = (e: KeyboardEvent) => {
            // NOTE: Escape key exits fullscreen at the browser level BEFORE JS can intercept it.
            // We handle that via fullscreenchange event, NOT by blocking Escape.
            const blocked = [
                // Tab switching
                e.ctrlKey && e.key === "Tab",
                e.altKey && e.key === "Tab",
                // New tab/window
                e.ctrlKey && e.key === "t",
                e.ctrlKey && e.key === "n",
                e.ctrlKey && e.key === "w",
                // DevTools
                e.key === "F12",
                e.ctrlKey && e.shiftKey && e.key === "I",
                e.ctrlKey && e.shiftKey && e.key === "J",
                e.ctrlKey && e.shiftKey && e.key === "C",
                // Print screen
                e.key === "PrintScreen",
                // Reload
                e.key === "F5",
                e.ctrlKey && e.key === "r",
                // Copy/paste
                e.ctrlKey && e.key === "c",
                e.ctrlKey && e.key === "v",
            ]

            if (blocked.some(Boolean)) {
                e.preventDefault()
                e.stopPropagation()

                if (e.key === "F12" || (e.ctrlKey && e.shiftKey)) {
                    triggerWarning("Attempted to open DevTools")
                }
            }
        }

        // ── 6. Text Selection Disabled ───────────────────────────────
        const handleSelectStart = (e: Event) => {
            // Allow selection inside textarea elements (for typing answers)
            if ((e.target as HTMLElement)?.tagName === "TEXTAREA") return
            e.preventDefault()
        }

        // ── 7. Copy Disabled ─────────────────────────────────────────
        const handleCopy = (e: ClipboardEvent) => {
            e.preventDefault()
        }

        // ── Register All Listeners ───────────────────────────────────
        document.addEventListener("fullscreenchange", handleFullscreenChange)
        document.addEventListener("visibilitychange", handleVisibilityChange)
        document.addEventListener("contextmenu", handleContextMenu)
        document.addEventListener("keydown", handleKeyDown)
        document.addEventListener("selectstart", handleSelectStart)
        document.addEventListener("copy", handleCopy)
        window.addEventListener("blur", handleWindowBlur)

        // ── Check current fullscreen state on mount ──────────────────
        setIsFullscreen(!!document.fullscreenElement)

        // ── Cleanup ──────────────────────────────────────────────────
        return () => {
            document.removeEventListener("fullscreenchange", handleFullscreenChange)
            document.removeEventListener("visibilitychange", handleVisibilityChange)
            document.removeEventListener("contextmenu", handleContextMenu)
            document.removeEventListener("keydown", handleKeyDown)
            document.removeEventListener("selectstart", handleSelectStart)
            document.removeEventListener("copy", handleCopy)
            window.removeEventListener("blur", handleWindowBlur)

            // Exit fullscreen when exam done
            if (document.fullscreenElement) {
                document.exitFullscreen().catch(() => {})
            }
        }
    }, [enabled])

    return {
        isFullscreen,
        warningCount,
        enterFullscreen,
    }
}