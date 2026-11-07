# Chris Donnelly — visual reference analysis

Source: https://www.linkedin.com/in/donnellychris/  
Local evidence: `banner.jpg`, `portrait.png`, `profile.json`, `headline.txt`. The original files were visually inspected individually. Banner source is **1400×349**; portrait is **800×800**. Capture: 6 November 2026. Bounds, font sizes and spacing below are visual estimates from the raster, not recovered editable design data; exact font family cannot be proved from these images.

## Banner decomposition

| Element | Bounds in source pixels (x, y, w, h) | Normalized bounds | Observation |
|---|---|---|---|
| Background | (0, 0, 1400, 349) | [0.0, 0.0, 1.0, 1.0] | Full orange field; no border; a white dotted globe is masked by the bottom edge. |
| Searchable logo | (70, 60, 230, 36) | [0.05, 0.1719, 0.1643, 0.1032] | White symbol and custom wordmark. Brand marker, not a credibility endorsement. |
| AI marks | (419, 61, 414, 120) | [0.2993, 0.1748, 0.2957, 0.3438] | OpenAI knot, radiating asterisk, four-point diamond, each white; evenly spaced across upper middle. |
| Main statement | (855, 55, 470, 139) | [0.6107, 0.1576, 0.3357, 0.3983] | “Drive revenue” / “from AI Search”; two right-aligned lines. |
| CTA pill | (417, 236, 572, 60) | [0.2979, 0.6762, 0.4086, 0.1719] | “Get started for free via my featured section!” plus circled down arrow; peach translucent fill and thin light edge. |
| Award strip | (1074, 232, 250, 66) | [0.7671, 0.6648, 0.1786, 0.1891] | Four small G2-style “High Performer” badges; tiny category text is not reliably readable at this size. |

The uninterrupted orange makes the whole profile recognizable before any wording is read. The image has two simultaneous structures: a centered cluster of AI marks/globe and a right-aligned revenue promise. The top-left wordmark supplies origin, while the eye moves to the much larger white promise, then to the peach CTA capsule. The badge strip sits beyond the capsule on the right and supplies a secondary proof signal. There is no person cutout in this banner; the profile portrait supplies the human element.

The white globe is a dotted/halftone hemisphere rather than a solid illustration. Its approximate extents are x=137–1167, y=18–349. Dots vary in density and visibility to imply curvature; this texture fills empty space without competing with the clean white silhouettes. Its brightest/busiest region overlaps the middle marks and capsule but does not materially cross the two-line message. A recreation should use a deterministic SVG dot field or licensed equivalent, not an uncredited copy of the entire reference image.

Typography is an unverified contemporary grotesk, visually close to Inter/Helvetica. Main type is roughly 70–74 source px, medium weight 500–600, line box around 72 px, tracking about −2 to −3 px. The slogan's second line is slightly wider and anchors to the same right edge around x=1323, leaving a 77 px right margin (5.5%). CTA type is about 26 px, regular, with ample horizontal padding (~22 px). Main headline top margin is 54–61 px, and the top-level logo uses roughly 38 px lettering. G2 labels are highly compressed: they communicate the badge shape at small display size more than their fine print.

### Color and contrast

Working palette: background #FE4D00, text #FFFFFF, accent #FFFFFF, muted #FFE2CA, portrait_background #FF5000. Base/banner accent colors are approximations sampled from the raster; compression, gradients and antialiasing create nearby values. Use these as reconstruction tokens, not official brand standards. The large type relies on white against saturated orange; this is visually striking but has lower luminance contrast than white on navy/black, so do not use tiny white body text on the orange. Keep important type away from the lower-left overlap zone. A useful conservative starting mask is x=0–25% and y=50–100%, then validate real viewport crops; this is a design assumption, not a guaranteed LinkedIn UI measurement.

## Portrait: framing, lighting and identity

The 800×800 portrait is a clean cutout against essentially flat orange, matching the banner's saturated hue. Hair begins about y=57 (7% top margin); chin is around y=546 (68%); shoulders extend beyond both bottom corners. The head spans roughly x=224–579 (44% of the frame), while the chest fills the bottom third. The face is nearly frontal with a slight angle, direct eye contact, and a broad natural smile. Black crew-neck clothing reduces competition with the face. Light is broad and soft, with gentle shadow on the image-right side, visible skin texture, and no dramatic rim light. The eyes sit around y=285 (36%). This crop is close enough for recognition at avatar size while the hair remains inside the circular crop. The orange edge treatment around hair is relatively crisp; avoid reproducing any overly hard mask or halo.

## Banner and avatar together

Matching orange fields make the avatar feel like an extension of the banner. At typical desktop placement, the overlapping avatar covers a quiet area of the globe at bottom-left, not the wordmark or primary copy. The wordmark's y≈60 location keeps it above the usual overlap. The portrait's black shirt introduces a grounding neutral below an otherwise intense orange/white block. Because the composition has meaningful elements across most of the width, verify small/mobile crops: the right message should remain intact, and AI marks/badges can become secondary rather than forcing all of them into a narrow view.

## Headline and positioning

Exact scraped headline:

> Co Founder of Searchable.com | Follow for posts on Business, Marketing, Personal Brand & AI

The headline opens with an explicit role and associated product (“Co Founder of Searchable.com”), then offers a follow reason organized as topic categories. The banner promises one concrete commercial outcome, while the headline broadens the content proposition. “Follow for posts” is a content CTA, not a client-service claim. Its strength is clarity and brand continuity; its limitation is that the four broad topics are less differentiated than the banner's AI-search promise. Do not transfer the cofounder/product claim to another person.

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
