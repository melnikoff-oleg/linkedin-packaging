# Liam Karlsson — visual reference analysis

Source: https://www.linkedin.com/in/liamkarlsson/  
Local evidence: `banner.jpg`, `portrait.png`, `profile.json`, `headline.txt`. The original files were visually inspected individually. Banner source is **1400×349**; portrait is **800×800**. Capture: 6 November 2026. Bounds, font sizes and spacing below are visual estimates from the raster, not recovered editable design data; exact font family cannot be proved from these images.

## Banner decomposition

| Element | Bounds in source pixels (x, y, w, h) | Normalized bounds | Observation |
|---|---|---|---|
| Background | (0, 0, 1400, 349) | [0.0, 0.0, 1.0, 1.0] | Navy field with dense tan/gold stippling forming abstract billowing cloud/wave shapes. |
| Citera brand | (35, 20, 190, 50) | [0.025, 0.0573, 0.1357, 0.1433] | White checker-like circular symbol and serif wordmark, top-left. |
| Main statement | (394, 58, 947, 102) | [0.2814, 0.1662, 0.6764, 0.2923] | “Grow Traffic and Revenue from” / “AI Search, GEO, AEO and SEO on Autopilot”; right aligned white bold type. |
| Proof capsule | (966, 207, 377, 45) | [0.69, 0.5931, 0.2693, 0.1289] | Navy rounded rectangle: “Trusted by 1000+ Brands & Agencies” in white monospaced/bold small type. |
| Platform strip | (766, 273, 578, 43) | [0.5471, 0.7822, 0.4129, 0.1232] | Row of 11 white AI/search/platform symbols. Recognizable G, Bing, Meta infinity, OpenAI knot and asterisk among others; ambiguous marks should not be confidently named. |

Navy and gold create a premium, slightly engraved/financial aesthetic that is uncommon among the flat-color creator references. Organic stipple fields curve through the canvas, while the white typography remains rigid, large and right-aligned. The texture is densest at the left and lower-right; a darker navy pocket under the top copy helps reading. Unlike the orange globe, this is not a regular geometric dot pattern: irregular ink-like marks and flowing negative space produce a printed/etched effect.

The main type is an unverified bold grotesk, approximately 48–51 source px at 700–800 weight, line-height about 59 px and slight negative tracking (~−0.5 px). The first line begins around x=618 and the second x=395, both ending near x=1342, giving a right margin of ~58 px (4%). The sentence is unusually long—its comprehensiveness supports category positioning but weakens instant mobile scanning. “Autopilot” is an outcome/mechanism promise and should not be transferred to a hands-on executive advisor.

The brand is a serif wordmark around 49 px high beside a pixel/checkered circular icon. This serif contrast provides sophistication without adding another text paragraph. The proof capsule at y≈208 is ~377×43 px, corner radius around 12 px, with navy fill that suppresses the texture behind it. Proof type resembles a monospaced or slab-like bold face at 16–18 px with ~0.7 px tracking. The bottom symbols are approximately 35–40 px high with 17–21 px gaps. Their white unification prevents multiple logo colors from competing with the navy/gold system. These marks identify an ecosystem; they do not by themselves substantiate the “trusted by” number.

### Color and contrast

Working palette: background #072A76, text #FFFFFF, accent #C9A36F, muted #E7DDCE, portrait_background #072A76. Base/banner accent colors are approximations sampled from the raster; compression, gradients and antialiasing create nearby values. Use these as reconstruction tokens, not official brand standards. The large type relies on very high light/dark contrast for the primary message, while secondary textures and small proof are intentionally quieter. Keep important type away from the lower-left overlap zone. A useful conservative starting mask is x=0–25% and y=50–100%, then validate real viewport crops; this is a design assumption, not a guaranteed LinkedIn UI measurement.

## Portrait: framing, lighting and identity

The 800×800 portrait repeats the same navy/gold texture behind a warm, nearly frontal subject. Hair begins y≈60 (7.5%); eye line y≈309 (39%); chin y≈522 (65%). Upper body fills much of the lower half and head spans approximately x=250–579 (41%). Large dark glasses are a key recognizable feature, with visible cool reflections in the lenses. A light striped shirt and dark padded vest introduce professional/casual texture; the small garment badge remains visible. Lighting is soft and warm from front-left, but this image is less crisp than the others and the hair/background boundary has some softness. The face is relaxed with closed mouth, direct gaze and a slight angle. The patterned backdrop can compete with fine hair detail; a cleaner area directly behind the head would improve separation.

## Banner and avatar together

This is the strongest literal background continuity of the five: banner and portrait use the same blue-and-gold texture, making the two assets read as one brand system. White banner text is balanced by the light shirt, dark frame/vest and warm face. The lower-left overlap mostly covers abstract texture, while the logo sits high enough to remain visible on typical desktop layouts. Texture survives crop changes better than fixed illustration edges. At mobile scale, however, the long sentence and 11-symbol row become crowded; adaptation should shorten wording and reduce decorative logos instead of shrinking type.

## Headline and positioning

Exact scraped headline:

> CEO @ Citera - Grow Traffic & Revenue from GEO, AEO and SEO | VC Scout | Young Entrepreneur of the Year 2026 | Don’t ask me what my favorite fragrance is 😉

The headline begins with CEO/company, then repeats the measurable traffic/revenue promise and technical categories. Additional credentials (VC Scout, named entrepreneurial award and year) build authority, and the fragrance joke adds a personal hook. This is a dense mix of service, role, recognition and personality; its strength is memorable breadth, while its limitation is that the late clauses may be truncated. The award and business claims are source-profile statements, not independently verified. A new subject should keep only credentials evidenced in their own source and choose a human detail only if they supply it.

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
