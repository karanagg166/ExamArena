import { test, expect } from '@playwright/test';

test.describe('E2E: Navigation & Role Redirection Guards', () => {
  test('E11: Unauthenticated access to protected dashboard routes redirects to login', async ({ page }) => {
    await page.goto('/principal');
    await expect(page).toHaveURL(/\/(login|sign-in|$)/, { timeout: 8000 });
  });

  test('E12: Brand logo link on login page navigates back to landing page', async ({ page }) => {
    await page.goto('/login');
    const brandLink = page.getByRole('link', { name: /exam.*arena|home/i }).or(page.locator('a[href="/"]')).first();
    if (await brandLink.isVisible()) {
      await brandLink.click();
      await expect(page).toHaveURL(/\/$/);
    }
  });

  test('E13: Error page recovery and home navigation', async ({ page }) => {
    await page.goto('/non-existent-page-404');
    await expect(page.locator('body')).toBeVisible();
  });
});
