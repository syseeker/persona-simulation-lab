declare module '#dataset-reader' {
  export class DatasetQueryError extends Error {}
  export function readDatasetCatalogue(): Promise<unknown>;
  export function readDatasetOptions(query: URLSearchParams): Promise<unknown>;
  export function readDatasetPage(query: URLSearchParams): Promise<unknown>;
}
