import type { AIGradingProposal } from "@/types/grading";

const confidenceDescriptions: Record<string, string> = {
  HIGH: "The AI reports a clear match to the supplied grading context.",
  MEDIUM: "Some aspects of the answer need closer teacher review.",
  LOW: "Review the answer and grading context carefully before deciding.",
};
export function AIProposal({ proposal }: { proposal: AIGradingProposal }) {
  return (
    <section
      className="space-y-4 rounded-xl border border-[var(--border-default)] p-4"
      aria-label="AI grading suggestion"
    >
      <h3 className="font-semibold">
        AI Suggested Score: {proposal.suggestedMarks} / {proposal.maxMarks}
      </h3>
      <p>Confidence: {proposal.confidence}</p>
      <p className="text-sm text-[var(--text-muted)]">
        {confidenceDescriptions[proposal.confidence] ??
          "Review this suggestion carefully."}{" "}
        Confidence does not guarantee correctness. Teacher review required.
      </p>
      {proposal.warnings.length > 0 && (
        <div role="note" className="rounded-lg border border-amber-500 p-3">
          <h4 className="font-semibold">AI warnings</h4>
          <ul className="list-disc pl-5">
            {proposal.warnings.map((warning, i) => (
              <li key={i}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
      <h4 className="font-semibold">Rubric Breakdown</h4>
      {proposal.rubricBreakdown.length === 0 ? (
        <p>No rubric breakdown supplied.</p>
      ) : (
        <ul className="space-y-3">
          {proposal.rubricBreakdown.map((item, i) => (
            <li
              key={i}
              className="border-b border-[var(--border-default)] pb-2"
            >
              <p className="font-medium">
                {item.criterion} — {item.awardedMarks} / {item.maxMarks}
              </p>
              <p className="text-sm">
                {item.awardedMarks >= item.maxMarks
                  ? "Full credit"
                  : item.awardedMarks > 0
                    ? "Partial credit"
                    : "No credit"}
              </p>
              <p className="text-sm text-[var(--text-muted)] whitespace-pre-wrap">
                {item.justification}
              </p>
            </li>
          ))}
        </ul>
      )}
      <h4 className="font-semibold">Suggested Feedback</h4>
      <p className="whitespace-pre-wrap break-words">
        {proposal.feedback || "No feedback supplied."}
      </p>
    </section>
  );
}
