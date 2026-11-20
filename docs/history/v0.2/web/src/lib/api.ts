export async function labApi<T = any>(operation: string, body?: unknown): Promise<T> {
  const response = await fetch('/api/' + operation, body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error ?? 'The operation failed');
  return data as T;
}

export function pretty(value: unknown) { return JSON.stringify(value, null, 2); }
