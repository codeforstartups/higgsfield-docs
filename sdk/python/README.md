# Python helper

This thin package delegates authentication, polling, retries, and uploads to
the official `higgsfield-client` package while limiting model identifiers to
the catalog documented in `docs/openapi.yaml`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export HF_KEY="your-api-key-id:your-api-key-secret"
python examples/generate.py
```

Use this only in trusted server-side environments.
