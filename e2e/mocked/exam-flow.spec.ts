import { test, expect, Request } from '@playwright/test';

test.describe('Mocked UI: Exam Exploration & Attempt Lifecycle', () => {
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

  async function setupMockAttemptEnvironment(page: any, customAttemptData = mockAttemptData) {
    await page.route('**/api/v1/auth/me', async (route: any) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockStudentUser),
      });
    });

    await page.route('**/api/v1/exams/student/me/history', async (route: any) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route('**/api/v1/exams/exam-gold-102', async (route: any) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockExamData),
      });
    });

    await page.route('**/api/v1/attempts/start', async (route: any) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(customAttemptData),
      });
    });

    await page.route('**/api/v1/attempts/att-gold-102', async (route: any) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(customAttemptData),
      });
    });

    await page.route('**/api/v1/exams/student', async (route: any) => {
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
  }

  test('E6: Exams discovery view renders search bar and subject filter tags', async ({ page }) => {
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

  test('E9: Mocked UI: Exam submission result redaction preview before release and release visibility', async ({ page }) => {
    let resultsReleased = false;

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockStudentUser),
      });
    });

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

    await page.goto('/student/exams/exam-gold-101/result');
    await expect(page.getByRole('heading', { name: /Exam Submitted Successfully/i })).toBeVisible({ timeout: 8000 });
    await expect(page.getByText(/Your submission has been securely recorded/i)).toBeVisible();
    await expect(page.getByText('Score Obtained')).not.toBeVisible();

    resultsReleased = true;
    await page.reload();

    await expect(page.getByRole('heading', { name: /Exam Results Released/i })).toBeVisible({ timeout: 8000 });
    await expect(page.getByText('Score Obtained')).toBeVisible();
    await expect(page.getByText('45')).toBeVisible();
    await expect(page.getByText(/90(\.0)?%/)).toBeVisible();
  });

  test('E10: Golden flow: Attempt answering, strict draft autosave inspection, and submission', async ({ page }) => {
    await setupMockAttemptEnvironment(page);

    let capturedDraftRequest: Request | null = null;
    let capturedDraftBody: any = null;

    await page.route('**/api/v1/attempts/att-gold-102/draft', async (route) => {
      capturedDraftRequest = route.request();
      capturedDraftBody = capturedDraftRequest.postDataJSON();

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          attemptId: 'att-gold-102',
          savedCount: 1,
          clientSequence: capturedDraftBody?.clientSequence || 1,
          revision: (capturedDraftBody?.baseRevision || 0) + 1,
          applied: true,
          conflict: false,
          savedAt: new Date().toISOString(),
          timeRemainingSeconds: 3500,
        }),
      });
    });

    let capturedSubmitBody: any = null;
    await page.route('**/api/v1/attempts/submit', async (route) => {
      capturedSubmitBody = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'att-gold-102',
          status: 'SUBMITTED',
        }),
      });
    });

    await page.goto('/student/exams/exam-gold-102/start');
    await expect(page.getByText('Algorithms 101')).toBeVisible({ timeout: 8000 });

    const agreementCheckbox = page.locator('button[role="checkbox"], input[type="checkbox"]').first();
    await agreementCheckbox.click();

    const startButton = page.getByRole('button', { name: /Begin Exam|Start Exam/i });
    await expect(startButton).toBeEnabled();
    await startButton.click();

    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/attempt/, { timeout: 10000 });
    await expect(page.getByText('What is the average time complexity of QuickSort?')).toBeVisible({ timeout: 8000 });

    const draftPromise = page.waitForRequest(req => 
      req.url().includes('/api/v1/attempts/att-gold-102/draft') && req.method() === 'PUT'
    );

    const option = page.locator('label').filter({ hasText: 'O(n log n)' });
    await expect(option).toBeVisible();
    await option.click();

    const draftReq = await draftPromise;
    expect(draftReq.url()).toContain('/api/v1/attempts/att-gold-102/draft');

    const draftBody = draftReq.postDataJSON();
    expect(draftBody).not.toBeNull();
    expect(draftBody.baseRevision).toBe(0);
    expect(draftBody.clientSequence).toBeGreaterThan(0);
    expect(draftBody.answers).toHaveLength(1);
    expect(draftBody.answers[0].questionId).toBe('q-algo-1');
    expect(draftBody.answers[0].selectedOptions).toEqual([{ optionId: 'opt-2' }]);
    expect(draftBody.answers[0].marksAwarded).toBeUndefined();
    expect(draftBody.answers[0].isCorrect).toBeUndefined();
    expect(draftBody.answers[0].feedback).toBeUndefined();

    await expect(page.getByText('Draft saved')).toBeVisible({ timeout: 5000 });

    const submitBtn = page.getByRole('button', { name: /Submit Exam/i });
    await expect(submitBtn).toBeVisible();
    await submitBtn.click();

    const confirmBtn = page.getByRole('button', { name: /Submit Anyway|Confirm/i });
    if (await confirmBtn.isVisible().catch(() => false)) {
      await confirmBtn.click();
    }

    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/result/, { timeout: 10000 });
    expect(capturedSubmitBody).not.toBeNull();
    expect(capturedSubmitBody.id).toBe('att-gold-102');
    expect(capturedSubmitBody.answers[0].selectedOptions).toEqual([{ optionId: 'opt-2' }]);
  });

  test('E10.1: Intentional answer clearing sends empty option selection and confirms persistence', async ({ page }) => {
    await setupMockAttemptEnvironment(page);

    let revisionTracker = 0;
    const capturedDrafts: any[] = [];

    await page.route('**/api/v1/attempts/att-gold-102/draft', async (route) => {
      const data = route.request().postDataJSON();
      capturedDrafts.push(data);
      revisionTracker += 1;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          attemptId: 'att-gold-102',
          savedCount: 1,
          clientSequence: data.clientSequence,
          revision: revisionTracker,
          applied: true,
          conflict: false,
          savedAt: new Date().toISOString(),
          timeRemainingSeconds: 3500,
        }),
      });
    });

    await page.goto('/student/exams/exam-gold-102/start');
    await page.locator('button[role="checkbox"], input[type="checkbox"]').first().click();
    await page.getByRole('button', { name: /Begin Exam|Start Exam/i }).click();

    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/attempt/, { timeout: 10000 });

    const firstSavePromise = page.waitForRequest(req => req.url().includes('/draft') && req.method() === 'PUT');
    await page.locator('label').filter({ hasText: 'O(n log n)' }).click();
    await firstSavePromise;
    await expect(page.getByText('Draft saved')).toBeVisible({ timeout: 5000 });

    const clearSavePromise = page.waitForRequest(req => req.url().includes('/draft') && req.method() === 'PUT');
    const clearButton = page.getByRole('button', { name: /Clear Response/i });
    await expect(clearButton).toBeVisible();
    await clearButton.click();

    await clearSavePromise;
    await expect(page.getByText('Draft saved')).toBeVisible({ timeout: 5000 });

    expect(capturedDrafts.length).toBeGreaterThanOrEqual(2);
    const lastDraft = capturedDrafts[capturedDrafts.length - 1];
    expect(lastDraft.baseRevision).toBe(1);
    expect(lastDraft.answers[0].selectedOptions).toEqual([]);
    expect(lastDraft.answers[0].textAnswer).toBe('');
  });

  test('E10.2: Edits occurring while older save is in flight queue and trigger fresh save', async ({ page }) => {
    await setupMockAttemptEnvironment(page);

    let resolveFirstSave!: () => void;
    const firstSaveDeferred = new Promise<void>((resolve) => {
      resolveFirstSave = resolve;
    });

    let draftCount = 0;
    const capturedDrafts: any[] = [];

    await page.route('**/api/v1/attempts/att-gold-102/draft', async (route) => {
      draftCount += 1;
      const data = route.request().postDataJSON();
      capturedDrafts.push(data);

      if (draftCount === 1) {
        await firstSaveDeferred;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            attemptId: 'att-gold-102',
            savedCount: 1,
            clientSequence: data.clientSequence,
            revision: 1,
            applied: true,
            conflict: false,
            savedAt: new Date().toISOString(),
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            attemptId: 'att-gold-102',
            savedCount: 1,
            clientSequence: data.clientSequence,
            revision: 2,
            applied: true,
            conflict: false,
            savedAt: new Date().toISOString(),
          }),
        });
      }
    });

    await page.goto('/student/exams/exam-gold-102/start');
    await page.locator('button[role="checkbox"], input[type="checkbox"]').first().click();
    await page.getByRole('button', { name: /Begin Exam|Start Exam/i }).click();

    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/attempt/, { timeout: 10000 });

    const firstReqPromise = page.waitForRequest(req => req.url().includes('/draft') && req.method() === 'PUT');
    await page.locator('label').filter({ hasText: 'O(n^2)' }).click();
    await firstReqPromise;

    await expect(page.getByText('Saving draft...')).toBeVisible({ timeout: 5000 });

    await page.locator('label').filter({ hasText: 'O(n log n)' }).click();

    const secondReqPromise = page.waitForRequest(req => req.url().includes('/draft') && req.method() === 'PUT');
    resolveFirstSave();

    await secondReqPromise;
    await expect(page.getByText('Draft saved')).toBeVisible({ timeout: 5000 });

    expect(capturedDrafts.length).toBeGreaterThanOrEqual(2);
    expect(capturedDrafts[0].answers[0].selectedOptions).toEqual([{ optionId: 'opt-1' }]);
    expect(capturedDrafts[1].answers[0].selectedOptions).toEqual([{ optionId: 'opt-2' }]);
    expect(capturedDrafts[1].baseRevision).toBe(1);
  });

  test('E10.3: Initial draft save failure triggers automatic retry without additional keystroke', async ({ page }) => {
    await setupMockAttemptEnvironment(page);

    let attempts = 0;
    await page.route('**/api/v1/attempts/att-gold-102/draft', async (route) => {
      attempts += 1;
      if (attempts === 1) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Transient database error' }),
        });
      } else {
        const data = route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            attemptId: 'att-gold-102',
            savedCount: 1,
            clientSequence: data.clientSequence,
            revision: 1,
            applied: true,
            conflict: false,
            savedAt: new Date().toISOString(),
          }),
        });
      }
    });

    await page.goto('/student/exams/exam-gold-102/start');
    await page.locator('button[role="checkbox"], input[type="checkbox"]').first().click();
    await page.getByRole('button', { name: /Begin Exam|Start Exam/i }).click();

    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/attempt/, { timeout: 10000 });

    const retryPromise = page.waitForRequest(req => req.url().includes('/draft') && req.method() === 'PUT');
    await page.locator('label').filter({ hasText: 'O(n log n)' }).click();

    await retryPromise;
    await expect(page.getByText('Save failed')).toBeVisible({ timeout: 5000 });

    await expect(page.getByText('Draft saved')).toBeVisible({ timeout: 8000 });
    expect(attempts).toBeGreaterThanOrEqual(2);
  });

  test('E10.4: Reconnect after offline state triggers automatic draft sync', async ({ page }) => {
    await setupMockAttemptEnvironment(page);

    let synced = false;
    await page.route('**/api/v1/attempts/att-gold-102/draft', async (route) => {
      synced = true;
      const data = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          attemptId: 'att-gold-102',
          savedCount: 1,
          clientSequence: data.clientSequence,
          revision: 1,
          applied: true,
          conflict: false,
          savedAt: new Date().toISOString(),
        }),
      });
    });

    await page.goto('/student/exams/exam-gold-102/start');
    await page.locator('button[role="checkbox"], input[type="checkbox"]').first().click();
    await page.getByRole('button', { name: /Begin Exam|Start Exam/i }).click();

    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/attempt/, { timeout: 10000 });

    await page.evaluate(() => window.dispatchEvent(new Event('offline')));
    await expect(page.getByText('Offline (will sync)')).toBeVisible({ timeout: 5000 });

    await page.locator('label').filter({ hasText: 'O(n log n)' }).click();

    const syncPromise = page.waitForRequest(req => req.url().includes('/draft') && req.method() === 'PUT');
    await page.evaluate(() => window.dispatchEvent(new Event('online')));

    await syncPromise;
    await expect(page.getByText('Draft saved')).toBeVisible({ timeout: 5000 });
    expect(synced).toBe(true);
  });

  test('E10.5: Revision conflict correctly displays conflict state and warning', async ({ page }) => {
    await setupMockAttemptEnvironment(page);

    await page.route('**/api/v1/attempts/att-gold-102/draft', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          attemptId: 'att-gold-102',
          savedCount: 0,
          clientSequence: 1,
          revision: 5,
          applied: false,
          conflict: true,
          savedAt: new Date().toISOString(),
        }),
      });
    });

    await page.goto('/student/exams/exam-gold-102/start');
    await page.locator('button[role="checkbox"], input[type="checkbox"]').first().click();
    await page.getByRole('button', { name: /Begin Exam|Start Exam/i }).click();

    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/attempt/, { timeout: 10000 });

    const draftPromise = page.waitForRequest(req => req.url().includes('/draft') && req.method() === 'PUT');
    await page.locator('label').filter({ hasText: 'O(n log n)' }).click();
    await draftPromise;
    await expect(page.getByText(/Conflict|Draft conflict/i).first()).toBeVisible({ timeout: 6000 });
  });

  test('E10.6: Refresh and resume restores persisted revision and populated answers', async ({ page }) => {
    let currentAttemptData: any = {
      ...mockAttemptData,
      draftRevision: 0,
      answers: [
        {
          id: 'ans-algo-1',
          questionId: 'q-algo-1',
          questionType: 'MULTIPLE_CHOICE',
          status: 'NOT_VISITED',
        },
      ],
    };

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockStudentUser),
      });
    });

    await page.route('**/api/v1/exams/student/me/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route('**/api/v1/exams/exam-gold-102', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockExamData),
      });
    });

    await page.route('**/api/v1/attempts/start', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(currentAttemptData),
      });
    });

    await page.route('**/api/v1/attempts/att-gold-102', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(currentAttemptData),
      });
    });

    let nextDraftBaseRevision = -1;
    await page.route('**/api/v1/attempts/att-gold-102/draft', async (route) => {
      const data = route.request().postDataJSON();
      nextDraftBaseRevision = data.baseRevision;
      currentAttemptData = {
        ...currentAttemptData,
        draftRevision: (data.baseRevision || 0) + 1,
        answers: [
          {
            id: 'ans-algo-1',
            questionId: 'q-algo-1',
            questionType: 'MULTIPLE_CHOICE',
            status: 'ANSWERED',
            selectedOptions: data.answers[0]?.selectedOptions || [],
          },
        ],
      };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          attemptId: 'att-gold-102',
          savedCount: 1,
          clientSequence: data.clientSequence,
          revision: currentAttemptData.draftRevision,
          applied: true,
          conflict: false,
          savedAt: new Date().toISOString(),
        }),
      });
    });

    await page.goto('/student/exams/exam-gold-102/start');
    await page.locator('button[role="checkbox"], input[type="checkbox"]').first().click();
    await page.getByRole('button', { name: /Begin Exam|Start Exam/i }).click();

    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/attempt/, { timeout: 10000 });

    const firstSave = page.waitForRequest(req => req.url().includes('/draft') && req.method() === 'PUT');
    await page.locator('label').filter({ hasText: 'O(n log n)' }).click();
    await firstSave;
    await expect(page.getByText('Draft saved')).toBeVisible({ timeout: 5000 });

    await page.reload();

    await expect(page.getByText('What is the average time complexity of QuickSort?')).toBeVisible({ timeout: 8000 });
    const radio = page.locator('label').filter({ hasText: 'O(n log n)' }).locator('input[type="radio"]');
    await expect(radio).toBeChecked();

    const secondSave = page.waitForRequest(req => req.url().includes('/draft') && req.method() === 'PUT');
    await page.locator('label').filter({ hasText: 'O(log n)' }).click();
    await secondSave;

    await expect(page.getByText('Draft saved')).toBeVisible({ timeout: 5000 });
    expect(nextDraftBaseRevision).toBe(1);
  });

  test('E10.7: Failed exam submission shows visible retry behavior without losing student input', async ({ page }) => {
    await setupMockAttemptEnvironment(page);

    await page.route('**/api/v1/attempts/att-gold-102/draft', async (route) => {
      const data = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          attemptId: 'att-gold-102',
          savedCount: 1,
          clientSequence: data.clientSequence,
          revision: 1,
          applied: true,
          conflict: false,
          savedAt: new Date().toISOString(),
        }),
      });
    });

    let submitAttempts = 0;
    await page.route('**/api/v1/attempts/submit', async (route) => {
      submitAttempts += 1;
      if (submitAttempts === 1) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Submission gateway timeout' }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'att-gold-102',
            status: 'SUBMITTED',
          }),
        });
      }
    });

    await page.goto('/student/exams/exam-gold-102/start');
    await page.locator('button[role="checkbox"], input[type="checkbox"]').first().click();
    await page.getByRole('button', { name: /Begin Exam|Start Exam/i }).click();

    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/attempt/, { timeout: 10000 });
    await page.locator('label').filter({ hasText: 'O(n log n)' }).click();
    await expect(page.getByText('Draft saved')).toBeVisible({ timeout: 5000 });

    const submitBtn = page.getByRole('button', { name: /Submit Exam/i });
    await submitBtn.click();

    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/attempt/);
    await expect(submitBtn).toBeEnabled();

    // Dismiss error toast overlay so it does not intercept pointer clicks
    await page.evaluate(() => document.querySelectorAll('[data-sonner-toast]').forEach((el) => el.remove()));

    await submitBtn.click();

    await expect(page).toHaveURL(/\/student\/exams\/exam-gold-102\/result/, { timeout: 10000 });
    expect(submitAttempts).toBe(2);
  });
});
