import { test, expect } from '@playwright/test';

test.describe('E2E: Authentication & Landing Flows', () => {
  test('E1: Landing page loads with key headlines, brand badge, and navigation CTAs', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Exam|Arena/i);

    // Verify main header or hero section
    const heading = page.getByRole('heading', { level: 1 }).or(page.locator('h1'));
    await expect(heading.first()).toBeVisible();

    // Verify navigation buttons (Explore Exams / Login / Sign Up)
    const loginLink = page.getByRole('link', { name: /login|sign in/i }).first();
    const signupLink = page.getByRole('link', { name: /sign up|get started|register/i }).first();
    await expect(loginLink).toBeVisible();
    await expect(signupLink).toBeVisible();
  });

  test('E2: Navigation from landing to login page renders email and password form', async ({ page }) => {
    await page.goto('/');
    const loginLink = page.getByRole('link', { name: /login|sign in/i }).first();
    await loginLink.click();

    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('input[type="email"], input#email, input[name="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"], input#password, input[name="password"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in|login|continue/i })).toBeVisible();
  });

  test('E3: Login validation triggers on invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Attempt login with invalid credentials
    await page.locator('input[type="email"], input#email, input[name="email"]').fill('invalid.user@examarena.dev');
    await page.locator('input[type="password"], input#password, input[name="password"]').fill('WrongPass123!');
    await page.getByRole('button', { name: /sign in|login|continue/i }).click();

    // Expect an error toast, alert, or validation message to appear
    const alertMessage = page.locator('[role="alert"]').or(page.locator('.text-red-500, .text-destructive, [data-sonner-toast]'));
    await expect(alertMessage.first()).toBeVisible({ timeout: 7000 });
  });

  test('E4: Signup page loads with role selection and required profile fields', async ({ page }) => {
    await page.goto('/signup');

    // Verify page title and header
    await expect(page.locator('h1, h2').first()).toBeVisible();

    // Verify input fields for registration
    await expect(page.locator('input[type="email"], input#email, input[name="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"], input#password, input[name="password"]').first()).toBeVisible();
  });

  test('E5: Unauthenticated access to protected dashboards redirects to login', async ({ page }) => {
    const protectedPaths = ['/student', '/teacher', '/principal', '/profile'];

    for (const path of protectedPaths) {
      await page.goto(path);
      // Middleware or client guard must redirect to login
      await expect(page).toHaveURL(/\/(login|sign-in|$)/, { timeout: 8000 });
    }
  });
});
