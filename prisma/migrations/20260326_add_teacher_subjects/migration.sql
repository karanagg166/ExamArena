-- AlterTable: Add subjects column to Teacher with default empty JSON array
ALTER TABLE "Teacher" ADD COLUMN "subjects" TEXT NOT NULL DEFAULT '[]';
