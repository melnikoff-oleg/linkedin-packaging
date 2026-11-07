# Rob Hoffman — visual reference analysis

Source: https://www.linkedin.com/in/rob-hoffman-ceo/  
Local evidence: `banner.jpg`, `portrait.jpg`, `profile.json`, `headline.txt`. The original files were visually inspected individually. Banner source is **1400×350**; portrait is **800×800**. Capture: 6 November 2026. Bounds, font sizes and spacing below are visual estimates from the raster, not recovered editable design data; exact font family cannot be proved from these images.

## Banner decomposition

| Element | Bounds in source pixels (x, y, w, h) | Normalized bounds | Observation |
|---|---|---|---|
| Background | (0, 0, 1400, 350) | [0.0, 0.0, 1.0, 1.0] | Near-black #121212 with soft olive/lime glow at bottom-left and upper-right. |
| Contact wordmark | (37, 43, 169, 40) | [0.0264, 0.1229, 0.1207, 0.1143] | White custom lowercase logo, isolated in upper-left. |
| Main statement | (547, 55, 470, 110) | [0.3907, 0.1571, 0.3357, 0.3143] | “The search agency” in white / “built for what’s next.” in lime. |
| Supporting line | (549, 191, 407, 25) | [0.3921, 0.5457, 0.2907, 0.0714] | “Scale your SEO content effortlessly” in white. |
| Proof block | (549, 247, 382, 67) | [0.3921, 0.7057, 0.2729, 0.1914] | “RECENTLY HELPED:” above Shopify, Kajabi and beehiiv marks in white. |
| Banner person | (1048, 15, 266, 335) | [0.7486, 0.0429, 0.19, 0.9571] | Black-and-white waist/upper-body cutout, seated/leaning slightly forward, cropped at bottom. |
| Press proof | (1321, 22, 59, 81) | [0.9436, 0.0629, 0.0421, 0.2314] | Small “AS SEEN IN:” with Forbes + Inc. in black on the lime-lit far-right area. |

This layout converts a very large dark negative-space region into perceived confidence. The main copy starts unusually far right at 39% of the width; the left third holds only the small wordmark and atmospheric glow. The promise sits between that empty field and the right-side human cutout, producing a restrained three-column composition. The person acts as a visual full stop and looks directly at the viewer. Lime is reserved for the future-oriented second line and background light, so it has a clear semantic role.

Typeface is unverified, close to Inter/Helvetica Neue. Main lines are about 53–56 source px at regular 400 weight, line-height 55–58 px, slight negative tracking (~−1 to −1.5 px). This is noticeably lighter than Jake's or Liam's heavy slogans. Supporting type is approximately 24 px at y=191, separated from the slogan by ~27 px. Proof label is ~16 px bold/all-caps; logos occupy a ~32 px high row. Left alignment remains consistent at x≈549 for slogan, support, label and logos. The right portrait starts x≈1050, giving the text roughly 25–30 px of breathing room before it.

The wordmark is about 170 px wide with 37 px outer margin. The bottom-left glow uses a diffuse radius of roughly 200 px with no hard circle edge. The larger upper-right glow fades under the person, creating silhouette separation without an obvious neon outline. The press logos intentionally use dark ink on the glow, unlike the white client row. Logo shapes and company names are evidence claims: copying them to another person's banner would imply relationships they may not have.

### Color and contrast

Working palette: background #121212, text #F8F8F6, accent #CCE83C, muted #C9C9C7, portrait_background #303030. Base/banner accent colors are approximations sampled from the raster; compression, gradients and antialiasing create nearby values. Use these as reconstruction tokens, not official brand standards. The large type relies on very high light/dark contrast for the primary message, while secondary textures and small proof are intentionally quieter. Keep important type away from the lower-left overlap zone. A useful conservative starting mask is x=0–25% and y=50–100%, then validate real viewport crops; this is a design assumption, not a guaranteed LinkedIn UI measurement.

## Portrait: framing, lighting and identity

The standalone 800×800 headshot is color, not monochrome. A smooth dark-gray backdrop complements the banner while warm skin prevents the avatar from becoming visually flat. Hair starts at y≈53 (7%); head is centered near x=400; eyes around y=282 (35%); chin around y=562 (70%). Face/head width is about 350 px (44%); shoulders fill the lower third. The camera is near eye level, pose frontal, gaze direct, mouth closed with a very slight smile. Lighting is soft but directional from image-left/front, producing a darker image-right cheek and a warm dimensional face. The black shirt blends into the dark background at the edges. Retain enough midtone detail that a circular avatar does not become a dark disk.

## Banner and avatar together

Banner and avatar share black/charcoal neutrals and the same person, but use different treatments: large monochrome cutout in the banner and warm color portrait below. This repetition creates instant identity confirmation. The left-side avatar overlaps only negative space/glow. No proof or promise lies underneath it. The lime remains exclusively in the banner, so the face is the warm secondary accent. At small sizes, client logos and “AS SEEN IN” copy become weak; the two-line promise and face should remain the priority.

## Headline and positioning

Exact scraped headline:

> AI Search & SEO | Tech founders & marketing leaders hire us to grow sales with Search | 223+ companies helped | Founder & CEO, Contact.so

The headline stacks category (“AI Search & SEO”), target buyers (tech founders and marketing leaders), outcome (sales), quantified experience (“223+ companies helped”), then founder/CEO role. It gives the banner's broad “what's next” message much-needed specificity. Separators make it scannable but the sentence is long; readers on narrow screens may only see the category and buyer. The numerical proof is an author claim, not independently audited here. A new subject's equivalent should use their own named operating cases and defined metrics, without borrowing the reference's customer count or substituting generic tenure alone.

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
