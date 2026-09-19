# TypeScript helper

This server-side-only helper delegates polling and retries to the official
`@higgsfield/client` package while limiting model identifiers to the catalog
documented in `docs/openapi.yaml`.

```bash
npm install
export HF_CREDENTIALS="your-api-key-id:your-api-key-secret"
npx tsx examples/generate.ts
```

Never import this package into browser or mobile application code.
