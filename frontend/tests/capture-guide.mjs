import { chromium, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
const output = resolve('../docs/user-guide-assets');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({
  channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge',
  headless: true,
});
const pages = [];
async function user(code) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1.5,
  });
  if (process.env.VERDANT_TEST_API_ORIGIN) {
    await context.route('http://localhost:8000/api/**', (route) =>
      route.continue({
        url: route
          .request()
          .url()
          .replace(
            'http://localhost:8000',
            process.env.VERDANT_TEST_API_ORIGIN,
          ),
      }),
    );
  }
  const page = await context.newPage();
  pages.push(page);
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  if (!code) return page;
  await page.getByLabel('Employee ID or username').fill(code);
  await page.getByLabel('Password', { exact: true }).fill('verdant-demo');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: /Welcome back/ }),
  ).toBeVisible();
  if (await page.getByRole('button', { name: 'Dismiss notification' }).count())
    await page.getByRole('button', { name: 'Dismiss notification' }).click();
  return page;
}
async function shot(page, name) {
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: resolve(output, name + '.png'),
    fullPage: false,
    animations: 'disabled',
  });
}
async function project(page, name = 'DEMO - Atlas EV platform') {
  await page.getByRole('button', { name: 'My projects', exact: false }).click();
  await page
    .getByRole('button', { name: new RegExp(name + '.*Open workspace') })
    .click();
}
async function pdfReady(page) {
  await page.locator('canvas').first().waitFor();
  await page.waitForFunction(() =>
    [...document.querySelectorAll('canvas')].every((c) => c.width > 0),
  );
  await page
    .locator('.reader-surface .sr-only')
    .first()
    .waitFor({ state: 'attached' });
  await expect
    .poll(() => page.locator('.reader-surface .sr-only').first().textContent())
    .not.toBe('');
}
try {
  const login = await user();
  await shot(login, 'login');
  const owner = await user('EMP-1042');
  await shot(owner, 'home');
  await owner
    .getByRole('button', { name: 'My projects', exact: false })
    .click();
  await shot(owner, 'my-projects');
  await owner
    .getByRole('button', { name: 'Create project', exact: true })
    .click();
  await shot(owner, 'create-project');
  await owner.getByRole('button', { name: 'Cancel', exact: true }).click();
  await project(owner);
  await owner.getByRole('tab', { name: 'People & stages' }).click();
  await shot(owner, 'people-stages');
  await owner
    .getByRole('button', { name: 'Required document', exact: true })
    .click();
  await owner
    .getByLabel('Document title', { exact: true })
    .fill('Technical drawing - mounting plate');
  await owner
    .getByLabel('Document type / part', { exact: true })
    .fill('Mounting plate drawing');
  await owner
    .getByLabel('Lifecycle stage', { exact: true })
    .selectOption({ label: 'Design' });
  await owner
    .getByLabel('Responsible employee', { exact: true })
    .selectOption({ label: 'Mira Nair' });
  await owner
    .getByLabel('Reviewer', { exact: true })
    .selectOption({ label: 'Vikram Shah' });
  await shot(owner, 'requirement-form');
  await owner.getByRole('button', { name: 'Cancel', exact: true }).click();
  await owner.getByRole('tab', { name: 'Documents', exact: true }).click();
  await owner
    .getByRole('button', { name: /Material selection report/ })
    .click();
  await pdfReady(owner);
  await shot(owner, 'project-workspace');
  await owner.getByRole('button', { name: 'Share', exact: true }).click();
  await owner
    .getByLabel('Employee or visitor', { exact: true })
    .selectOption({ label: 'Leela Thomas' });
  await shot(owner, 'share-dialog');
  await owner.getByRole('button', { name: 'Cancel', exact: true }).click();
  await owner.getByRole('tab', { name: /Research links/ }).click();
  await shot(owner, 'project-references');
  await owner.getByRole('tab', { name: 'Activity', exact: true }).click();
  await owner.locator('.activity-row').first().waitFor();
  await shot(owner, 'activity-log');
  await owner.getByLabel('Search all documents').fill('thermal');
  await expect(
    owner
      .getByRole('region', { name: 'Search results' })
      .getByRole('button')
      .first(),
  ).toBeVisible();
  await shot(owner, 'search');
  await owner
    .getByRole('button', { name: 'Clear search', exact: true })
    .click();

  const writer = await user('EMP-1071');
  await writer
    .getByRole('button', { name: 'My actions', exact: false })
    .click();
  await shot(writer, 'my-actions');
  await writer
    .getByRole('button', { name: /Battery enclosure drawing/ })
    .click();
  await pdfReady(writer);
  await writer
    .getByRole('button', { name: 'Compare versions side by side', exact: true })
    .click();
  await expect(writer.locator('canvas')).toHaveCount(2);
  await shot(writer, 'version-comparison');
  await writer
    .getByRole('button', { name: 'Close comparison', exact: true })
    .click();
  await writer
    .getByRole('button', { name: 'Upload new version', exact: true })
    .click();
  await writer
    .getByLabel('What changed?', { exact: true })
    .fill('Increased the illustrative flange clearance from 12 mm to 16 mm.');
  await shot(writer, 'upload-version');
  await writer.getByRole('button', { name: 'Cancel', exact: true }).click();
  await project(writer);
  await writer
    .getByRole('button', { name: 'Research library', exact: true })
    .click();
  await writer
    .getByRole('button', { name: /\[DEMO\] Aluminium alloy selection notes/ })
    .click();
  await pdfReady(writer);
  await shot(writer, 'research-library');
  await writer
    .getByRole('button', { name: 'Create classification', exact: true })
    .click();
  await shot(writer, 'category-form');
  await writer.getByRole('button', { name: 'Cancel', exact: true }).click();
  await writer
    .getByRole('button', { name: 'Upload document', exact: true })
    .click();
  await shot(writer, 'research-upload');
  await writer.getByRole('button', { name: 'Cancel', exact: true }).click();
  await writer
    .getByRole('button', { name: 'All research', exact: false })
    .click();
  await writer
    .getByRole('button', { name: /\[DEMO\] Supplier handover notes/ })
    .click();
  await expect(writer.locator('.office-preview')).toContainText(
    'Record the source',
  );
  await shot(writer, 'research-links');
  await writer
    .getByRole('button', { name: 'All research', exact: false })
    .click();
  await writer
    .getByRole('button', { name: /\[DEMO\] Material comparison workbook/ })
    .click();
  await expect(writer.locator('.office-preview table')).toBeVisible();
  await shot(writer, 'office-preview');

  const reviewer = await user('EMP-1088');
  await project(reviewer, 'DEMO - Nova lightweight seat');
  await reviewer
    .getByRole('button', { name: /Aluminium bracket drawing/ })
    .click();
  await pdfReady(reviewer);
  await shot(reviewer, 'review-document');
  await reviewer
    .getByRole('button', { name: 'Request changes', exact: true })
    .click();
  await reviewer
    .getByLabel('Feedback', { exact: true })
    .fill(
      'Please clarify the hole-pattern note and upload the corrected revision.',
    );
  await shot(reviewer, 'review-feedback');
  await reviewer.getByRole('button', { name: 'Cancel', exact: true }).click();

  const visitor = await user('VIS-1100');
  await visitor
    .getByRole('button', { name: 'Shared with me', exact: true })
    .click();
  await visitor
    .getByRole('button', { name: /Material selection report/ })
    .click();
  await pdfReady(visitor);
  await shot(visitor, 'visitor-inbox');
  console.log(
    'Captured 22 current-interface guide screenshots; no project data was modified.',
  );
} finally {
  await browser.close();
}
