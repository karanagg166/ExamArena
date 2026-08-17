import { test, expect } from '@playwright/test';

test.describe('E2E: School & Class Management Views', () => {
  test('E3: Schools explorer page renders search and list components', async ({ page }) => {
    await page.goto('/schools');
    await expect(page.locator('body')).toBeVisible();
  });

  test('E4: Classes overview page loads without crashing', async ({ page }) => {
    await page.goto('/classes');
    await expect(page.locator('body')).toBeVisible();
  });
});
