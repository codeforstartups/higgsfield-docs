import {
  configureFromEnvironment,
  generate,
  outputUrls,
} from "../src/index.js";

configureFromEnvironment();

const result = await generate("higgsfield-ai/soul/standard", {
  prompt: "Editorial portrait in soft daylight",
  num_images: 1,
  resolution: "2K",
  aspect_ratio: "4:3",
});

for (const url of outputUrls(result)) {
  console.log(url);
}
