import { chromium, expect } from '@playwright/test';

const origin = process.env.VERDANT_TEST_API_ORIGIN;
if (!origin || origin === 'http://localhost:8000')
  throw new Error(
    'Use the disposable backend supplied by the Python test runner.',
  );
const browser = await chromium.launch({
  channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge',
  headless: true,
});
const errors = [];
async function account(code) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
  });
  await context.route('http://localhost:8000/api/**', (route) =>
    route.continue({
      url: route.request().url().replace('http://localhost:8000', origin),
    }),
  );
  const page = await context.newPage();
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  await page.getByLabel('Employee ID or username').fill(code);
  await page.getByLabel('Password', { exact: true }).fill('verdant-demo');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: /Welcome back/ }),
  ).toBeVisible();
  expect(page.url()).not.toContain('?');
  expect(
    await page.evaluate(() => localStorage.getItem('verdant_token')),
  ).toBeNull();
  expect(await page.evaluate(() => document.cookie)).not.toContain(
    'verdant_session',
  );
  return page;
}
async function save(page, name = 'Save') {
  await page
    .getByRole('dialog')
    .getByRole('button', { name, exact: true })
    .click();
  await expect(page.getByRole('dialog')).not.toBeVisible();
}
async function openTask(page) {
  await page.getByRole('button', { name: 'My actions', exact: false }).click();
  await page.getByRole('button', { name: /Workflow test drawing/ }).click();
}
async function choose(page, label, name) {
  await page
    .getByRole('dialog')
    .getByLabel(label, { exact: true })
    .selectOption({ label: name });
}
async function file(page, content) {
  await page
    .getByRole('dialog')
    .getByLabel('File', { exact: true })
    .setInputFiles({
      name: 'workflow.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from(content),
    });
}
try {
  const owner = await account('EMP-1042');
  await owner
    .getByRole('button', { name: 'Create project', exact: true })
    .click();
  await owner
    .getByLabel('Project name', { exact: true })
    .fill('Browser workflow project');
  await save(owner, 'Create project');
  await owner.getByRole('tab', { name: 'People & stages' }).click();
  await owner.getByRole('button', { name: 'Add stage', exact: true }).click();
  await owner.getByLabel('Stage name', { exact: true }).fill('Design');
  await save(owner);
  for (const employee of ['Mira Nair', 'Vikram Shah']) {
    await owner
      .getByRole('button', { name: 'Add member', exact: true })
      .click();
    await choose(owner, 'Employee', employee);
    await save(owner);
  }
  await owner
    .getByRole('button', { name: 'Required document', exact: true })
    .click();
  await owner
    .getByLabel('Document title', { exact: true })
    .fill('Workflow test drawing');
  await owner
    .getByLabel('Document type / part', { exact: true })
    .fill('Technical drawing');
  await choose(owner, 'Lifecycle stage', 'Design');
  await choose(owner, 'Responsible employee', 'Mira Nair');
  await choose(owner, 'Reviewer', 'Vikram Shah');
  await save(owner);
  await owner.getByRole('tab', { name: 'Documents', exact: true }).click();
  await owner.getByRole('button', { name: /Workflow test drawing/ }).click();
  await expect(
    owner.getByRole('button', { name: 'Upload document', exact: true }),
  ).toHaveCount(0);

  const writer = await account('EMP-1071');
  await openTask(writer);
  await writer
    .getByRole('button', { name: 'Upload document', exact: true })
    .click();
  await file(writer, 'First revision — diameter 20 mm');
  await save(writer, 'Upload');
  await expect(writer.locator('.office-preview')).toContainText(
    'diameter 20 mm',
  );
  await writer
    .getByRole('button', { name: 'Submit for review', exact: true })
    .click();
  await expect(writer.locator('.document-detail .status')).toHaveText(
    'submitted',
  );
  const reviewer = await account('EMP-1088');
  await openTask(reviewer);
  await reviewer
    .getByRole('button', { name: 'Start review', exact: true })
    .click();
  await expect(
    reviewer.getByRole('button', { name: 'Request changes', exact: true }),
  ).toBeVisible();
  await reviewer
    .getByRole('button', { name: 'Request changes', exact: true })
    .click();
  await reviewer
    .getByLabel('Feedback', { exact: true })
    .fill('Please change the diameter to 25 mm.');
  await save(reviewer, 'Send feedback');
  await writer.reload({ waitUntil: 'networkidle' });
  await openTask(writer);
  await expect(writer.locator('.feedback')).toContainText('25 mm');
  await writer
    .getByRole('button', { name: 'Upload new version', exact: true })
    .click();
  await file(writer, 'Second revision — diameter 25 mm');
  await writer
    .getByLabel('What changed?', { exact: true })
    .fill('Corrected diameter from 20 mm to 25 mm.');
  await save(writer, 'Upload');
  await writer
    .getByRole('button', { name: 'Submit for review', exact: true })
    .click();
  await expect(writer.locator('.document-detail .status')).toHaveText(
    'submitted',
  );
  await reviewer.reload({ waitUntil: 'networkidle' });
  await openTask(reviewer);
  await reviewer
    .getByRole('button', { name: 'Compare versions side by side', exact: true })
    .click();
  await expect(reviewer.locator('.office-preview')).toHaveCount(2);
  await expect(reviewer.locator('.reader-comparison')).toContainText(
    'diameter 20 mm',
  );
  await expect(reviewer.locator('.reader-comparison')).toContainText(
    'diameter 25 mm',
  );
  await reviewer
    .getByRole('button', { name: 'Start review', exact: true })
    .click();
  await reviewer.getByRole('button', { name: 'Approve', exact: true }).click();
  await reviewer
    .getByLabel('Review notes', { exact: true })
    .fill('Dimensions confirmed.');
  await save(reviewer, 'Approve version');
  await expect(reviewer.locator('.document-detail .status')).toHaveText(
    'approved',
  );
  await reviewer
    .getByLabel('Document version', { exact: true })
    .selectOption({ label: 'Version 1' });
  await expect(reviewer.locator('.feedback').first()).toContainText(
    'Please change the diameter',
  );

  await owner
    .getByRole('button', { name: 'Research library', exact: true })
    .click();
  await owner
    .getByRole('button', { name: 'Create classification', exact: true })
    .click();
  await owner.getByLabel('Name', { exact: true }).fill('Browser research');
  await save(owner);
  for (const name of ['Browser study one', 'Browser study two']) {
    await owner
      .getByRole('button', { name: 'Upload document', exact: true })
      .click();
    await owner.getByLabel('Document title', { exact: true }).fill(name);
    await choose(owner, 'Classification', 'Browser research');
    await file(owner, name + ' content');
    await save(owner, 'Upload document');
    await expect(owner.locator('.office-preview')).toContainText(
      name + ' content',
    );
  }
  await owner
    .getByRole('button', { name: '+ Add reference', exact: true })
    .click();
  await choose(owner, 'Research document', 'Browser study one');
  await save(owner);
  await owner
    .getByRole('button', { name: '+ Link project', exact: true })
    .click();
  await choose(owner, 'Project', 'Browser workflow project');
  await save(owner);
  await owner
    .locator('.link-chip')
    .getByRole('button', { name: 'Browser workflow project', exact: true })
    .click();
  await owner.getByRole('tab', { name: /Research links/ }).click();
  await expect(owner.locator('.reference-row')).toContainText(
    'Browser study two',
  );
  await owner
    .getByRole('button', { name: 'Browser study two', exact: true })
    .click();
  await expect(owner.locator('.office-preview')).toContainText(
    'Browser study two content',
  );
  await owner
    .locator('.link-chip')
    .getByRole('button', { name: 'Browser study one', exact: true })
    .click();
  await expect(owner.locator('.office-preview')).toContainText(
    'Browser study one content',
  );
  await owner.getByLabel('Search all documents').fill('Browser study two');
  await owner
    .getByRole('region', { name: 'Search results' })
    .getByRole('button', { name: /Browser study two/ })
    .click();
  await expect(owner.locator('.office-preview')).toContainText(
    'Browser study two content',
  );

  // A real PDF renders to canvas, including at mobile width, with no external tab/download.
  await owner
    .getByRole('button', { name: /High-strength steel comparison/ })
    .count()
    .then(async (count) => {
      if (!count)
        await owner
          .getByRole('button', { name: 'All research', exact: false })
          .click();
    });
  await owner
    .getByRole('button', { name: /High-strength steel comparison/ })
    .click();
  await expect(owner.locator('canvas')).toBeVisible();
  await owner.waitForFunction(
    () => document.querySelector('canvas')?.width > 0,
  );
  await owner.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() =>
      owner
        .locator('canvas')
        .evaluate((element) => element.getBoundingClientRect().width),
    )
    .toBeLessThan(310);
  await expect(owner.locator('.reader-toolbar')).toContainText('Page 1 of 1');
  expect(errors).toEqual([]);
  console.log(
    'PASS: login privacy; personal home; project setup; assigned upload; feedback; resubmission; approval; version comparison; research navigation; bidirectional links; search; mobile PDF.',
  );
} finally {
  await browser.close();
}
