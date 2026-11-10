// @vitest-environment jsdom
import { expect, test } from 'vitest';
import { renderMarkdown } from './markdown';

test('formats useful markdown and keeps official links', () => {
  const result = renderMarkdown('**Course** [details](https://www.onepa.gov.sg/courses)');
  expect(result).toContain('<strong>Course</strong>');
  expect(result).toContain('href="https://www.onepa.gov.sg/courses"');
});

test('does not execute supplied HTML, load images or retain javascript links', () => {
  const result = renderMarkdown('<img src="https://example.org/x" onerror="alert(1)"><script>alert(1)</script>[x](javascript:alert(1))');
  expect(result).not.toMatch(/<img|<script|onerror=|href="javascript:/);
});
