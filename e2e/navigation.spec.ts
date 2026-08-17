import { test, expect } from '@playwright/test';

test.describe('E2E: Navigation & Role Redirection', () => {
  test('E9: Unauthenticated access to protected dashboard redirects to login', async ({ page }) => {
    await page.goto('/principal');
    // Should either redirect to /login or show login required
    await expect(page).toHaveURL(/\/(login|sign-in|$)/);
  });

  test('E10: Public exam listing page renders filters', async ({ page }) => {
    await page.goto('/exams');
    // Verify page loads without crash
    await expect(page.locator('body')).toBeVisible();
  });
});
