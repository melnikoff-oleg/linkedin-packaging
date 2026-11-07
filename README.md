# LinkedIn Packaging

Create a LinkedIn banner, profile photo, headline, and desktop/mobile previews from your own experience and portrait. Choose one of ten saved reference layouts, or let the tool choose. It runs as a standalone Python command; no Codex or OpenAI API key is required.

[Visual setup guide](https://www.oleg.ae/linkedin-packaging) · [Finished examples (open locally)](examples/index.html) · [Command guide](docs/cli.md) · [Providers and recovery](docs/providers-kie.md)

## Quick start

You need **Python 3.10 or newer**, an internet connection, and a funded [Kie.ai account](https://kie.ai/api-key). Allow around **three minutes for setup once Python and your provider accounts are ready**; downloads and connection speed can make this longer. Account signup and image generation are separate and can take longer.

1. Click **Code → Download ZIP** on [this repository](https://github.com/melnikoff-oleg/linkedin-packaging), extract it, and open a terminal in the extracted folder. Git users can instead run `git clone https://github.com/melnikoff-oleg/linkedin-packaging.git` and `cd linkedin-packaging`.
2. Install the tool and its Chromium renderer:

   **macOS / Linux**
   ```bash
   bash setup.sh
   ```

   **Windows PowerShell**
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
   ```

3. Open the new **`.env`** file in a text editor and replace the placeholders with **your own** keys. Dotfiles may be hidden in your file browser: use `open -e .env` on macOS, `notepad .env` on Windows, or `nano .env` on Linux from the project terminal. This local file is ignored by Git. Do not put keys in commands, screenshots, or files you share.

   | Key | When you need it |
   |---|---|
   | `KIE_AI_API_KEY` | Required for AI copy, photo generation, and buyer review |
   | `APIFY_API_KEY` | Required when you supply a LinkedIn profile URL; get one from [Apify](https://console.apify.com/settings/integrations) |
   | `FIRECRAWL_API_KEY` | Optional; needed only with `--website`; get one from [Firecrawl](https://www.firecrawl.dev/app) |

4. Run one command with your profile URL and audience:

   **macOS / Linux**
   ```bash
   ./package.sh --linkedin "https://www.linkedin.com/in/your-handle/" --style laraacostar --context "I help B2B founders with product strategy."
   ```

   **Windows PowerShell**
   ```powershell
   .\.venv\Scripts\python.exe -m linkedin_pack create --linkedin "https://www.linkedin.com/in/your-handle/" --style laraacostar --context "I help B2B founders with product strategy."
   ```

The result is saved in **`output/your-handle/`**. Open `preview.png` and `preview-mobile.png`, check the facts and likeness, then use `banner.png`, `portrait.png`, and `headline.txt` for your LinkedIn profile. The tool does not publish or change your account.

**Provider requests cost money.** One style can make separate requests for copy, a profile photo, a wider banner photo, background extraction, and review. An AI review can request revisions; this is not a guarantee of a finished result on the first try. Do not blindly rerun failed paid requests: read [recovery instructions](docs/providers-kie.md).

## Start with a photo instead of a LinkedIn URL

This needs only Kie. Put your portrait in the project folder and replace the sample facts with your actual experience:

```bash
./package.sh --name "Alex Morgan" --portrait ./alex.jpg --style adrian-kul --context "I advise B2B founders on product strategy. My documented experience includes ..."
```

On Windows, replace `./package.sh` with `.\.venv\Scripts\python.exe -m linkedin_pack create`.

## Choose a style

```bash
.venv/bin/python -m linkedin_pack styles
```

The ten IDs are `clarekitching`, `diandraescobar`, `laraacostar`, `mattgray1`, `adrian-kul`, `donnellychris`, `rob-hoffman-ceo`, `jakezward`, `charlie-hills`, and `liamkarlsson`. Omit `--style` for automatic selection. `--all-styles` generates all ten and can make many more paid requests.

Reference layouts retain their original hierarchy and palette. Facts, employer relationships, company marks, and photographs must belong to the new subject. A role at a company is not its endorsement. Unsupported proof slots stay empty. The examples are local design demonstrations, not LinkedIn endorsements or independently audited business results.

## Edit and render offline

Edit `reference_content` in a generated `brief.json`, keeping the same fields and array lengths. Then rerender without paid calls:

```bash
.venv/bin/python -m linkedin_pack render --brief output/your-handle/brief.json --portrait output/your-handle/portrait.png --banner-photo output/your-handle/banner-photo-cutout.png --output output/revised
```

Omit `--banner-photo` for Clare, Adrian, Chris, Charlie, and Liam. The other five styles require a separate transparent banner photograph. Offline rendering performs technical checks and leaves visual review pending. See [all options and review commands](docs/cli.md).

## Troubleshooting

- **Python missing:** install [Python](https://www.python.org/downloads/); on Windows enable “Add Python to PATH.” Restart your terminal.
- **Linux cannot create a virtual environment:** install your distribution's Python venv package, often `python3-venv`, and rerun setup.
- **Linux Chromium is missing system libraries:** run `.venv/bin/python -m playwright install-deps chromium` and follow its system-package prompts, then rerun setup.
- **API/key error:** check your own `.env` values, provider balance, and the requirements table above. Existing environment variables take precedence over `.env`.
- **Image generation times out:** keep the output and cache folders. Rerun the unchanged command to resume the saved task, unless the message says the submission outcome is unknown; then inspect the provider dashboard first.

Setup installs from this source folder with `pip install -e .`. Keep the folder in place. Installing a Python wheel alone is not supported because the renderer also needs the bundled fonts, prompts, and reference files.

## Development and licensing

```bash
.venv/bin/python -m unittest discover -s tests -q
```

Tests use synthetic/local fixtures and mocks; they do not purchase provider requests. Before publishing changes, use [the release checks](docs/public-release.md). Historical client research, website captures, credentials, commercial font bundles, and private build archives are excluded from this source release.

Code is [MIT licensed](LICENSE). Font licenses and third-party reference/demo ownership are described in [THIRD_PARTY.md](THIRD_PARTY.md).
