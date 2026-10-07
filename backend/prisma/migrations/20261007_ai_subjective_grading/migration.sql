-- AlterTable: Add AI grading proposal and final grading metadata to StudentExamAnswer
ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiSuggestedMarks" DOUBLE PRECISION;
ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiConfidence" VARCHAR;
ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiFeedback" TEXT;
ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiGradingBreakdown" JSONB;
ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiWarnings" JSONB;
ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "aiGradedAt" TIMESTAMPTZ;
ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "gradedBy" VARCHAR;
ALTER TABLE "StudentExamAnswer" ADD COLUMN IF NOT EXISTS "gradedAt" TIMESTAMPTZ;
