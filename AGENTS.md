# Working on this project

This is a standalone Python CLI. A recipient does not need Codex or an OpenAI API key.

- Read README.md for setup and docs/cli.md for supported commands.
- Use Python 3.10+ and install with `bash setup.sh` or the Windows command in README.md.
- Keep credentials in ignored `.env` or environment variables. Never print key values, put them in commands, or commit local outputs.
- Run `.venv/bin/python -m unittest discover -s tests -q` after code changes. Tests use local/synthetic fixtures and mocks; they make no paid provider requests.
- Do not invoke live `create`, `review`, or `collect-references` merely to test code. These can incur charges. Offline `render` is suitable for visual verification.
- Preserve fixed reference slot geometry and explicit user facts. Avoid invented endorsements or metrics.
- Keep example raster files unchanged unless the user asks for revisions. Commercial font bundles, website captures, raw profile archives, and private client research do not belong in this repository.
- Before publication, follow docs/public-release.md and scan the exact staged content.
