# LinkedIn Packaging: agent instructions

You are the operator. The person should describe their profile and give feedback, not run terminal commands.

1. Read [docs/agent-workflow.md](docs/agent-workflow.md) before generating or revising a package. Read the actual CLI/schema code where needed.
2. Use supplied profile, website, branding, photo and context. Ask only for missing essentials. Generate all 10 styles by default, then let the person choose a favorite from the localhost preview. Do not ask them to select a style upfront.
3. Handle installation and commands yourself. Use existing authorized browser/image tools and supplied assets before requiring extra services. Python or account installation may need a focused user step; never pretend it happened.
4. Keep API keys in ignored `.env` or environment variables. Never request keys in chat, print them, place them in commands, or include them in downloads. Only ask for a service when the selected workflow actually requires it.
5. Preserve identity and source-backed facts. Never borrow template claims, invent proof, or use the same photo/pose in the portrait and banner. Website context does not automatically apply company fonts/colors; use the explicit local brand-bundle workflow.
6. Render and inspect the assembled desktop/mobile previews for every style, and use an independent AI buyer review when available. A technical pass alone is not visual approval. Do not fabricate or manually green-light review metadata.
7. Start the loopback review server over the subject's output folder so all 10 styles appear together. Keep it running and return its actual localhost URL. Refine the chosen style from feedback; reuse approved assets and research, preserve prior versions, and refresh the previews.
8. Every style and subsequent revision must include usable `banner.png`, `portrait.png`, `headline.txt` and an editable source download. Keep its declared fonts, logos and media with its brief. A preview alone is not delivery.

For development: run `.venv/bin/python -m unittest discover -s tests -q`. Tests use local fixtures/mocks; do not call paid providers just to test code. Before publication, follow [docs/public-release.md](docs/public-release.md). Keep generated output, provider caches, private research, commercial font bundles and credentials out of the public project. Existing raster examples are demonstrations, not another person's reusable claims or assets.
