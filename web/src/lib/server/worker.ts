import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process';
import { createInterface } from 'node:readline';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { randomUUID } from 'node:crypto';

export type Operation = 'status' | 'catalogue' | 'chat' | 'runs' | 'start_run' | 'get_run' | 'get_trace' | 'cancel_run' | 'evaluate_run';
type Pending = { resolve: (value: unknown) => void; reject: (error: Error) => void; timer: ReturnType<typeof setTimeout> };

export class WorkerClient {
  private child?: ChildProcessWithoutNullStreams;
  private pending = new Map<string, Pending>();
  private stopped = false;
  private root: string;

  constructor(root?: string) {
    const cwd = process.cwd();
    this.root = root ?? process.env.LAB_ROOT ?? (existsSync(resolve(cwd, 'pyproject.toml')) ? cwd : resolve(cwd, '..'));
  }

  private start() {
    if (this.child && !this.child.killed) return;
    this.stopped = false;
    const python = process.env.LAB_PYTHON ?? resolve(this.root, '.venv/bin/python');
    if (!existsSync(python)) throw new Error('The Python environment is missing. Run the project setup first.');
    const child = spawn(python, ['-m', 'learning_lab.worker'], {
      cwd: this.root, env: { ...process.env, PYTHONUNBUFFERED: '1' }, stdio: ['pipe', 'pipe', 'pipe']
    });
    this.child = child;
    // Library logs stay on the server; browser responses never contain process environment values.
    child.stderr.on('data', () => {});
    const lines = createInterface({ input: child.stdout });
    lines.on('line', (line) => {
      try {
        const response = JSON.parse(line);
        if (response.version !== 1 || typeof response.id !== 'string') throw new Error('Invalid worker response');
        const pending = this.pending.get(response.id);
        if (!pending) return;
        clearTimeout(pending.timer);
        this.pending.delete(response.id);
        if (response.error) pending.reject(new Error(response.error.message));
        else pending.resolve(response.result);
      } catch {
        this.fail(new Error('The worker returned an invalid protocol message. Restart the app.'));
        child.kill('SIGTERM');
      }
    });
    child.on('error', () => this.fail(new Error('The Python worker could not start.')));
    child.on('exit', () => {
      if (this.child !== child) return;
      this.child = undefined;
      this.fail(new Error('The worker stopped. Active runs are interrupted; partial results remain saved.'));
    });
  }

  private fail(error: Error) {
    for (const item of this.pending.values()) { clearTimeout(item.timer); item.reject(error); }
    this.pending.clear();
  }

  request<T = unknown>(method: Operation, params: Record<string, unknown> = {}): Promise<T> {
    this.start();
    const id = randomUUID();
    return new Promise((resolveResult, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error('The operation timed out. Check saved run progress before retrying.'));
      }, method === 'chat' || method === 'evaluate_run' ? 160000 : 30000);
      this.pending.set(id, { resolve: (value) => resolveResult(value as T), reject, timer });
      this.child!.stdin.write(JSON.stringify({ version: 1, id, method, params }) + '\n');
    });
  }

  close() {
    if (this.stopped) return;
    this.stopped = true;
    this.child?.stdin.end();
    const child = this.child;
    if (child) { const timer = setTimeout(() => child.kill('SIGTERM'), 3000); timer.unref(); }
    this.fail(new Error('The app is shutting down.'));
  }
}

const globalWorker = globalThis as typeof globalThis & { learningLabWorker?: WorkerClient };
export const worker = globalWorker.learningLabWorker ??= new WorkerClient();
process.once('SIGTERM', () => worker.close());
process.once('SIGINT', () => worker.close());
