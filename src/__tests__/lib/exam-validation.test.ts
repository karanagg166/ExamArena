import { describe, it, expect } from "vitest";
import { validateExam, computeMaxMarks } from "@/lib/exam-validation";

describe("validateExam", () => {
  const validQuestion = {
    text: "What is 2+2?",
    questionNumber: 1,
    marks: 5,
    section: "Section A",
    questionType: "MULTIPLE_CHOICE" as const,
    options: [
      { text: "3", optionNumber: 1, isCorrect: false },
      { text: "4", optionNumber: 2, isCorrect: true },
    ],
  };

  const validExam = {
    name: "Math Quiz",
    description: "A test description",
    scheduledAt: "2020-01-01T00:00:00Z",
    duration: 30,
    type: "QUIZ" as const,
    maxMarks: 5,
    questions: [validQuestion],
  };

  it("returns null for a valid exam", () => {
    expect(validateExam(validExam)).toBeNull();
  });

  it("rejects empty exam title", () => {
    expect(validateExam({ ...validExam, name: "  " })).toContain("title");
  });

  it("rejects empty description", () => {
    expect(validateExam({ ...validExam, description: "" })).toContain("Description");
  });

  it("rejects missing scheduledAt", () => {
    expect(validateExam({ ...validExam, scheduledAt: "" })).toContain("Scheduled");
  });

  it("allows past scheduledAt date without error", () => {
    expect(validateExam({ ...validExam, scheduledAt: "2020-01-01T00:00:00Z" })).toBeNull();
  });

  it("rejects duration less than 5 minutes", () => {
    expect(validateExam({ ...validExam, duration: 3 })).toContain("5 minutes");
  });

  it("rejects empty questions list", () => {
    expect(validateExam({ ...validExam, questions: [] })).toContain("at least one question");
  });

  it("rejects empty question text with explicit question number and section", () => {
    const q = { ...validQuestion, text: "   " };
    const error = validateExam({ ...validExam, questions: [q] });
    expect(error).toContain("Question 1 in Section A cannot be empty");
  });

  it("rejects empty option text with explicit option number and question", () => {
    const q = {
      ...validQuestion,
      options: [
        { text: "", optionNumber: 1, isCorrect: false },
        { text: "4", optionNumber: 2, isCorrect: true },
      ],
    };
    const error = validateExam({ ...validExam, questions: [q] });
    expect(error).toContain("Option 1 for Question 1 in Section A cannot be empty");
  });

  it("rejects Multiple Choice question without any correct option", () => {
    const q = {
      ...validQuestion,
      options: [
        { text: "3", optionNumber: 1, isCorrect: false },
        { text: "4", optionNumber: 2, isCorrect: false },
      ],
    };
    const error = validateExam({ ...validExam, questions: [q] });
    expect(error).toContain("must have at least one correct option selected");
  });

  it("rejects TRUE_FALSE with not exactly 2 options", () => {
    const q = {
      ...validQuestion,
      questionType: "TRUE_FALSE" as const,
      options: [{ text: "True", optionNumber: 1, isCorrect: true }],
    };
    const error = validateExam({ ...validExam, questions: [q] });
    expect(error).toContain("must have exactly 2 options");
  });

  it("rejects invalid section name", () => {
    const q = { ...validQuestion, section: "Part 1" };
    const error = validateExam({ ...validExam, questions: [q] });
    expect(error).toContain('Invalid section "Part 1"');
  });

  it("rejects question with marks <= 0", () => {
    const q = { ...validQuestion, marks: 0 };
    const error = validateExam({ ...validExam, questions: [q] });
    expect(error).toContain("must have marks greater than 0");
  });

  it("computes maxMarks as sum of question marks", () => {
    const q1 = { ...validQuestion, marks: 10 };
    const q2 = { ...validQuestion, questionNumber: 2, marks: 15 };
    expect(computeMaxMarks([q1, q2])).toBe(25);
  });
});
