# Save the original profile for comparison

The agent does this before generating edited assets. Keep the person's original LinkedIn name, headline, portrait and banner; never use the generated portrait or banner as their “before.” The local gallery automatically pairs this saved header with all ten styles.

From the project environment, run:

```bash
.venv/bin/python -m linkedin_pack before --profile output/person/source/profile.json --output output/person
```

The normalized JSON contains `name`, `headline`, `location`, `url`, and local `portrait_file` / `banner_file` names relative to the JSON folder. An agent collecting with its own browser can save those same fields and original image files. Optional `--portrait ORIGINAL_PATH` and `--banner ORIGINAL_PATH` supply original local images when the JSON does not name them. No network or provider calls occur.

The command writes only `before/review-desktop.png`, `before/review-mobile.png` and `before/metadata.json` under the gallery root. These are reconstructed profile headers from saved source assets, not claims of a current live LinkedIn screenshot. Unchanged inputs reuse the existing captures.

If the original banner is unavailable, the before uses a neutral cover and says so. If the original portrait is unavailable, capture stops with a focused explanation; obtain the original photo or show the generated styles without a before. Never invent a missing original image. Raw dossiers and source files stay private; the gallery only receives the two raster previews and sanitized display metadata.

`create --linkedin ...` attempts this capture once, immediately after collecting the original profile and before editing images. Its default gallery root is `--output`. If generation is nested, pass `--before-output output/person` alongside `--output output/person/v01`. Missing original media does not stop generation; the command explains why the before is unavailable. Agent-prepared offline `render` workflows call `before` once explicitly, then serve the common subject root:

```bash
.venv/bin/python -m linkedin_pack serve --output output/person --port 8765
```
