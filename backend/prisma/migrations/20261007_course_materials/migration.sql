-- CreateEnum
CREATE TYPE "CourseMaterialDocumentType" AS ENUM ('TEXTBOOK', 'TEACHER_NOTES', 'SYLLABUS', 'QUESTION_BANK', 'PAST_PAPER', 'OTHER');

-- CreateEnum
CREATE TYPE "CourseMaterialStatus" AS ENUM ('UPLOADED', 'PROCESSING', 'READY', 'FAILED');

-- CreateTable
CREATE TABLE IF NOT EXISTS "CourseMaterial" (
    "id" TEXT NOT NULL,
    "schoolId" TEXT NOT NULL,
    "subject" "Subject" NOT NULL,
    "classId" TEXT,
    "uploadedBy" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "originalFileName" TEXT NOT NULL,
    "fileSize" INTEGER NOT NULL,
    "mimeType" TEXT NOT NULL,
    "documentType" "CourseMaterialDocumentType" NOT NULL DEFAULT 'OTHER',
    "searchSphereDocumentId" TEXT,
    "searchSphereCollectionId" TEXT NOT NULL,
    "status" "CourseMaterialStatus" NOT NULL DEFAULT 'UPLOADED',
    "processingError" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "CourseMaterial_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "coursematerial_schoolid_idx" ON "CourseMaterial"("schoolId");
CREATE INDEX IF NOT EXISTS "coursematerial_subject_idx" ON "CourseMaterial"("subject");
CREATE INDEX IF NOT EXISTS "coursematerial_classid_idx" ON "CourseMaterial"("classId");
CREATE INDEX IF NOT EXISTS "coursematerial_uploadedby_idx" ON "CourseMaterial"("uploadedBy");
CREATE INDEX IF NOT EXISTS "coursematerial_status_idx" ON "CourseMaterial"("status");
CREATE INDEX IF NOT EXISTS "coursematerial_spheredocid_idx" ON "CourseMaterial"("searchSphereDocumentId");

-- AddForeignKey
ALTER TABLE "CourseMaterial" ADD CONSTRAINT "CourseMaterial_schoolId_fkey" FOREIGN KEY ("schoolId") REFERENCES "School"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "CourseMaterial" ADD CONSTRAINT "CourseMaterial_classId_fkey" FOREIGN KEY ("classId") REFERENCES "SchoolClass"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "CourseMaterial" ADD CONSTRAINT "CourseMaterial_uploadedBy_fkey" FOREIGN KEY ("uploadedBy") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;
