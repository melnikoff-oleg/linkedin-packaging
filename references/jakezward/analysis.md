# Jake Ward — visual reference analysis

Source: https://www.linkedin.com/in/jakezward/  
Local evidence: `banner.jpg`, `portrait.jpg`, `profile.json`, `headline.txt`. The original files were visually inspected individually. Banner source is **1400×350**; portrait is **800×800**. Capture: 6 November 2026. Bounds, font sizes and spacing below are visual estimates from the raster, not recovered editable design data; exact font family cannot be proved from these images.

## Banner decomposition

| Element | Bounds in source pixels (x, y, w, h) | Normalized bounds | Observation |
|---|---|---|---|
| Background | (0, 0, 1400, 350) | [0.0, 0.0, 1.0, 1.0] | Warm white field; a peach/coral radial glow is localized behind the right portrait. |
| Known wordmark | (37, 35, 128, 31) | [0.0264, 0.1, 0.0914, 0.0886] | Lowercase black “known” with an elevated coral-ring “o”. |
| Main statement | (394, 88, 553, 102) | [0.2814, 0.2514, 0.395, 0.2914] | “Be known everywhere” / “your customers search”; “everywhere” is coral italic. |
| Proof capsule | (387, 231, 740, 62) | [0.2764, 0.66, 0.5286, 0.1771] | “SEEN IN” followed by Forbes, TechCrunch, Inc., Business Insider, Y Combinator marks in gray. |
| Banner person | (1090, 20, 282, 330) | [0.7786, 0.0571, 0.2014, 0.9429] | Warm full-color seated/upper-body cutout, smiling, black crew-neck; overlaps right portion of the capsule. |
| Orbit system | (956, 40, 444, 310) | [0.6829, 0.1143, 0.3171, 0.8857] | Fine coral dotted curves with small white circular AI/search icon disks, clipped by right/bottom edges. |

The main statement is compact, exceptionally bold, and phrased entirely from the customer's point of view. A single italic coral word adds speed and emphasis without introducing a second font category. It visually answers “where?” while the black second line clarifies the audience context. The eye then moves to the smiling person and supporting platform orbit. The small brand marker at top-left leaves the avatar zone quiet.

Font is an unverified neo-grotesk/geometric sans; Inter ExtraBold or a similarly compact grotesk is a workable substitute. Main source size is roughly 51–54 px, weight 750–800, line-height about 51 px, tracking −1.5 to −2 px. “everywhere” shares the scale but uses a true italic/slanted design and coral fill. Left text edge is x≈394, top y≈89; line two ends around x=948. Margins are asymmetrical because the right person replaces ordinary whitespace. The proof capsule begins almost directly under the headline (x≈387) with a 38–41 px gap. Its 60 px height, 30 px radius, thin gray border and faint internal gradient are deliberately quieter than the headline.

The orbital arcs are mostly on the right quarter, not a full-frame motif. Their dotted strokes are hairline (~1 px), and the icon disks are ~38 px across with subtle shadows. Visible marks include OpenAI, Google, a radiating asterisk and a four-color diamond; these are distribution platforms, not customer endorsements. At the bottom, a small disk is cut by the canvas edge, suggesting a larger system. The human cutout sits in front of both arcs and proof strip, introducing depth through overlap rather than excessive shadows.

### Color and contrast

Working palette: background #FAFAF8, text #101111, accent #FF4A28, muted #74777B, portrait_background #62635F. Base/banner accent colors are approximations sampled from the raster; compression, gradients and antialiasing create nearby values. Use these as reconstruction tokens, not official brand standards. The large type relies on very high light/dark contrast for the primary message, while secondary textures and small proof are intentionally quieter. Keep important type away from the lower-left overlap zone. A useful conservative starting mask is x=0–25% and y=50–100%, then validate real viewport crops; this is a design assumption, not a guaranteed LinkedIn UI measurement.

## Portrait: framing, lighting and identity

The 800×800 portrait is a tight head-and-shoulders crop with neutral textured gray background and black shirt. Hair begins y≈26 (3% margin); eyes y≈353 (44%); chin y≈662 (83%). The face is large, roughly x=191–616 (53% width), with shoulders only in the bottom quarter. Direct eye contact and an open smile make the technical offer personable. Soft frontal light keeps both eyes clear and leaves natural skin texture; background is slightly darker and warmer on the right. This is the closest crop among these five references, so recognition is strong at tiny avatar sizes. A strict circular crop can approach the hair/shoulder edges; keep a few percent more headroom in the new version.

## Banner and avatar together

The banner uses a medium upper-body cutout while the avatar gives a much tighter facial view. This two-scale repetition works because the clothes and expression are consistent. Gray avatar background remains neutral against warm white and coral; the subject's warm skin echoes the peach glow without requiring a coral backdrop. The left quarter of the banner has no important bottom content. A mobile view may lose some orbit disks and press logos; that is acceptable provided the promise survives. The proof capsule's extreme right is intentionally obscured by the torso, making it essential not to put the only proof item there.

## Headline and positioning

Exact scraped headline:

> Growing B2B SaaS with SEO, AI search + LinkedIn. Acquired 175,000+ users for my SaaS. Ran SEO experiments that even Google’s CEO has seen.

The opening states who and how: B2B SaaS growth through SEO, AI search and LinkedIn. Two following sentences supply concrete achievement and a memorable authority anecdote. The first-person shift creates personality and makes the result claim attributable. The banner is a broad dream outcome, the headline supplies mechanism and evidence. The “175,000+ users” and Google CEO anecdote are reference-specific statements; do not reuse them or convert them into implied proof for another person.

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
