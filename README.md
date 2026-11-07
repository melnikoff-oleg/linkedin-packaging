# LinkedIn Packaging

Make a banner, portrait and headline with **Claude Code or Codex**. Get all 10 styles, pick your favorite in your browser, and ask for changes in plain English.

## Start here

1. **Open the project.** [Download the project](https://www.oleg.ae/downloads/linkedin-packaging.zip), unzip it, and open that folder in the **Codex app** or **Claude Code** on your computer.
2. **Connect your three API keys.** Create or sign in to each account, then get a key:

| Service | Where to get your key | Project setting |
|---|---|---|
| Kie | [API Key Management](https://kie.ai/api-key) → create and copy a key | `KIE_AI_API_KEY` |
| Apify | [Settings → API & Integrations](https://console.apify.com/settings/integrations) → Personal API tokens → **+ Create a new token** → copy | `APIFY_API_KEY` |
| Firecrawl | [API Keys](https://www.firecrawl.dev/app/api-keys) → create and copy a key | `FIRECRAWL_API_KEY` |

Ask your agent:

```text
Create .env from .env.example in this project's root folder if it doesn't exist, and open it for me. Preserve existing values. I'll paste my API keys there. Don't display keys in chat or logs.
```

In the local `.env` file beside `README.md`, paste each key privately after the matching `=` and save the file as `.env`, not `.env.txt`. Never paste keys into chat, logs or public files. Provider usage may cost extra.

3. **Paste your brief.** Replace the brackets and attach a clear photo:

```text
Use this project to create my LinkedIn packaging.

LinkedIn: [profile URL]
Website: [URL, if any]
Branding: [logo, colors, fonts, or use my website]
About me: [what I do, who I help, and real results]
Photo: [attach a clear photo]

Handle setup and generate all 10 styles using my branding. Show all 10 together in a localhost preview, alongside my original profile when available, so I can pick my favorite. Refine my choice from my feedback, then give me the banner, portrait, headline, and editable source files.
```

4. **Compare and refine.** Your agent generates all 10 styles and opens a localhost preview. Pick a favorite and give feedback in the same chat; the page updates after the agent rerenders. Keep the agent session running while viewing the local page. You do not need to type terminal commands.

When the original is available, the preview shows it alongside each style. Use presentation mode to show the results, or download **Upload files** and **Editable source**. Your files also stay in `output/` inside this folder. Nothing is posted to LinkedIn automatically.

An agent with local file and command access is required. It handles installation and can reuse supplied assets and research; the offline renderer itself makes no provider calls. Python installation may need one installer step on a new computer. Account setup and generation time vary.

[Visual guide](https://www.oleg.ae/linkedin-packaging) · [Agent workflow](docs/agent-workflow.md) · [Manual CLI reference](docs/cli.md) · [Local examples](examples/index.html)

## For developers

The renderer is a Python 3.10+ source project. `setup.sh` / `setup.ps1` install its dependencies; `docs/cli.md` covers manual generation and offline rendering. The local review server is started with `python -m linkedin_pack serve --output output --port 8765` using the project's virtual environment.

Run `.venv/bin/python -m unittest discover -s tests -q` after code changes. The tests do not buy provider requests. Before publishing, follow [release checks](docs/public-release.md); never include `.env`, provider caches or personal outputs.

Code is [MIT licensed](LICENSE). Third-party examples, marks and fonts have [separate terms](THIRD_PARTY.md).
