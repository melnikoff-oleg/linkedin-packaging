# LinkedIn Packaging

Make a banner, portrait and headline with **Claude Code or Codex**. Get all 10 styles, pick your favorite in your browser, and ask for changes in plain English.

## Start here

1. [Download the project](https://www.oleg.ae/downloads/linkedin-packaging.zip) and unzip it.
2. Open that folder in the **Codex app** or **Claude Code** on your computer.
3. Paste this, replacing the brackets and attaching a clear photo:

```text
Use this project to create my LinkedIn packaging.

LinkedIn: [profile URL]
Website: [URL, if any]
Branding: [logo, colors, fonts, or use my website]
About me: [what I do, who I help, and real results]
Photo: [attach a clear photo]

Handle setup and generate all 10 styles using my branding. Show all 10 together in a localhost preview so I can pick my favorite. Refine my choice from my feedback, then give me the banner, portrait, headline, and editable source files.
```

Your agent handles setup and generates all 10 styles before you choose. You do not need to type terminal commands. Keep the agent session running while viewing the local page. Pick a favorite and give feedback in the same chat; the page updates after the agent rerenders.

The preview offers **Upload files** and **Editable source** downloads. Your files also stay in `output/` inside this folder. Nothing is posted to LinkedIn automatically.

An agent with local file and command access is required. It can use tools and assets you already have; if a requested image or data service needs a key, it will help you add your own privately to `.env`. Provider usage may cost extra. Python installation may need one installer step on a new computer. Account setup and generation time vary.

[Visual guide](https://www.oleg.ae/linkedin-packaging) · [Agent workflow](docs/agent-workflow.md) · [Manual CLI reference](docs/cli.md) · [Local examples](examples/index.html)

## For developers

The renderer is a Python 3.10+ source project. `setup.sh` / `setup.ps1` install its dependencies; `docs/cli.md` covers manual generation and offline rendering. The local review server is started with `python -m linkedin_pack serve --output output --port 8765` using the project's virtual environment.

Run `.venv/bin/python -m unittest discover -s tests -q` after code changes. The tests do not buy provider requests. Before publishing, follow [release checks](docs/public-release.md); never include `.env`, provider caches or personal outputs.

Code is [MIT licensed](LICENSE). Third-party examples, marks and fonts have [separate terms](THIRD_PARTY.md).
