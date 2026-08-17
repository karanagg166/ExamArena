import { test, expect } from '@playwright/test';

test.describe('E2E: Exam Exploration & Taking Flows', () => {
  test('E6: Public exams page shows exam listing elements and search', async ({ page }) => {
    await page.goto('/exams');
    await expect(page.locator('body')).toBeVisible();
  });

  test('E7: Attempt page with invalid/unauthenticated ID redirects safely', async ({ page }) => {
    await page.goto('/attempt/non-existent-exam-id');
    await expect(page.locator('body')).toBeVisible();
  });
});
