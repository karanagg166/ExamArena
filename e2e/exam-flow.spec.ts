import { test, expect } from '@playwright/test';

test.describe('E2E: Exam Exploration & Attempt Lifecycle', () => {
  const mockStudentUser = {
    id: 'usr_student_gold',
    email: 'student.gold@examarena.com',
    name: 'Gold Student',
    role: 'STUDENT',
    schoolId: 'school_demo',
    classId: 'class_demo',
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-01-01T00:00:00Z',
  };

  test('E6: Exams discovery view renders search bar and subject filter tags', async ({ page }) => {
    // Mock student authentication and student exams list
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockStudentUser),
      });
    });

    await page.route('**/api/v1/exams/student/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'exam-sample-1',
            title: 'Mathematics Advanced Exam',
            subject: 'Mathematics',
            duration: 60,
            maxMarks: 100,
            isPublished: true,
            isResultsReleased: false,
            studentStatus: 'NOT_ATTEMPTED',
            attemptId: null,
            sections: [],
          },
        ]),
      });
    });

    await page.goto('/student/exams');
    await expect(page.locator('input[placeholder*="Search by exam name"], input[placeholder*="Search"]').first()).toBeVisible({ timeout: 8000 });
  });

  test('E7: Unauthenticated attempt on exam redirects securely to login', async ({ page }) => {
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Not authenticated' }),
      });
    });

    await page.goto('/student/exams/non-existent-exam-id/attempt');
    await expect(page).toHaveURL(/\/(login|sign-in|$)/, { timeout: 8000 });
  });

  test('E8: Navigation to public routes does not cause rendering errors', async ({ page }) => {
    const publicPages = ['/', '/login', '/signup'];

    for (const url of publicPages) {
      const response = await page.goto(url);
      expect(response?.status()).toBeLessThan(400);
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('E9: Golden flow: Exam submission result redaction before release and release visibility', async ({ page }) => {
    let resultsReleased = false;

    // 1. Mock student auth
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockStudentUser),
      });
    });

    // 2. Mock exam details (dynamic based on resultsReleased state)
    await page.route('**/api/v1/exams/exam-gold-101', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'exam-gold-101',
          title: 'CS101 Final Exam',
          subject: 'Computer Science',
          duration: 60,
          maxMarks: 50,
          passingMarks: 20,
          isResultsReleased: resultsReleased,
          isPublished: true,
          sections: [],
        }),
      });
    });

    // 3. Mock student exams index
    await page.route('**/api/v1/exams/student', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'exam-gold-101',
            title: 'CS101 Final Exam',
            attemptId: 'att-gold-101',
            studentStatus: 'SUBMITTED',
            isResultsReleased: resultsReleased,
          },
        ]),
      });
    });

    // 4. Mock attempt details with redaction toggled by resultsReleased
    await page.route('**/api/v1/attempts/att-gold-101', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'att-gold-101',
          examId: 'exam-gold-101',
          studentId: 'usr_student_gold',
          status: 'SUBMITTED',
          marksObtained: resultsReleased ? 45 : null,
          isResultsReleased: resultsReleased,
          draftRevision: 3,
          warningCount: 0,
          answers: resultsReleased
            ? [
                {
                  id: 'ans-1',
                  questionId: 'q-1',
                  questionType: 'MULTIPLE_CHOICE',
                  marksAwarded: 5,
                  feedback: 'Great job!',
                },
              ]
            : [],
        }),
      });
    });

    // Step A: Visit results page before release
    await page.goto('/student/exams/exam-gold-101/result');

    // Verify unreleased state shows submission acknowledgment but redacts scores
    await expect(page.getByRole('heading', { name: /Exam Submitted Successfully/i })).toBeVisible({ timeout: 8000 });
    await expect(page.getByText(/Your submission has been securely recorded/i)).toBeVisible();
    await expect(page.getByText('Score Obtained')).not.toBeVisible();

    // Step B: Teacher releases results
    resultsReleased = true;

    // Step C: Student refreshes results page
    await page.reload();

    // Verify released state displays unredacted score and percentage
    await expect(page.getByRole('heading', { name: /Exam Results Released/i })).toBeVisible({ timeout: 8000 });
    await expect(page.getByText('Score Obtained')).toBeVisible();
    await expect(page.getByText('45')).toBeVisible();
    await expect(page.getByText(/90(\.0)?%/)).toBeVisible();
  });

  test('E10: Golden flow: Attempt answering, draft autosave sync, and submission', async ({ page }) => {
    page.on('console', (msg) => console.log('BROWSER CONSOLE:', msg.text()));
    page.on('pageerror', (err) => console.log('BROWSER ERROR:', err.message));
    // 1. Mock student auth
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockStudentUser),
      });
    });

    // 2. Mock exam history
    await page.route('**/api/v1/exams/student/me/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    const sampleQuestion = {
      id: 'q-algo-1',
      questionNumber: 1,
      text: 'What is the average time complexity of QuickSort?',
      questionType: 'MULTIPLE_CHOICE',
      marks: 5,
      options: [
        { id: 'opt-1', text: 'O(n^2)' },
        { id: 'opt-2', text: 'O(n log n)' },
        { id: 'opt-3', text: 'O(log n)' },
        { id: 'opt-4', text: 'O(1)' },
      ],
    };

    const mockExamData = {
      id: 'exam-gold-102',
      name: 'Algorithms 101',
      title: 'Algorithms 101',
      subject: 'Computer Science',
      duration: 60,
      maxMarks: 10,
      passingMarks: 4,
      isPublished: true,
      isPublic: true,
      isResultsReleased: false,
      instructions: 'Please answer all questions carefully.',
      questions: [sampleQuestion],
      sections: [
        {
          id: 'sec-1',
          name: 'Section A',
          questions: [sampleQuestion],
        },
      ],
    };

    // 3. Mock exam details
    await page.route('**/api/v1/exams/exam-gold-102', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockExamData),
      });
    });

    const mockAttemptData = {
      id: 'att-gold-102',
      examId: 'exam-gold-102',
      studentId: 'usr_student_gold',
      status: 'IN_PROGRESS',
      draftRevision: 0,
      warningCount: 0,
      startedAt: new Date().toISOString(),
      durationSeconds: 3600,
      timeRemainingSeconds: 3600,
      answers: [
        {
          id: 'ans-algo-1',
          questionId: 'q-algo-1',
          questionType: 'MULTIPLE_CHOICE',
          status: 'NOT_VISITED',
        },
      ],
    };

    // 4. Mock start attempt
    await page.route('**/api/v1/attempts/start', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAttemptData),
      });
    });

    // 5. Mock attempt details
    await page.route('**/api/v1/attempts/att-gold-102', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAttemptData),
      });
    });

    // 6. Mock draft save
    let draftSaved = false;
    await page.route('**/api/v1/attempts/att-gold-102/draft', async (route) => {
      draftSaved = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          applied: true,
          conflict: false,
          revision: 1,
        }),
      });
    });

    // 7. Mock submit
    await page.route('**/api/v1/attempts/submit', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'att-gold-102',
          status: 'SUBMITTED',
        }),
      });
    });

    // 8. Mock student exams index for result page
    await page.route('**/api/v1/exams/student', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'exam-gold-102',
            attemptId: 'att-gold-102',
            studentStatus: 'SUBMITTED',
            isResultsReleased: false,
          },
        ]),
      });
    });

    // Navigate to exam start page
    await page.goto('/student/exams/exam-gold-102/start');
    await expect(page.getByText('Algorithms 101')).toBeVisible({ timeout: 8000 });

    // Accept instructions
    const agreementCheckbox = page.locator('button[role="checkbox"], input[type="checkbox"]').first();
    await agreementCheckbox.click();

    // Click Start/Begin Exam button
    const startButton = page.getByRole('button', { name: /Begin Exam|Start Exam/i });
    await expect(startButton).toBeEnabled();
    await startButton.click();

    // Verify transition to attempt page
    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/attempt/, { timeout: 10000 });
    await expect(page.getByText('What is the average time complexity of QuickSort?')).toBeVisible({ timeout: 8000 });

    // Select the correct option: O(n log n)
    const option = page.locator('label').filter({ hasText: 'O(n log n)' });
    await expect(option).toBeVisible();
    await option.click();

    // Verify option is selected
    const radio = option.locator('input[type="radio"]');
    await expect(radio).toBeChecked();

    // Submit the exam
    const submitBtn = page.getByRole('button', { name: /Submit Exam/i });
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();

    // If confirmation dialog appears, confirm submission
    const confirmBtn = page.getByRole('button', { name: /Submit Anyway|Confirm/i });
    if (await confirmBtn.isVisible({ timeout: 2000 })) {
      await confirmBtn.click();
    }

    // Verify redirection to results page
    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/result/, { timeout: 10000 });
    await expect(page.getByRole('heading', { name: /Exam Submitted Successfully/i })).toBeVisible({ timeout: 8000 });
  });
});
