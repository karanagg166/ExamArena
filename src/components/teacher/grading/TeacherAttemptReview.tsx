"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { api } from "@/lib/axios";
import { gradingApi } from "@/lib/api/grading";
import type { Exam } from "@/types/exam";
import type { TeacherAnswerDetail, TeacherAttempt } from "@/types/grading";
import { TeacherGradingPanel } from "./TeacherGradingPanel";
import { gradingError, isSubjective } from "./status";

export function TeacherAttemptReview({
  examId,
  attemptId,
}: {
  examId: string;
  attemptId: string;
}) {
  const [attempt, setAttempt] = useState<TeacherAttempt | null>(null);
  const [exam, setExam] = useState<Exam | null>(null);
  const [index, setIndex] = useState(0);
  const [details, setDetails] = useState<Record<string, TeacherAnswerDetail>>(
    {},
  );
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    async function load() {
      setError(null);
      try {
        const [submission, examResponse] = await Promise.all([
          gradingApi.getAttempt(attemptId),
          api.get<Exam>(`/api/v1/exams/${encodeURIComponent(examId)}`),
        ]);
        if (!active) return;
        if (submission.examId !== examId)
          throw new Error("This submission does not belong to this exam.");
        setAttempt(submission);
        setExam(examResponse.data);
      } catch (err) {
        if (active) setError(gradingError(err));
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [examId, attemptId, retry]);

  const answers = [...(attempt?.answers ?? [])].sort((a, b) => {
    const questions = exam?.questions ?? [];
    return (
      (questions.find((q) => q.id === a.questionId)?.questionNumber ?? 0) -
      (questions.find((q) => q.id === b.questionId)?.questionNumber ?? 0)
    );
  });
  const selected = answers[index];
  const selectedId = selected?.id;
  const detail = selectedId ? details[selectedId] : undefined;
  const reviewable =
    !!attempt && ["SUBMITTED", "GRADED", "EXPIRED"].includes(attempt.status);
  useEffect(() => {
    if (!selectedId || detail || !reviewable) return;
    let active = true;
    setError(null);
    gradingApi
      .getAnswer(selectedId)
      .then((answer) => {
        if (active)
          setDetails((current) => ({ ...current, [answer.id]: answer }));
      })
      .catch((err) => {
        if (active) setError(gradingError(err));
      });
    return () => {
      active = false;
    };
  }, [selectedId, detail, retry, reviewable]);

  const subjective = answers.filter((answer) =>
    isSubjective(answer.questionType),
  );
  const graded = subjective.filter(
    (answer) =>
      (details[answer.id]?.finalGrade?.gradingStatus ??
        answer.gradingStatus) === "MANUALLY_GRADED",
  ).length;
  function navigate(next: number) {
    setError(null);
    setIndex(next);
  }
  function update(answer: TeacherAnswerDetail) {
    setDetails((current) => ({ ...current, [answer.id]: answer }));
    const grade = answer.finalGrade;
    if (grade?.gradingStatus === "MANUALLY_GRADED") {
      setAttempt((current) =>
        current
          ? {
              ...current,
              answers:
                current.answers?.map((item) =>
                  item.id === answer.id
                    ? {
                        ...item,
                        marksAwarded: grade.marksAwarded,
                        feedback: grade.feedback,
                        gradingStatus: grade.gradingStatus,
                      }
                    : item,
                ) ?? null,
            }
          : current,
      );
    }
  }
  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto space-y-5">
        <Link
          href={`/teacher/exams/${examId}/results`}
          className="text-indigo-500"
        >
          Back to exam results
        </Link>
        <h1 className="text-2xl font-semibold">
          {exam?.name ?? "Submission"} — Review answers
        </h1>
        {error && (
          <div role="alert">
            <p>{error}</p>
            <Button
              variant="outline"
              onClick={() => setRetry((value) => value + 1)}
            >
              Retry loading
            </Button>
          </div>
        )}
        {!attempt && !error && <p role="status">Loading submission...</p>}
        {attempt && !reviewable && (
          <p>
            This attempt has not been submitted. Grading is available after
            submission.
          </p>
        )}
        {reviewable && (
          <>
            <p role="status">
              Subjective grading: {graded} of {subjective.length} answers graded
            </p>
            <nav
              aria-label="Question navigation"
              className="flex flex-wrap gap-2"
            >
              {answers.map((answer, position) => (
                <Button
                  key={answer.id}
                  variant={position === index ? "primary" : "outline"}
                  disabled={busy}
                  aria-current={position === index ? "step" : undefined}
                  onClick={() => navigate(position)}
                >
                  Q
                  {exam?.questions?.find((q) => q.id === answer.questionId)
                    ?.questionNumber ?? position + 1}{" "}
                  —{" "}
                  {details[answer.id]?.finalGrade?.gradingStatus ===
                  "MANUALLY_GRADED"
                    ? "Teacher graded"
                    : details[answer.id]?.aiProposal
                      ? "AI suggestion ready"
                      : answer.gradingStatus === "AUTO_GRADED"
                        ? "Auto graded"
                        : answer.gradingStatus === "MANUALLY_GRADED"
                          ? "Teacher graded"
                          : "Needs grading"}
                </Button>
              ))}
            </nav>
            {selected && !detail && !error && (
              <p role="status">Loading answer...</p>
            )}
            {detail && (
              <GlassCard className="p-4 sm:p-6">
                <TeacherGradingPanel
                  key={detail.id}
                  answer={detail}
                  onChange={update}
                  onBusyChange={setBusy}
                />
                {!isSubjective(detail.questionType) && (
                  <section className="mt-4">
                    <h3 className="font-semibold">Selected options</h3>
                    <ul>
                      {selected?.selectedOptions?.map((option) => (
                        <li key={option.optionId}>
                          {exam?.questions
                            ?.find((q) => q.id === selected.questionId)
                            ?.options?.find(
                              (item) => item.id === option.optionId,
                            )?.text ?? "Selected option unavailable"}
                        </li>
                      ))}
                    </ul>
                    {!selected?.selectedOptions?.length && (
                      <p>No option selected.</p>
                    )}
                  </section>
                )}
              </GlassCard>
            )}
            {!answers.length && <p>No answers in this submission.</p>}
            <div className="flex justify-between gap-3">
              <Button
                variant="outline"
                disabled={busy || index === 0}
                onClick={() => navigate(index - 1)}
              >
                Previous Question
              </Button>
              <Button
                variant="outline"
                disabled={busy || index >= answers.length - 1}
                onClick={() => navigate(index + 1)}
              >
                Next Question
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
