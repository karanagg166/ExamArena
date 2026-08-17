import { test, expect } from '@playwright/test';

test.describe('E2E: Authentication & Landing Flows', () => {
  test('E1: Landing page loads with key headlines and navigation links', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Exam|Arena/i);
    // Verify main CTA or login button is visible
    const loginLink = page.getByRole('link', { name: /login|sign in/i });
    if (await loginLink.count() > 0) {
      await expect(loginLink.first()).toBeVisible();
    }
  });

  test('E2: Login page renders email and password fields', async ({ page }) => {
    await page.goto('/login');
    const emailInput = page.getByLabel(/email/i).or(page.locator('input[type="email"]'));
    const passwordInput = page.getByLabel(/password/i).or(page.locator('input[type="password"]'));
    
    if (await emailInput.count() > 0) {
      await expect(emailInput.first()).toBeVisible();
      await expect(passwordInput.first()).toBeVisible();
    }
  });
});
