export type Exam = {
  id: string;
  name: string;
  description: string;
  date: string;
  duration: number;
  maxMarks: number;
  type: "MIDTERM" | "FINAL" | "QUIZ" | "ASSIGNMENT" | "MOCK";
  teacherId: string;
  createdAt: string;
  updatedAt: string;
};
