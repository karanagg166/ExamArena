import { test, expect } from '@playwright/test';

test.describe('E2E: School & Class Management Views', () => {
  test('E9: Direct navigation to school views requires authentication', async ({ page }) => {
    await page.goto('/principal');
    await expect(page).toHaveURL(/\/(login|sign-in|$)/, { timeout: 8000 });
  });

  test('E10: Teacher dashboard route is protected from unauthenticated access', async ({ page }) => {
    await page.goto('/teacher');
    await expect(page).toHaveURL(/\/(login|sign-in|$)/, { timeout: 8000 });
  });
});
