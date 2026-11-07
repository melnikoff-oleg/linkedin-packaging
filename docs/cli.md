# Command-line usage

Run commands from the project folder after setup. `./package.sh` is shorthand for `.venv/bin/python -m linkedin_pack create` on macOS/Linux. Windows uses `.\.venv\Scripts\python.exe -m linkedin_pack`.

## Create a reference-faithful package

```bash
.venv/bin/python -m linkedin_pack create \
  --linkedin 'https://www.linkedin.com/in/your-profile/' \
  --style clarekitching \
  --context 'My buyer is a growing-business founder seeking part-time technology leadership.'
```

The tool saves source evidence, fills the selected original's fixed slots, prepares original marks, creates identity-faithful photographs, renders assembled previews and requests a separate AI buyer review. It does not publish to LinkedIn. All newly generated packages use `layout_mode: "reference-faithful"`; prepared legacy briefs keep their existing rendering path.

An explicit style uses one structured copy request. Without `--style`, one request selects a reference and drafts the subject story, then another fills its exact slot schema. The content schema contains field types, counts and phrase budgets, not the Kal fixture's claims. Company/metric retention checks run before paid image generation, though after copy generation.

Context-only intake skips Apify:

```bash
.venv/bin/python -m linkedin_pack create \
  --name 'Alex Morgan' \
  --context 'My actual role, experience, audience and supported results are ...' \
  --portrait './alex.jpg' --style adrian-kul
```

Name, factual context and a real portrait (or `--reuse-portrait`) are required without LinkedIn. Sources are labeled user-provided. A folder containing another person's source is rejected. Default output is `output/<profile-handle-or-safe-name>/`.

## Options

| Flag | Effect |
|---|---|
| `--linkedin URL` | Collect/save the subject's public profile; optional with complete context-only intake |
| `--name NAME` | Subject name for context-only intake |
| `--website URL` | Retrieve website content/branding context; a failed scrape stops with an error |
| `--context TEXT` | Factual background, audience and preferences |
| `--style SLUG` | Fill one original reference's fixed composition |
| `--all-styles` | Generate all ten styles into separate subfolders |
| `--portrait PATH` | Use a local source identity photograph |
| `--reuse-portrait PATH` | Skip avatar generation and use an approved photograph |
| `--banner-photo PATH` | Supply a distinct wider shot; `create` extracts an opaque background, while `render` requires transparent PNG |
| `--brief PATH` | Use prepared JSON and skip paid copy generation; incompatible with `--all-styles` |
| `--output DIRECTORY` | Choose destination |
| `--background PATH` | Supply a local background image where the template supports it |
| `--keep-reference-colors` | Retain the reference palette; already the new-mode default |
| `--use-website-colors` | Only for prepared legacy briefs with `--website`; explicitly rejected in reference-faithful mode before network/paid work |

Website content can supply evidence without recoloring the template. New reference generation never applies extracted colors implicitly. In legacy prepared mode, explicit palette selection preserves the existing contrast/provenance behavior. Extracted font names remain context; bundled fonts are used for rendering.

`--all-styles` can involve ten copy requests, ten avatars, five distinct banner photographs, up to five extractions and ten buyer reviews before cache/supplied-asset savings. Changed prompts/sources create new requests. A rejection does not trigger automatic paid regeneration.

## Brief schema and fixed slots

`brief.json` retains the ordinary subject fields: name, audience, positioning, evidence, selected style, headline, legacy banner metadata, portrait guidance and rationale. New-mode additions are:

```json
{
  "layout_mode": "reference-faithful",
  "selected_style": "adrian-kul",
  "reference_content": {
    "brand": "AM",
    "title": "A technology partner for growing teams"
  },
  "proof_cards": [],
  "proof_points": []
}
```

This is a schema fragment, not a complete brief. Each style has its own precise `reference_content` tree. The registry and `reference_slot_contract()` provide that shape, array counts, character budgets and fixed style values. The renderer requires explicit content and never falls back to another person's facts. Generated content is checked against the phrase budget; actual rendering still determines glyph fit.

All visible banner copy belongs in `reference_content`. Legacy `banner_title`, `banner_subtitle` and `cta` are metadata in this mode; they cannot satisfy specificity when the visible banner is generic. Keep a nonempty headline of at most 220 characters and source entries for every displayed factual claim. Preserve approximations, metric definitions, role scope and time windows.

Do not alter layout or type size to fit long prose. Rewrite within the original slot, preserving its intended line count and phrase density. Empty unsupported proof/logo slots are permitted; invented awards, press logos, testimonials or people are not. There is no active one-proof-unit limit or universal 48 px type floor in reference mode.

## Named cases and original company logos

The source inventory retains up to 40 roles and company-scoped metric/story evidence. `validate_specificity()` inspects actual reference strings and coherent named-case groups, rejects absent or wrongly attributed metrics, and refuses generic output when rich source cases were available. Limited evidence is recorded rather than replaced with fabricated achievements. This is a conservative retention gate, not perfect causal or factual verification.

Reference logo arrays use only subject-specific source identities or an empty string. Curated product aliases require exact original-asset provenance and a matching documented role; a parent-company ID cannot be relabeled as the product. A visible company name beside a logo must match that actual asset identity.

Original assets live at `logos/<key>.png` with source/hash records in `logos/provenance.json`. Reference mode uses transparent marks, preserves proportions and may tint original alpha geometry. It does not redraw logos or add white plates. Opaque/unavailable marks are removed from their slots with `logo_preparation.omitted` warnings, leaving reserved geometry. Known truthful labels remain in existing text slots. Offline rerenders copy local originals and provenance; they do not download replacements.

## Separate photographs

Diandra, Lara, Matt, Rob and Jake use a distinct banner photograph; Clare, Adrian, Chris, Charlie and Liam do not. The avatar is never substituted into the banner. Photo-pair checks reject identical or highly similar resized/recolored/mirrored pixels, but a separate visual review must still catch repeated pose or uncanny duplication.

Match the original avatar palette/clothing and banner pose direction while preserving identity. The runtime creates a wider 3:4 banner shot, then a background-only extraction when necessary. Genuine transparency is required; a checkerboard, opaque plate or token clear corner fails. Use existing prepared assets for copy/layout revisions rather than paying to regenerate unchanged photographs.

## Offline render and review

```bash
.venv/bin/python -m linkedin_pack render \
  --brief './output/my-package/brief.json' \
  --portrait './output/my-package/portrait.png' \
  --banner-photo './output/my-package/banner-photo-cutout.png' \
  --output './output/revised'
```

Omit the banner-photo flag for person-free templates. Offline rendering requires no keys, never extracts a background and leaves visual approval pending. Fixed reference layouts live in `reference_group_a.py`, `_b.py`, `_c.py`, dispatched by `reference_layout.py`; legacy layouts remain in their existing modules.

Inspect exported pixels against the original at equal scale. Technical QA checks dimensions, loaded fonts, bounds, collisions, supplied slots and measured reference regions; it does not establish aesthetic fidelity. Secondary text retains the source hierarchy. The assembled primary message/headline must be understandable at native 792/390, while fine labels must not be falsely described as fully mobile-readable.

```bash
.venv/bin/python -m linkedin_pack review \
  --output './output/revised' \
  --audience 'A founder considering fractional technology leadership.'
```

The paid buyer simulation receives only neutral desktop/mobile cards and the persona. A separate reference-comparison review checks fidelity. Buyer approval is tied to current screenshots/deliverables, persona and prompt. Technical pass plus a current accepted, specific, clear verdict with no material concerns is required for `ready`; historical or stale reviews cannot supply it. This is AI simulation, not human testimony or audited business results.

For `render`, exit code 0 means technical checks passed and review remains required. For `create`/`review`, exit code 0 means current technical/buyer gates passed. Exit code 2 reports invalid input, provider/check failure or a revision verdict. Read the explanation and QA record; do not blindly buy another image generation.

## Public examples and authoring scripts

The public examples are finished raster demonstrations. Private source profiles, commercial fonts and historical review archives are excluded. The calibration/account scripts under `scripts/` remain available for developers supplying their own local account and asset records; they do not rebuild the public example gallery out of the box. Normal `create`, `render`, `review` and `styles` commands do not require those archives.

## Sharing and recovery

```bash
.venv/bin/python -m linkedin_pack collect-references
.venv/bin/python -m linkedin_pack export --output './dist/linkedin-package-shareable.zip'
```

Collection retains source snapshots; refresh deliberately rather than discarding a live collection run. Export uses a broad project-directory allowlist and excludes common credentials, caches, logs and virtual environments. For public publication, also follow [the release checks](public-release.md): independently scan known secrets and check third-party asset scope before sharing. The exporter alone is not a comprehensive public-release security check.

After a polling timeout, resume the same saved task. Ambiguous paid submissions are not blindly resubmitted. See [provider recovery](providers-kie.md). A different prompt, model or source is a different request and may incur a charge.
