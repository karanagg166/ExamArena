-- Enrollment is deliberately modelled before a Student row exists.  The
-- runtime API uses the same PostgreSQL enum through SQLAlchemy.
CREATE TYPE "JoinRequestStatus" AS ENUM ('PENDING', 'APPROVED', 'REJECTED');

ALTER TABLE "SchoolClass"
  ADD COLUMN "joinCode" TEXT,
  ADD COLUMN "nextRollNo" INTEGER NOT NULL DEFAULT 1;

-- Existing classes need shareable codes before the NOT NULL / unique guarantees
-- are applied.  Retry in the extremely unlikely event that a generated code
-- collides with an earlier row.
DO $$
DECLARE
  class_row RECORD;
  candidate TEXT;
BEGIN
  FOR class_row IN SELECT "id" FROM "SchoolClass" WHERE "joinCode" IS NULL LOOP
    LOOP
      candidate := upper(substr(md5(class_row."id" || random()::text || clock_timestamp()::text), 1, 8));
      EXIT WHEN NOT EXISTS (
        SELECT 1 FROM "SchoolClass" WHERE "joinCode" = candidate
      );
    END LOOP;
    UPDATE "SchoolClass" SET "joinCode" = candidate WHERE "id" = class_row."id";
  END LOOP;
END $$;

-- Start new allocations after the highest numeric legacy roll number.  Legacy
-- non-numeric rolls remain valid but never affect the counter.
UPDATE "SchoolClass" AS class
SET "nextRollNo" = COALESCE(
  (
    SELECT MAX(CASE WHEN student."rollNo" ~ '^[0-9]+$' THEN student."rollNo"::INTEGER END)
    FROM "Student" AS student
    WHERE student."classId" = class."id"
  ),
  0
) + 1;

-- Stop rather than silently change a student's roll number if an older,
-- manually modified database already contains class-local duplicates.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM "Student"
    GROUP BY "classId", "rollNo"
    HAVING COUNT(*) > 1
  ) THEN
    RAISE EXCEPTION 'Cannot apply class roll-number constraint: duplicate roll numbers exist within a class';
  END IF;
END $$;

ALTER TABLE "SchoolClass" ALTER COLUMN "joinCode" SET NOT NULL;
ALTER TABLE "SchoolClass" ADD CONSTRAINT "SchoolClass_joinCode_key" UNIQUE ("joinCode");

DO $$
DECLARE
  constraint_name TEXT;
BEGIN
  SELECT conname INTO constraint_name
  FROM pg_constraint
  WHERE conrelid = '"Student"'::regclass
    AND contype = 'u'
    AND conkey = ARRAY[
      (SELECT attnum::SMALLINT FROM pg_attribute WHERE attrelid = '"Student"'::regclass AND attname = 'rollNo')
    ]::SMALLINT[];
  IF constraint_name IS NOT NULL THEN
    EXECUTE format('ALTER TABLE "Student" DROP CONSTRAINT %I', constraint_name);
  END IF;
END $$;

ALTER TABLE "Student" ADD CONSTRAINT "Student_classId_rollNo_key" UNIQUE ("classId", "rollNo");

CREATE TABLE "ClassJoinRequest" (
  "id" TEXT NOT NULL,
  "studentUserId" TEXT NOT NULL,
  "classId" TEXT NOT NULL,
  "status" "JoinRequestStatus" NOT NULL DEFAULT 'PENDING',
  "requestedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "decidedAt" TIMESTAMP(3),
  "decidedBy" TEXT,
  CONSTRAINT "ClassJoinRequest_pkey" PRIMARY KEY ("id"),
  CONSTRAINT "ClassJoinRequest_studentUserId_classId_key" UNIQUE ("studentUserId", "classId"),
  CONSTRAINT "ClassJoinRequest_studentUserId_fkey"
    FOREIGN KEY ("studentUserId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "ClassJoinRequest_classId_fkey"
    FOREIGN KEY ("classId") REFERENCES "SchoolClass"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX "ClassJoinRequest_classId_idx" ON "ClassJoinRequest"("classId");
CREATE INDEX "ClassJoinRequest_studentUserId_idx" ON "ClassJoinRequest"("studentUserId");
