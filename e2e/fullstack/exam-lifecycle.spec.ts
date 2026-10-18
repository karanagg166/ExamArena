import { test, expect, type Page, type BrowserContext } from '@playwright/test';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const DEFAULT_PASSWORD = 'Password123!';

const USERS = {
  teacher: {
    email: 'teacher.e2e@examarena.dev',
    name: 'Prof. FullStack',
    role: 'TEACHER',
  },
  student1: {
    email: 'student1.e2e@examarena.dev',
    name: 'Student Alice',
    role: 'STUDENT',
  },
  student2: {
    email: 'student2.e2e@examarena.dev',
    name: 'Student Bob',
    role: 'STUDENT',
  },
  outsider: {
    email: 'outsider.e2e@examarena.dev',
    name: 'Student Charlie (Outsider)',
    role: 'STUDENT',
  },
};

/**
 * Log in via UI form and wait for role-based dashboard landing page.
 */
async function loginViaUI(page: Page, email: string, password = DEFAULT_PASSWORD) {
  await page.goto('/login');
  await page.locator('input[type="email"], input#email').fill(email);
  await page.locator('input[type="password"], input#password').fill(password);
  await page.getByRole('button', { name: /sign in|login/i }).click();
  await page.waitForURL(/\/(student|teacher|principal)/, { timeout: 15000 });
}

/**
 * Perform login via backend API to get authenticated cookie state.
 */
async function loginViaApi(context: BrowserContext, email: string, password = DEFAULT_PASSWORD) {
  const res = await context.request.post(`${BACKEND_URL}/api/v1/auth/login`, {
    data: { email, password },
  });
  expect(res.status()).toBe(200);
  const data = await res.json();
  return data;
}

test.describe('Full-Stack Real Exam Lifecycle & Verification (Unmocked)', () => {
  test.describe.configure({ mode: 'serial' });

  let teacherContext: BrowserContext;
  let student1Context: BrowserContext;
  let student2Context: BrowserContext;
  let outsiderContext: BrowserContext;

  let examId = '';
  let examCode = 'E2E-MASTERY-101';
  let student1AttemptId = '';
  let q1Id = '';
  let q2Id = '';
  let opt2Id = ''; // Correct MCQ option (O(n))
  let q2AnswerId = '';

  test.beforeAll(async ({ browser }) => {
    // Isolated browser contexts for each synthetic user
    teacherContext = await browser.newContext();
    student1Context = await browser.newContext();
    student2Context = await browser.newContext();
    outsiderContext = await browser.newContext();
  });

  test.afterAll(async () => {
    await teacherContext?.close();
    await student1Context?.close();
    await student2Context?.close();
    await outsiderContext?.close();
  });

  test.beforeEach(() => {
    test.setTimeout(90_000);
  });

  test('Step 1: Teacher setup, verification, and student discovery', async () => {
    const teacherPage = await teacherContext.newPage();

    // 1. Authenticate through the real UI
    await loginViaUI(teacherPage, USERS.teacher.email);
    expect(teacherPage.url()).toContain('/teacher');

    // 2. Fetch teacher's exams via authorized API
    const examsRes = await teacherContext.request.get(`${BACKEND_URL}/api/v1/exams`);
    expect(examsRes.status()).toBe(200);
    const exams = await examsRes.json();
    const e2eExam = exams.find((e: { examCode?: string }) => e.examCode === examCode);
    expect(e2eExam).toBeDefined();
    examId = e2eExam.id;
    expect(e2eExam.isPublished).toBe(true);
    expect(e2eExam.maxMarks).toBe(10);

    // Verify question IDs from exam details
    const examDetailRes = await teacherContext.request.get(`${BACKEND_URL}/api/v1/exams/${examId}`);
    expect(examDetailRes.status()).toBe(200);
    const examDetail = await examDetailRes.json();
    expect(examDetail.questions.length).toBe(2);

    const q1 = examDetail.questions.find((q: { questionType: string }) => q.questionType === 'MULTIPLE_CHOICE');
    const q2 = examDetail.questions.find((q: { questionType: string }) => q.questionType === 'SHORT_ANSWER');
    expect(q1).toBeDefined();
    expect(q2).toBeDefined();
    q1Id = q1.id;
    q2Id = q2.id;

    // Find correct option for Q1
    const optCorrect = q1.options.find((o: { isCorrect?: boolean; text: string }) => o.isCorrect || o.text === 'O(n)');
    expect(optCorrect).toBeDefined();
    opt2Id = optCorrect.id;

    // 3. Authenticate Student 1 via UI and verify exam is visible
    const studentPage = await student1Context.newPage();
    await loginViaUI(studentPage, USERS.student1.email);
    expect(studentPage.url()).toContain('/student');

    // Verify student sees exam in their assigned exams list
    const studentExamsRes = await student1Context.request.get(`${BACKEND_URL}/api/v1/exams/student`);
    expect(studentExamsRes.status()).toBe(200);
    const studentExams = await studentExamsRes.json();
    const visibleExam = studentExams.find((e: { id: string }) => e.id === examId);
    expect(visibleExam).toBeDefined();
    expect(visibleExam.name).toContain('E2E Mastery Certification');
    expect(visibleExam.studentStatus).toBe('NOT_ATTEMPTED');

    await teacherPage.close();
    await studentPage.close();
  });

  test('Step 2: Access control checks before attempt', async () => {
    // 1. Authenticate Outsider (different school)
    await loginViaApi(outsiderContext, USERS.outsider.email);

    // Outsider must NOT see the exam in their student exam list
    const outsiderExamsRes = await outsiderContext.request.get(`${BACKEND_URL}/api/v1/exams/student`);
    expect(outsiderExamsRes.status()).toBe(200);
    const outsiderExams = await outsiderExamsRes.json();
    const foundExam = outsiderExams.find((e: { id: string }) => e.id === examId);
    expect(foundExam).toBeUndefined();

    // Outsider cannot start this exam (must return 403 Forbidden)
    const outsiderStartRes = await outsiderContext.request.post(`${BACKEND_URL}/api/v1/attempts/start`, {
      data: { examId, examCode },
    });
    expect([400, 403]).toContain(outsiderStartRes.status());
    const errorJson = await outsiderStartRes.json();
    expect(errorJson.detail).toContain('not enrolled in the school');

    // 2. Student cannot release results (only teacher/admin)
    const studentReleaseRes = await student1Context.request.post(`${BACKEND_URL}/api/v1/exams/${examId}/release-results`);
    expect(studentReleaseRes.status()).toBe(403);

    // 3. Student cannot access scoreboard results before release
    const studentScoreboardRes = await student1Context.request.get(`${BACKEND_URL}/api/v1/exams/${examId}/results`);
    expect(studentScoreboardRes.status()).toBe(403);
  });

  test('Step 3: Student start, autosave persistence, intentional clearing, and submission', async () => {
    test.setTimeout(120_000);
    const studentPage = await student1Context.newPage();

    // Navigate to exam start page
    await studentPage.goto(`/student/exams/${examId}/start`);
    await studentPage.waitForLoadState('networkidle');

    // Agree to guidelines checkbox
    const agreeCheckbox = studentPage.locator('input[type="checkbox"], button[role="checkbox"]');
    if (await agreeCheckbox.isVisible()) {
      await agreeCheckbox.click();
    }

    // Fill exam code if prompted
    const codeInput = studentPage.locator('#exam-code-input, input[placeholder*="password" i], input[placeholder*="code" i]');
    if (await codeInput.isVisible()) {
      await codeInput.fill(examCode);
    }

    // Click "Start Exam"
    const startButton = studentPage.getByRole('button', { name: /start exam|begin/i });
    await expect(startButton).toBeEnabled();
    await startButton.click();

    // Verify redirected to exam attempt page
    await studentPage.waitForURL(new RegExp(`/student/exams/${examId}/attempt`), { timeout: 15000 });

    // Retrieve attempt ID from API or store
    const myExamsRes = await student1Context.request.get(`${BACKEND_URL}/api/v1/exams/student`);
    const myExams = await myExamsRes.json();
    const currentExam = myExams.find((e: { id: string }) => e.id === examId);
    expect(currentExam.attemptId).toBeTruthy();
    student1AttemptId = currentExam.attemptId;

    // ─── Answer Q1 (Objective MCQ) ───
    const q1Radio = studentPage.locator(`input[value="${opt2Id}"]`).or(
      studentPage.locator('label').filter({ hasText: 'O(n)' }).locator('input')
    );
    await q1Radio.first().click();

    // ─── Navigate to Q2 (Subjective) and answer ───
    const nextBtn = studentPage.getByRole('button', { name: /next/i });
    if (await nextBtn.isVisible() && await nextBtn.isEnabled()) {
      await nextBtn.click();
    } else {
      // Click Q2 palette badge if present
      const q2Badge = studentPage.locator('button, div').filter({ hasText: /^2$/ }).first();
      if (await q2Badge.isVisible()) await q2Badge.click();
    }

    const textarea = studentPage.locator('textarea');
    await expect(textarea).toBeVisible({ timeout: 10000 });
    const fullAcidAnswer =
      'Atomicity guarantees all or nothing transactions. Consistency ensures state invariants. Isolation keeps concurrent operations separate. Durability guarantees committed transactions survive failures.';
    await textarea.fill(fullAcidAnswer);

    // Wait for server autosave to complete (UI displays "Draft saved")
    await expect(studentPage.getByText(/draft saved/i)).toBeVisible({ timeout: 15000 });

    // ─── Read saved attempt directly through backend API to assert durable persistence ───
    const attemptDraftRes = await student1Context.request.get(`${BACKEND_URL}/api/v1/attempts/${student1AttemptId}`);
    expect(attemptDraftRes.status()).toBe(200);
    const draftData = await attemptDraftRes.json();
    expect(draftData.draftRevision).toBeGreaterThanOrEqual(1);

    const answersMap = new Map(draftData.answers.map((a: { questionId: string }) => [a.questionId, a]));
    const savedQ1 = answersMap.get(q1Id) as { selectedOptions?: { optionId: string }[] };
    const savedQ2 = answersMap.get(q2Id) as { textAnswer?: string; id: string };
    q2AnswerId = savedQ2.id;

    expect(savedQ1.selectedOptions?.[0]?.optionId).toBe(opt2Id);
    expect(savedQ2.textAnswer).toBe(fullAcidAnswer);

    // ─── Browser Reload: Verify persisted answers restore from server ───
    await studentPage.reload();
    await studentPage.waitForLoadState('networkidle');

    // Confirm Q1 has option selected
    const q1RadioRestored = studentPage.locator('label').filter({ hasText: 'O(n)' }).locator('input');
    await expect(q1RadioRestored.first()).toBeChecked({ timeout: 10000 });

    // Navigate to Q2 and confirm textarea still contains persisted answer
    const nextBtnReload = studentPage.getByRole('button', { name: /next/i });
    if (await nextBtnReload.isVisible() && await nextBtnReload.isEnabled()) {
      await nextBtnReload.click();
    } else {
      const q2Badge = studentPage.locator('button, div').filter({ hasText: /^2$/ }).first();
      if (await q2Badge.isVisible()) await q2Badge.click();
    }
    await expect(studentPage.locator('textarea')).toHaveValue(fullAcidAnswer, { timeout: 10000 });

    // ─── Intentionally Clear an Answer (Q2 Subjective) ───
    const clearBtn = studentPage.getByRole('button', { name: /clear response/i });
    await expect(clearBtn).toBeVisible({ timeout: 5000 });
    await clearBtn.click();
    await expect(studentPage.locator('textarea')).toHaveValue('');

    // Wait for autosave to acknowledge intentional clear
    await expect(studentPage.getByText(/draft saved/i)).toBeVisible({ timeout: 15000 });

    // Reload again to verify intentional clearing persisted
    await studentPage.reload();
    await studentPage.waitForLoadState('networkidle');

    // Verify on server that Q2 answer was cleared
    const clearedAttemptRes = await student1Context.request.get(`${BACKEND_URL}/api/v1/attempts/${student1AttemptId}`);
    const clearedData = await clearedAttemptRes.json();
    const clearedAnsMap = new Map(clearedData.answers.map((a: { questionId: string }) => [a.questionId, a]));
    const clearedQ2 = clearedAnsMap.get(q2Id) as { textAnswer?: string };
    expect(clearedQ2.textAnswer || '').toBe('');

    // ─── Re-enter intended answer for Q2 ───
    const nextBtnReload2 = studentPage.getByRole('button', { name: /next/i });
    if (await nextBtnReload2.isVisible() && await nextBtnReload2.isEnabled()) {
      await nextBtnReload2.click();
    } else {
      const q2Badge2 = studentPage.locator('button, div').filter({ hasText: /^2$/ }).first();
      if (await q2Badge2.isVisible()) await q2Badge2.click();
    }
    await studentPage.locator('textarea').fill(fullAcidAnswer);
    await expect(studentPage.getByText(/draft saved/i)).toBeVisible({ timeout: 15000 });

    // ─── Submit through Real Application ───
    const submitBtn = studentPage.getByRole('button', { name: /submit exam/i });
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();

    // Confirm dialog if shown
    const confirmModalSubmit = studentPage.locator('[role="dialog"]').getByRole('button', { name: /submit|confirm/i });
    if (await confirmModalSubmit.isVisible()) {
      await confirmModalSubmit.click();
    }

    // Verify student is navigated to results view
    await studentPage.waitForURL(new RegExp(`/student/exams/${examId}/result`), { timeout: 15000 });

    // ─── Assert Server Database Attempt Status ───
    const submittedAttemptRes = await student1Context.request.get(`${BACKEND_URL}/api/v1/attempts/${student1AttemptId}`);
    expect(submittedAttemptRes.status()).toBe(200);
    const submittedData = await submittedAttemptRes.json();
    expect(submittedData.status).toBe('SUBMITTED');

    await studentPage.close();
  });

  test('Step 4: Real Teacher Grading, Score Recalculation, and Student Redaction Pre-Release', async () => {
    // 1. Verify subjective answer is pending and scores are redacted for student
    const preReleaseStudentRes = await student1Context.request.get(`${BACKEND_URL}/api/v1/attempts/${student1AttemptId}`);
    expect(preReleaseStudentRes.status()).toBe(200);
    const preReleaseData = await preReleaseStudentRes.json();

    // Redaction invariant: Before release, student cannot see marks or feedback
    expect(preReleaseData.marksObtained).toBeNull();
    for (const ans of preReleaseData.answers) {
      expect(ans.marksAwarded).toBeNull();
      expect(ans.isCorrect).toBeNull();
      expect(ans.feedback).toBeNull();
    }

    // 2. In Student UI, verify pending release message is shown
    const studentPage = await student1Context.newPage();
    await studentPage.goto(`/student/exams/${examId}/result`);
    await expect(studentPage.getByText(/pending teacher release|evaluate and release results soon/i).first()).toBeVisible({ timeout: 15000 });
    // Total score must NOT be visible yet
    await expect(studentPage.getByText(/Score Obtained/i)).not.toBeVisible();
    await studentPage.close();

    // 3. Authenticate Teacher and grade subjective answer through real grading API
    await loginViaApi(teacherContext, USERS.teacher.email);

    // Apply manual grade: 5.0 marks with detailed rubric feedback
    const gradeRes = await teacherContext.request.patch(
      `${BACKEND_URL}/api/v1/student-answers/${q2AnswerId}/grade`,
      {
        data: {
          marks: 5.0,
          feedback: 'Excellent explanation of ACID properties. All criteria fully satisfied.',
        },
      }
    );
    expect(gradeRes.status()).toBe(200);
    const gradeData = await gradeRes.json();
    expect(gradeData.marksAwarded).toBe(5.0);
    expect(gradeData.gradingStatus).toBe('MANUALLY_GRADED');
    expect(gradeData.isCorrect).toBe('FULLY_CORRECT');

    // 4. Verify teacher sees recalculated attempt total (5 MCQ + 5 Subjective = 10 / 10 marks)
    const teacherAttemptRes = await teacherContext.request.get(`${BACKEND_URL}/api/v1/attempts/${student1AttemptId}`);
    expect(teacherAttemptRes.status()).toBe(200);
    const teacherAttemptData = await teacherAttemptRes.json();
    expect(teacherAttemptData.status).toBe('GRADED');
    expect(teacherAttemptData.marksObtained).toBe(10.0);

    // 5. Still before release, student API MUST still be redacted!
    const stillRedactedRes = await student1Context.request.get(`${BACKEND_URL}/api/v1/attempts/${student1AttemptId}`);
    const stillRedactedData = await stillRedactedRes.json();
    expect(stillRedactedData.marksObtained).toBeNull();
  });

  test('Step 5: Teacher Releases Results and Student Observes Verified Scores and Feedback', async () => {
    // 1. Teacher releases results via actual release API (NOT a local mocked variable!)
    const releaseRes = await teacherContext.request.post(`${BACKEND_URL}/api/v1/exams/${examId}/release-results`);
    expect(releaseRes.status()).toBe(200);
    const releasedExam = await releaseRes.json();
    expect(releasedExam.isResultsReleased).toBe(true);

    // 2. Student API now unredacts scores and answer details
    const studentUnredactedRes = await student1Context.request.get(`${BACKEND_URL}/api/v1/attempts/${student1AttemptId}`);
    expect(studentUnredactedRes.status()).toBe(200);
    const unredactedData = await studentUnredactedRes.json();
    expect(unredactedData.marksObtained).toBe(10.0);
    expect(unredactedData.isResultsReleased).toBe(true);

    const q1Ans = unredactedData.answers.find((a: { questionId: string }) => a.questionId === q1Id);
    const q2Ans = unredactedData.answers.find((a: { questionId: string }) => a.questionId === q2Id);
    expect(q1Ans.marksAwarded).toBe(5.0);
    expect(q1Ans.isCorrect).toBe('FULLY_CORRECT');
    expect(q2Ans.marksAwarded).toBe(5.0);
    expect(q2Ans.feedback).toContain('Excellent explanation');

    // 3. Student UI: Reload /student/exams/[examId]/result and assert visible score & breakdown
    const studentPage = await student1Context.newPage();
    await studentPage.goto(`/student/exams/${examId}/result`);

    // Assert "Exam Results Released" headline
    await expect(studentPage.getByText(/exam results released/i).first()).toBeVisible({ timeout: 15000 });

    // Assert Score Obtained: 10 / 10
    await expect(studentPage.getByText(/10/i).filter({ hasText: /10/i }).first()).toBeVisible();
    await expect(studentPage.getByText(/100.0%/i).or(studentPage.getByText(/100%/i)).first()).toBeVisible();

    // Assert Answer Key & Explanations section
    await expect(studentPage.getByText(/answer key & explanations/i).first()).toBeVisible();

    await studentPage.close();
  });

  test('Step 6: Isolation & Cross-Student Security Assertions', async () => {
    // Authenticate Student 2 (same class, but different student)
    await loginViaApi(student2Context, USERS.student2.email);

    // 1. Student 2 CANNOT read Student 1's attempt (must return 403 or 404)
    const crossReadRes = await student2Context.request.get(`${BACKEND_URL}/api/v1/attempts/${student1AttemptId}`);
    expect([403, 404]).toContain(crossReadRes.status());

    // 2. Student 2 CANNOT mutate Student 1's attempt draft
    const crossDraftRes = await student2Context.request.put(`${BACKEND_URL}/api/v1/attempts/${student1AttemptId}/draft`, {
      data: {
        baseRevision: 1,
        clientSequence: 99,
        answers: [{ questionId: q1Id, textAnswer: 'Malicious modification' }],
      },
    });
    expect([400, 403]).toContain(crossDraftRes.status());

    // 3. Student 2 CANNOT submit Student 1's attempt
    const crossSubmitRes = await student2Context.request.post(`${BACKEND_URL}/api/v1/attempts/submit`, {
      data: {
        id: student1AttemptId,
        answers: [],
      },
    });
    expect([400, 403]).toContain(crossSubmitRes.status());
  });
});
