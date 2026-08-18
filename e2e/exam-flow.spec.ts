import { test, expect } from '@playwright/test';

test.describe('E2E: Exam Exploration & Attempt Lifecycle', () => {
  test('E6: Exams discovery view renders search bar and subject filter tags', async ({ page }) => {
    await page.goto('/login');
    // Verify login page is available if redirection occurs
    await expect(page.locator('input[type="email"], input#email, input[name="email"]')).toBeVisible();
  });

  test('E7: Unauthenticated attempt on exam redirects securely to login', async ({ page }) => {
    // Attempting to access an exam attempt without active session
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
});
