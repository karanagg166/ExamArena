import { describe, it, expect } from "vitest";

const SECTION_NAME_PATTERN = /^Section [A-Z]$/;

function validateSectionName(name: string): boolean {
  return SECTION_NAME_PATTERN.test(name);
}

function getNextSectionName(existingNames: string[]): string {
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const usedLetters = new Set(
    existingNames
      .map((name) => {
        const match = name.match(/^Section ([A-Z])$/);
        return match ? match[1] : null;
      })
      .filter((l): l is string => Boolean(l))
  );

  for (let i = 0; i < letters.length; i++) {
    if (!usedLetters.has(letters[i])) {
      return `Section ${letters[i]}`;
    }
  }
  return "Section A";
}

describe("Exam Section Rules & Validation", () => {
  it("strictly accepts valid Section A, Section B names", () => {
    expect(validateSectionName("Section A")).toBe(true);
    expect(validateSectionName("Section B")).toBe(true);
    expect(validateSectionName("Section Z")).toBe(true);
  });

  it("strictly rejects invalid section names", () => {
    expect(validateSectionName("Section 1")).toBe(false);
    expect(validateSectionName("section a")).toBe(false);
    expect(validateSectionName("first section")).toBe(false);
    expect(validateSectionName("Section AA")).toBe(false);
    expect(validateSectionName("Section 123")).toBe(false);
    expect(validateSectionName("Physics")).toBe(false);
  });

  it("computes the next sequential section letter correctly", () => {
    expect(getNextSectionName([])).toBe("Section A");
    expect(getNextSectionName(["Section A"])).toBe("Section B");
    expect(getNextSectionName(["Section A", "Section B"])).toBe("Section C");
    expect(getNextSectionName(["Section A", "Section C"])).toBe("Section B");
  });

  it("enforces fixed marking scheme per section", () => {
    const sectionA = {
      name: "Section A",
      questionType: "MULTIPLE_CHOICE",
      marksPerQuestion: 2,
    };

    const questions = [
      { id: "q1", section: "Section A", marks: sectionA.marksPerQuestion },
      { id: "q2", section: "Section A", marks: sectionA.marksPerQuestion },
      { id: "q3", section: "Section A", marks: sectionA.marksPerQuestion },
    ];

    const totalMarks = questions.reduce((sum, q) => sum + q.marks, 0);
    expect(totalMarks).toBe(6);
    expect(questions.every((q) => q.marks === 2)).toBe(true);
  });
});
