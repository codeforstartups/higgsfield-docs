import { config, higgsfield } from "@higgsfield/client/v2";

export const supportedModels = [
  "higgsfield-ai/soul/standard",
  "kling-video/v2.5-turbo/pro/image-to-video",
  "kling-video/v2.5-turbo/pro/text-to-video",
  "kling-video/v2.5-turbo/standard/image-to-video",
  "minimax/hailuo-2.3/standard/image-to-video",
  "minimax/hailuo-2.3/standard/text-to-video",
] as const;

export type ModelId = (typeof supportedModels)[number];
export type Input = Record<string, unknown>;
export type Subscribe = (
  model: string,
  options: { input: Input; withPolling: true },
) => Promise<unknown>;

export function configureFromEnvironment(
  credentials = process.env.HF_CREDENTIALS,
): void {
  if (!credentials) {
    throw new Error("Set HF_CREDENTIALS to API_KEY_ID:API_KEY_SECRET");
  }
  config({ credentials });
}

export async function generateWith(
  subscribe: Subscribe,
  model: ModelId,
  input: Input,
): Promise<unknown> {
  return subscribe(model, { input, withPolling: true });
}

export async function generate(
  model: ModelId,
  input: Input,
): Promise<unknown> {
  return generateWith(higgsfield.subscribe.bind(higgsfield), model, input);
}

export function outputUrls(result: unknown): string[] {
  if (!isRecord(result) || !Array.isArray(result.jobs)) {
    return [];
  }

  const urls: string[] = [];
  for (const job of result.jobs) {
    if (!isRecord(job) || !isRecord(job.results)) {
      continue;
    }
    const raw = job.results.raw;
    collectUrls(raw, urls);
  }
  return urls;
}

function collectUrls(value: unknown, urls: string[]): void {
  if (Array.isArray(value)) {
    value.forEach((item) => collectUrls(item, urls));
    return;
  }
  if (!isRecord(value)) {
    return;
  }
  if (typeof value.url === "string") {
    urls.push(value.url);
  }
  Object.values(value).forEach((item) => collectUrls(item, urls));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
