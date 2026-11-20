import { WorkerClient } from './worker.ts';
const state = globalThis as typeof globalThis & { citizenJourneyWorker?: WorkerClient };
export const journeyWorker = state.citizenJourneyWorker ??= new WorkerClient(undefined, { guideOnly: true });
process.once('SIGTERM', () => journeyWorker.close());
process.once('SIGINT', () => journeyWorker.close());
