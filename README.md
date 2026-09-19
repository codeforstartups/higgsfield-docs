# Higgsfield Docs

An interactive, developer-maintained companion for the operations in
Higgsfield's supplementary public OpenAPI specification. It includes a Swagger
UI portal, safe cURL workflows, and thin Python and TypeScript helpers built on
the official Higgsfield SDKs.

> This is not an official Higgsfield repository. The live Higgsfield Console
> contains models that are absent from the supplementary OpenAPI file. This
> project deliberately documents only the operations listed below.

## Documented operations

| Category | Operation |
| --- | --- |
| Soul | `POST /higgsfield-ai/soul/standard` |
| Kling Video | `POST /kling-video/v2.5-turbo/pro/image-to-video` |
| Kling Video | `POST /kling-video/v2.5-turbo/pro/text-to-video` |
| Kling Video | `POST /kling-video/v2.5-turbo/standard/image-to-video` |
| MiniMax | `POST /minimax/hailuo-2.3/standard/image-to-video` |
| MiniMax | `POST /minimax/hailuo-2.3/standard/text-to-video` |
| Requests | `GET /requests/{request_id}/status` |
| Requests | `POST /requests/{request_id}/cancel` |

Catalog snapshot: September 19, 2026.

## Open the API portal

Serve the repository root so Swagger UI can load its YAML document:

```bash
python3 -m http.server 8080
```

Open <http://localhost:8080/docs/>. If that port is already in use by another
service, pick a free one; a different app on the same port will serve its own
`/docs` page instead. The static `docs/` directory is also ready to use as a
GitHub Pages publishing source.

## Authentication and security

Higgsfield expects this server-side header:

```http
Authorization: Key API_KEY_ID:API_KEY_SECRET
```

Copy `.env.example` to `.env` and replace placeholders locally. `.env` is
ignored by Git. Never use Higgsfield credentials in browser or mobile code.
Swagger UI's authorization control is intended only for trusted local testing.

The credential previously present in `curl.md` must be revoked in the
Higgsfield Console; removing it from this folder cannot invalidate it.

## Request lifecycle

Generation calls return immediately with a `request_id`, `status_url`, and
`cancel_url`. Persist the ID and poll with backoff until the request becomes
`completed`, `failed`, `nsfw`, or `canceled`. A request can be canceled only
while queued. Output URLs are retained for at least seven days, so copy media
that needs long-term storage.

Do not blindly retry generation `POST` requests after an ambiguous timeout:
the API does not currently support idempotency keys.

## Examples

Run the generic cURL flow with the default Soul endpoint:

```bash
chmod +x examples/curl/*.sh
./examples/curl/submit-and-wait.sh
```

Pass a model path and JSON file for another documented model:

```bash
./examples/curl/submit-and-wait.sh \
  minimax/hailuo-2.3/standard/text-to-video \
  ./request.json
```

Python setup is documented in `sdk/python/README.md`; TypeScript setup is in
`sdk/typescript/README.md`. Both helpers use official Higgsfield clients for
authentication, polling, and retries instead of reimplementing that lifecycle.
Use those official clients directly when you need cancellation or uploads.

The separate `curl.md` Marketing Studio example is retained because it was
already part of this project, but that endpoint is intentionally not added to
the portal because it is absent from the selected OpenAPI source.

## Source policy

- [Official documentation index](https://docs.higgsfield.ai/docs/llms.txt)
- [Supplementary OpenAPI specification](https://docs.higgsfield.ai/docs/openapi.json)
- [Authentication](https://docs.higgsfield.ai/docs/authentication.md)
- [Requests and lifecycle](https://docs.higgsfield.ai/docs/concepts/requests.md)
- [Webhooks](https://docs.higgsfield.ai/docs/how-to/webhooks.md)
- [Errors and retries](https://docs.higgsfield.ai/docs/concepts/errors.md)
- [Official SDKs](https://docs.higgsfield.ai/docs/how-to/sdk)

Higgsfield states that model-specific documentation and the Console are
authoritative when sources differ. Before production use, verify endpoint
availability and input schemas against the model documentation available to
your account.

## Validation

```bash
npx --yes @redocly/cli lint docs/openapi.yaml

cd sdk/python
python -m pip install -e ".[dev]"
ruff check .
pytest

cd ../typescript
npm install
npm run typecheck
npm test
```
