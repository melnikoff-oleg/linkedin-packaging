# Adrian Kuleszo — reference breakdown

Source: [LinkedIn profile](https://www.linkedin.com/in/adrian-kul/), collected through Apify on 2026-11-06. Directly inspected `banner.jpg` (1400 × 350) and `portrait.png` (800 × 800). Measurements are approximate source-pixel estimates. Font suggestions are substitutes rather than a verified font identification. Company/client names in the source headline are observed claims, not independent verification.

## Banner structure and visual intent

This is an exercise in restraint. The field is almost entirely white, with extremely pale, large, rounded geometric contours in the upper-right region. A small black abstract mark sits around the horizontal center, and a single line of black text sits toward the lower-right. No person, proof logos, badges, colored accents, CTA, decorative icons or additional subtitle are present.

| Element | Approximate source-pixel bounds | Normalized bounds (x, y, width, height) | Treatment |
|---|---:|---|---|
| White field | 0, 0, 1400, 350 | 0, 0, 1, 1 | Nearly pure white with faint border/shading |
| Pale geometry | x640–1400, y0–253 | .457, 0, .543, .723 | Very low-contrast soft rounded/extruded contours |
| Black mark | 677, 96, 48, 42 | .484, .274, .034, .120 | Compact circular/half-disc geometry, soft shadow |
| Service statement | 677, 282, 538, 24 | .484, .806, .384, .069 | One line, black medium/bold sans |

Exact visible statement: `Design & development partner for funded startups`. It is left-aligned with the small mark but separated by roughly 145 px of empty vertical space. That shared left edge is the hidden grid. The right margin is about 185 px (13.2%), so the sentence does not feel jammed into the corner. The empty left region supports profile-photo overlap with minimal risk.

The black mark resembles stacked/overlapped discs or a bowl-like smile. Its precise brand meaning is not knowable from the image alone. It must not be copied as a generic icon for a new person. In adaptation, a simple original monogram or no mark is safer and semantically cleaner.

## Type, spacing and contrast

The line appears to use a straightforward modern sans such as Inter or Helvetica/Arial, around 23–25 px at medium/bold weight, line height near 28 px, with neutral or mildly tight tracking (-0.3 to -0.5 px). There is only one typographic level. Its modest scale makes the large empty field feel deliberate and confident. A full-size headline would change the identity of this reference significantly.

The principal palette is white `#FFFFFF`, pale gray roughly `#FAFAFA`, and black. The decorative relief is often only a few RGB values away from white, so it nearly disappears at small scale. That is intentional; it should not be intensified into a visible noisy background. Black on white is highly legible at full resolution, but the small physical text size limits phone readability. The absence of contrast in the geometry makes the black mark and sentence the only crisp visual objects.

## Portrait

The supplied PNG is already a circular cutout on transparent corners; the black corners seen in some viewers are transparency, not a black square background. Alpha inspection confirms corner pixels have alpha 0. Inside the circle the background is near-white/light gray. The person wears a black cap and black crew-neck shirt, echoing the banner's black/white palette. There is a small red embroidered emblem on the cap; it is an incidental clothing detail, not a banner accent to replicate.

The head is turned slightly and tilted, with a natural smile showing teeth. Top of cap is around y74 (9%). Eyes are around y282 (35%); chin around y523 (65%). The frame includes substantial shoulders, cropped into the circle at the bottom. Lighting is soft, fairly frontal and warm, with modest shadow under the cap brim and face. Skin texture and beard detail remain visible. It reads as approachable founder photography rather than a formal executive studio portrait.

## Combined system and headline

The circular black shirt/cap silhouette creates the dense visual mass that the white banner intentionally lacks. The portrait anchors the left; the tiny banner mark and lower-right sentence anchor the right. The head does not compete with a large banner face. Monochrome makes the pair very coherent while leaving skin color as the primary warmth.

Exact saved headline:

> Co-founder of DesignMe™ | Product partners for tech startups & enterprises | Clients include: Seamless.AI, GoHighLevel, N3XT, Ballogy, and 100+ more

The headline supplies nearly all the authority and specificity: role/company, audience, category, then named clients and volume. The banner narrows the audience to funded startups, while the headline expands it to enterprises. This is a useful division of labor when the person has strong recognizable clients, though it is less effective if those names mean little to the visitor. The exact client list is not reusable.

## Quality gates

- Flatten the target portrait to a normal square image before upload; LinkedIn supplies the circular crop.
- Do not accidentally render transparent corners as black in the final preview.
- Keep the background geometry intentionally faint and inspect at both full and small sizes.
- Ensure the single sentence remains outside the avatar overlap area and is not clipped on the right.
- Preserve simplicity; the quality depends on proportion, alignment and restraint, not on adding more elements.

**Specificity check:** Cover the name and portrait. If most people in the same industry could use the remaining text unchanged, revise the case, company, metric or distinctive detail. Check the combined profile, not just each asset. Logos must preserve the true relationship; approximate figures and their definitions must remain intact.

## Applying this reference

Use only the new subject's supported facts, photographs and authentic marks. Preserve the original slot geometry and hierarchy; leave unsupported proof empty. The renderer requires explicit `reference_content`. See the [design system](../../docs/design-system.md) and [reference fidelity guide](../../docs/reference-fidelity.md).
