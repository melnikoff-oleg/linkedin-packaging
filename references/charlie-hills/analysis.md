# Charlie Hills 🦩 — visual reference analysis

Source: https://www.linkedin.com/in/charlie-hills/  
Local evidence: `banner.jpg`, `portrait.png`, `profile.json`, `headline.txt`. The original files were visually inspected individually. Banner source is **1400×349**; portrait is **800×800**. Capture: 6 November 2026. Bounds, font sizes and spacing below are visual estimates from the raster, not recovered editable design data; exact font family cannot be proved from these images.

## Banner decomposition

| Element | Bounds in source pixels (x, y, w, h) | Normalized bounds | Observation |
|---|---|---|---|
| Background | (0, 0, 1400, 349) | [0.0, 0.0, 1.0, 1.0] | White canvas with faint gray square grid approximately every 35 source px. |
| Main statement | (370, 93, 489, 109) | [0.2643, 0.2665, 0.3493, 0.3123] | “How to (actually) win” / “on LinkedIn right now”; “LinkedIn right now” is blue. |
| Event detail | (370, 222, 484, 24) | [0.2643, 0.6361, 0.3457, 0.0688] | “Thu 5 Nov · 5pm UK · with my guests”; first phrase darker/bolder, remainder gray. |
| Guest group | (885, 81, 478, 177) | [0.6321, 0.2321, 0.3414, 0.5072] | Four overlapping circular portraits; central Charlie circle larger, all white borders. |
| Guest captions | (892, 194, 469, 63) | [0.6371, 0.5559, 0.335, 0.1805] | Fatima Khan 116K followers; Charlie Hills 260K followers; Mischa Collins 72K followers; Magali De Reu 48K followers. Colored rounded badges. |

This capture is a time-sensitive live-session promotion, not an evergreen personal-brand banner. The event date shown is Thu 5 Nov; the capture is 6 Nov 2026, so the promotion is already dated at analysis time. It is nevertheless a useful visual reference: white/blue teaching energy, large practical promise, graph-paper background and friendly faces. Adapt the grammar rather than preserving the expired event structure.

The phrase “(actually)” functions as conversational skepticism: it acknowledges overpromising advice and makes the offer feel practical. The second line switches partway from black “on” to saturated LinkedIn-like blue. The main type is estimated 52–55 source px, bold 750–800, with line-height about 58 px and tight tracking around −2 px. It is an unverified grotesk; Inter Bold/ExtraBold is a reasonable substitute, not a proven font identification. Text begins x≈370 (26.4%) and y≈95, making the left quarter almost completely empty. The source grid is approximately 35 px square, strokes around 1 px and very low contrast (#F0F0F0 against white), so it reads as a subtle technical/workshop cue.

The four portrait circles begin near x=885. Charlie is central and larger (about 163 px diameter versus ~130–137 px for neighbors), so hierarchy is communicated before names are read. Thick white rings separate overlaps; colored badges sit on top of the lower circle edges. The badges are roughly 105–123 px wide, 41–48 px tall, with highly rounded corners and soft drop shadows. Names are small bold white sans (about 13–14 px) and follower counts about 11–12 px. This is dense detail at actual LinkedIn size; the promise and faces are the robust information, while exact follower counts are not.

### Color and contrast

Working palette: background #FFFFFF, text #202121, accent #0875D3, muted #7B7B7B, portrait_background #234DAD. Base/banner accent colors are approximations sampled from the raster; compression, gradients and antialiasing create nearby values. Use these as reconstruction tokens, not official brand standards. The large type relies on very high light/dark contrast for the primary message, while secondary textures and small proof are intentionally quieter. Keep important type away from the lower-left overlap zone. A useful conservative starting mask is x=0–25% and y=50–100%, then validate real viewport crops; this is a design assumption, not a guaranteed LinkedIn UI measurement.

## Portrait: framing, lighting and identity

The 800×800 standalone avatar uses a rich royal-blue softly textured studio background. Hair begins y≈93 (12%); head center is slightly right of frame center; eyes sit around y≈325 (41%); chin around y≈604 (76%). Head width is roughly 381 px (48%). The body is angled slightly while the face returns toward the camera. An open smile, visible teeth, short beard and casual black collared shirt communicate warmth and accessibility. Soft directional light from image-left illuminates the forehead/cheek with modest shadow on the opposite side. Blue helps the warm face stand out and matches the banner's keyword emphasis; it is not the exact same blue, which adds depth rather than looking like a flat template.

## Banner and avatar together

A bold blue circular avatar below the largely white banner anchors the composition on the left, balancing the cluster of circles on the right. The white avatar ring would echo the guest circles. Left overlap is especially safe: the entire first quarter is only grid. Repeating the same smiling person in the avatar and large guest circle reinforces identity. However, four guests plus follower counts are only appropriate when they are genuine collaborators in a real event; a one-person advisor should instead use an explicitly labeled cluster of genuine career cases, without a decorative second self-portrait or invented event context.

## Headline and positioning

Exact scraped headline:

> I help you (actually) use AI | AI OS for LinkedIn starts 9 Nov

“I help you (actually) use AI” states an approachable practical benefit, with “actually” echoing the banner voice. The second clause announces a cohort/program and precise launch date. It is short, human and commercially timely, but it needs regular maintenance: dated launches age quickly. In this capture, headline advertises 9 Nov while banner advertises 5 Nov, showing two separate promotions. For a new subject an evergreen practical sentence is preferable unless they supply an actual program or event date.

## Reproduction and QA checkpoints

1. Rebuild typography and simple effects in HTML/CSS/SVG at a 1584×396 design canvas, then render at 2×. Preserve the hierarchy, whitespace and palette, not the person's trademarks or claims.
2. Keep face identity anchored to the subject's original portrait. Never use the reference person's face as the identity input; reference images guide lighting/background/crop only.
3. Inspect the 3168×792 output at full resolution and at a typical ~790 px desktop display. Check text edges, glyphs, line wrapping, empty margins, and whether decorative detail becomes noise.
4. Inspect the portrait as a square and circle at 800, 200 and 48 px. Eyes/glasses/face should remain recognizable; no missing hair, distorted glasses, oversmoothed skin or hard cutout fringe.
5. Compose the actual banner/avatar/headline preview, including left overlap. Check a narrower mobile-like crop as a stress test; do not assert pixel-exact LinkedIn reproduction across devices.
6. Confirm every number, award, logo, affiliation and implied endorsement comes from the subject's evidence. Remove unsupported proof instead of filling empty slots.

**Specificity check:** Cover the name and portrait. If most people in the same industry could use the remaining text unchanged, revise the case, company, metric or distinctive detail. Check the combined profile, not just each asset. Logos must preserve the true relationship; approximate figures and their definitions must remain intact.

## Applying this reference

Use only the new subject's supported facts, photographs and authentic marks. Preserve the original slot geometry and hierarchy; leave unsupported proof empty. The renderer requires explicit `reference_content`. See the [design system](../../docs/design-system.md) and [reference fidelity guide](../../docs/reference-fidelity.md).
