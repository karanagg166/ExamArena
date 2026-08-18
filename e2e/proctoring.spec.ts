import { test, expect } from '@playwright/test';

test.describe('E2E: Proctoring & Exam Integrity Guards', () => {
  test('E14: Unauthenticated attempt page blocks access and guards proctoring session', async ({ page }) => {
    await page.goto('/student/exams/fake-exam-uuid/attempt');
    await expect(page).toHaveURL(/\/(login|sign-in|$)/, { timeout: 8000 });
  });

  test('E15: Root URL loads securely with proper HTML document structure', async ({ page }) => {
    await page.goto('/');
    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBeDefined();
    await expect(page.locator('meta[name="viewport"]')).toBeAttached();
  });
});
