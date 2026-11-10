import { expect, test } from '@playwright/test';

test('advisor finds a sourced class through the real worker and MCP server', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Your next chapter starts here.' })).toBeVisible();
  await page.getByRole('button', { name: 'Try a photography class' }).click();
  await page.getByLabel('Budget, before funding').fill('50');
  await page.getByRole('button', { name: 'Send learning goal' }).click();
  await expect(page.locator('.message').last()).toContainText('CC-001');
  await expect(page.getByRole('link', { name: 'View official listing' }).first()).toHaveAttribute('href', /onepa.gov.sg/);
});

test('simulation saves replies and Helix scores them', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /02.*Run a simulation/ }).click();
  await page.getByRole('button', { name: 'Start simulation' }).click();
  await expect(page.getByText('1 of 1 episodes saved')).toBeVisible({ timeout: 30000 });
  await page.getByRole('button', { name: 'Inspect conversation' }).click();
  await expect(page.locator('.message').last()).toContainText('SF-005');
  await page.getByRole('button', { name: 'Evaluate saved replies' }).click();
  await expect(page.getByText('4 of 4 checks passed')).toBeVisible({ timeout: 30000 });
});

test('narrow screens remain usable and model-supplied HTML stays inert', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route('**/api/chat', route => route.fulfill({ json: {
    session_id: '00000000-0000-0000-0000-000000000000',
    content: '<img src=x onerror="window.injected=true"><script>window.injected=true</script>**Safe answer**', matches: []
  } }));
  await page.goto('/');
  await page.getByLabel('Your learning goal').fill('photography');
  await page.getByRole('button', { name: 'Send learning goal' }).click();
  await expect(page.getByText('Safe answer')).toBeVisible();
  expect(await page.evaluate(() => (window as typeof window & { injected?: boolean }).injected)).toBeUndefined();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
