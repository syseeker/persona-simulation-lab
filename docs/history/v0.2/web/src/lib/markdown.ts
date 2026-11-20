import DOMPurify from 'dompurify';
import { marked } from 'marked';

export function renderMarkdown(text: string): string {
  if (typeof window === 'undefined') return text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  return DOMPurify.sanitize(marked.parse(text, { async: false }), {
    ALLOWED_TAGS: ['p', 'strong', 'em', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'a', 'br', 'h3', 'h4'],
    ALLOWED_ATTR: ['href', 'title']
  });
}
