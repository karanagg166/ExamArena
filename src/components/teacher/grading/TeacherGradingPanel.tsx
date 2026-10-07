"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { gradingApi } from "@/lib/api/grading";
import type { TeacherAnswerDetail, TeacherGrade } from "@/types/grading";
import { AIProposal } from "./AIProposal";
import { gradingError, gradingStatusLabel, isSubjective } from "./status";

interface Props {
  answer: TeacherAnswerDetail;
  onChange: (answer: TeacherAnswerDetail) => void;
  onBusyChange?: (busy: boolean) => void;
}
export function TeacherGradingPanel({ answer, onChange, onBusyChange }: Props) {
  const [operation, setOperation] = useState<string | null>(null);
  const busyRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [marks, setMarks] = useState("");
  const [feedback, setFeedback] = useState("");
  const subjective = isSubjective(answer.questionType);
  const final = answer.finalGrade?.gradingStatus === "MANUALLY_GRADED";
  const proposal = answer.aiProposal;
  const numberMarks = Number(marks);
  const validMarks =
    marks.trim() !== "" &&
    Number.isFinite(numberMarks) &&
    numberMarks >= 0 &&
    numberMarks <= answer.maxMarks;
  const missingContext =
    !answer.referenceAnswer?.trim() && !answer.gradingRubric?.length;

  async function run(name: string, action: () => Promise<void>) {
    if (busyRef.current) return;
    busyRef.current = true;
    setOperation(name);
    onBusyChange?.(true);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(gradingError(err, name === "Generating grading suggestion..."));
    } finally {
      busyRef.current = false;
      setOperation(null);
      onBusyChange?.(false);
    }
  }
  function finish(grade: TeacherGrade) {
    onChange({ ...answer, finalGrade: grade });
    setEditing(false);
  }
  function startEditing(useProposal: boolean) {
    setMarks(
      String(
        useProposal && proposal
          ? proposal.suggestedMarks
          : (answer.finalGrade?.marksAwarded ?? ""),
      ),
    );
    setFeedback(
      useProposal && proposal
        ? proposal.feedback
        : (answer.finalGrade?.feedback ?? ""),
    );
    setEditing(true);
  }

  return (
    <article
      className="space-y-5"
      aria-label={`Question ${answer.questionNumber}`}
    >
      <header>
        <h2 className="text-xl font-semibold">
          Question {answer.questionNumber} — {answer.maxMarks} marks
        </h2>
        <p className="text-sm text-[var(--text-muted)]">
          {answer.questionType.replaceAll("_", " ")}
        </p>
        <p>{gradingStatusLabel(answer.finalGrade?.gradingStatus)}</p>
      </header>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-5 min-w-0">
          <section>
            <h3 className="font-semibold">Question</h3>
            <p className="whitespace-pre-wrap break-words">
              {answer.questionText}
            </p>
          </section>
          <section className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-card)] p-5">
            <h3 className="text-lg font-semibold mb-3">Student Answer</h3>
            <div
              tabIndex={0}
              role="region"
              aria-label="Student answer text"
              className="max-h-[36rem] overflow-y-auto whitespace-pre-wrap break-words leading-relaxed"
            >
              {answer.studentAnswer || "No written answer submitted."}
            </div>
          </section>
          {subjective && (
            <>
              <section>
                <h3 className="font-semibold">Reference Answer</h3>
                <p className="whitespace-pre-wrap break-words">
                  {answer.referenceAnswer || "Reference answer not provided."}
                </p>
              </section>
              <section>
                <h3 className="font-semibold">Grading Rubric</h3>
                {!answer.gradingRubric?.length ? (
                  <p>Rubric not provided.</p>
                ) : (
                  <ul className="space-y-3 mt-2">
                    {answer.gradingRubric.map((item, i) => (
                      <li key={i}>
                        <p className="font-medium">
                          {typeof item.criterion === "string"
                            ? item.criterion
                            : `Criterion ${i + 1}`}{" "}
                          —{" "}
                          {typeof item.marks === "number" ||
                          typeof item.marks === "string"
                            ? item.marks
                            : "Unspecified"}{" "}
                          marks
                        </p>
                        {typeof item.description === "string" && (
                          <p className="text-sm text-[var(--text-muted)] whitespace-pre-wrap">
                            {item.description}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </>
          )}
        </div>
        <div className="space-y-4 min-w-0" aria-busy={!!operation}>
          {answer.finalGrade &&
            answer.finalGrade.gradingStatus !== "PENDING" && (
              <section
                className="rounded-xl border border-[var(--border-default)] p-4"
                aria-label="Final grade"
              >
                <h3 className="font-semibold">Final Grade</h3>
                <p className="text-2xl">
                  {answer.finalGrade.marksAwarded} / {answer.maxMarks}
                </p>
                <p>
                  Status: {gradingStatusLabel(answer.finalGrade.gradingStatus)}
                </p>
                <h4 className="font-medium mt-3">Feedback</h4>
                <p className="whitespace-pre-wrap break-words">
                  {answer.finalGrade.feedback || "No feedback provided."}
                </p>
              </section>
            )}
          {subjective && !final && (
            <>
              <h3 className="text-lg font-semibold">AI Grading</h3>
              <p className="text-sm text-[var(--text-muted)]">
                AI-assisted suggestions are drafts. You decide the final marks
                and feedback.
              </p>
              {missingContext && (
                <p role="note">
                  AI grading cannot reliably grade this answer because the
                  reference answer and rubric are missing. Manual grading is
                  still available.
                </p>
              )}
              {!proposal && (
                <Button
                  disabled={!!operation || missingContext}
                  onClick={() =>
                    run("Generating grading suggestion...", async () => {
                      const aiProposal = await gradingApi.generateAiGrade(
                        answer.id,
                      );
                      onChange({ ...answer, aiProposal });
                    })
                  }
                >
                  Generate AI Grading Suggestion
                </Button>
              )}
              {proposal && (
                <>
                  <AIProposal proposal={proposal} />
                  <p>
                    {proposal.suggestedMarks} / {answer.maxMarks} and the
                    suggested feedback will become the final teacher-approved
                    grade when you accept.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      disabled={!!operation || editing}
                      onClick={() =>
                        run("Accepting AI suggestion...", async () =>
                          finish(await gradingApi.acceptAiGrade(answer.id)),
                        )
                      }
                    >
                      Accept AI Suggestion
                    </Button>
                    <Button
                      variant="outline"
                      disabled={!!operation || editing}
                      onClick={() => startEditing(true)}
                    >
                      Modify AI Grade
                    </Button>
                    <Button
                      variant="outline"
                      disabled={!!operation}
                      onClick={() =>
                        run("Rejecting AI suggestion...", async () => {
                          await gradingApi.rejectAiGrade(answer.id);
                          onChange({ ...answer, aiProposal: null });
                        })
                      }
                    >
                      Reject AI Suggestion
                    </Button>
                  </div>
                  {editing && (
                    <p className="text-sm">
                      Save your edited marks and feedback below to finalize
                      them.
                    </p>
                  )}
                </>
              )}
              {!editing && (
                <Button
                  variant="secondary"
                  disabled={!!operation}
                  onClick={() => startEditing(false)}
                >
                  Grade Manually
                </Button>
              )}
            </>
          )}
          {subjective && editing && !final && (
            <form
              noValidate
              className="space-y-3"
              onSubmit={(event) => {
                event.preventDefault();
                if (!validMarks) {
                  setError(`Marks must be between 0 and ${answer.maxMarks}.`);
                  return;
                }
                void run("Saving grade...", async () =>
                  finish(
                    await gradingApi.updateManualGrade(answer.id, {
                      marks: numberMarks,
                      feedback,
                    }),
                  ),
                );
              }}
            >
              <label htmlFor={`marks-${answer.id}`}>
                Marks / {answer.maxMarks}
              </label>
              <Input
                id={`marks-${answer.id}`}
                type="number"
                min={0}
                max={answer.maxMarks}
                step="any"
                value={marks}
                disabled={!!operation}
                onChange={(e) => setMarks(e.target.value)}
                aria-invalid={!validMarks}
                aria-describedby={`bounds-${answer.id}`}
              />
              <p id={`bounds-${answer.id}`} className="text-sm">
                Enter marks from 0 to {answer.maxMarks}. Decimals are allowed.
              </p>
              <label htmlFor={`feedback-${answer.id}`}>Feedback</label>
              <Textarea
                id={`feedback-${answer.id}`}
                value={feedback}
                disabled={!!operation}
                onChange={(e) => setFeedback(e.target.value)}
              />
              <p className="text-sm">
                Saving makes these marks and feedback the final teacher-approved
                grade.
              </p>
              <Button type="submit" disabled={!!operation || !validMarks}>
                Save Grade
              </Button>
              <Button
                type="button"
                variant="ghost"
                disabled={!!operation}
                onClick={() => setEditing(false)}
              >
                Cancel editing
              </Button>
            </form>
          )}
          {operation && <p role="status">{operation}</p>}
          {error && (
            <p role="alert" className="text-red-500">
              {error}
            </p>
          )}
        </div>
      </div>
    </article>
  );
}
