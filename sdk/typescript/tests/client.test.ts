import assert from "node:assert/strict";
import test from "node:test";

import { generateWith, outputUrls, type Subscribe } from "../src/index.js";

test("generateWith delegates using polling", async () => {
  const calls: unknown[] = [];
  const subscribe: Subscribe = async (model, options) => {
    calls.push([model, options]);
    return {
      isCompleted: true,
      jobs: [{ results: { raw: { url: "https://cdn.test/video.mp4" } } }],
    };
  };

  const result = await generateWith(
    subscribe,
    "minimax/hailuo-2.3/standard/text-to-video",
    { prompt: "Test", duration: 6 },
  );

  assert.deepEqual(calls, [
    [
      "minimax/hailuo-2.3/standard/text-to-video",
      { input: { prompt: "Test", duration: 6 }, withPolling: true },
    ],
  ]);
  assert.deepEqual(outputUrls(result), ["https://cdn.test/video.mp4"]);
});

test("outputUrls supports nested and array outputs", () => {
  const result = {
    jobs: [
      {
        results: {
          raw: {
            images: [
              { url: "https://cdn.test/1.jpg" },
              { url: "https://cdn.test/2.jpg" },
            ],
          },
        },
      },
    ],
  };

  assert.deepEqual(outputUrls(result), [
    "https://cdn.test/1.jpg",
    "https://cdn.test/2.jpg",
  ]);
});
