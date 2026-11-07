# Reference-faithful design system

The active task is close reproduction of each original reference, changing the subject's copy, authentic logos and photographs while preserving layout, sizing and visual hierarchy. Each original composition has its own type hierarchy and supporting detail scale.

The original rasters under `references/<slug>/` are the visual authority. Their analysis documents preserve source observations, while `REFERENCE_REGIONS` and the fixed CSS in `linkedin_pack/reference_group_a.py`, `_b.py` and `_c.py` record the measured reconstruction. [Reference fidelity](reference-fidelity.md) records the current comparison work. Matching a background color alone is insufficient.

## Canvas and review scale

Author at 1584×396 design pixels and export a 3168×792 PNG. The portrait export is 800×800. Neutral assembled review images are 792 px desktop and native 390 px mobile. The labeled `preview-mobile.png` is 780 px at 2× and must be displayed at 390 px for a mobile judgment.

Normalize the source banner to the same width as its adaptation before comparing. Inspect both full-resolution detail and actual assembled display size. A larger raster does not improve the physical reading size. Secondary proof labels deliberately retain the source's hierarchy; do not promise universal fine-print readability at 390 px. The primary message and normal-size profile headline must communicate the offer, factual attribution and necessary qualifications.

## Fixed layout, variable content

Each new brief declares `layout_mode: "reference-faithful"` and provides `reference_content` explicitly. The registry supplies a typed slot tree, fixed array counts, phrase-length budgets and style values. It does not inject another person's example facts into a new brief. `proof_cards` and `proof_points` remain empty in this mode; legacy banner fields are metadata, not hidden evidence.

Preserve source title lines, phrase density, type scale, position, support hierarchy, proof rhythm, logo locations, photo direction and negative space. Rewrite copy to fit. Do not change font size, add lines, move a block, collapse a collage into one card, add a footer to a sparse source, ellipsize or hide words to silence a check. Character counts guide drafting; actual glyph widths and screenshot comparison decide fit.

| Reference | Composition that must remain recognizable |
|---|---|
| Clare | Upper-left identity; right two-line serif/italic pink title; elbow and two-line support; angled three-mark footer; peach/teal bars |
| Diandra | Five staggered small evidence snippets; subtle blurred depth; separate center-right action photograph; narrow three-line title; small supporting identity row |
| Lara | Small upper-left intro; central separate portrait and warm halo; tight two-line right title with continuing red emphasis; two tracked icon labels; four-mark lower band |
| Matt | Broad scenic field; one upper serif sentence with highlighted phrase; far-right relaxed subject looking toward the copy; no added case card |
| Adrian | Pale architectural geometry; small monogram; one narrow lower sentence; extensive intentional whitespace |
| Chris | Orange field; left identity; central large mark grouping; right two-line headline; lower support and small credential cluster |
| Rob | Dark field and lime glow; two-line center-left title; short support; compact logo row; seated grayscale subject; small far-right credential area |
| Jake | Light field; central two-line headline with italic coral emphasis; long rounded logo capsule; separate right seated subject and orbit details |
| Charlie | Grid field; compact two-line left-middle message and single support line; overlapping horizontal identity cluster at right |
| Liam | Blue/gold engraving; upper-left identity; broad two-line right headline; separate compact badge; lower white-mark row |

Truth can require semantic substitutions: documented employers replace unsupported press logos; career facts replace fabricated testimonials; a true role label replaces an invented audience count. Preserve the visual role and placement, and describe the substitution accurately. Do not invent marks or people merely to reproduce a source count.

## Typography and spacing

Use the reference's hierarchy, not a global title/support minimum. Preserve its serif/sans contrast, genuine italic treatment, line-height, tracking and relative logo mass. Bundled font families approximate the original raster; they are not asserted to be the original design files. All fonts must be loaded before measurement and rasterization.

Inspect actual ink as well as bounding boxes. Colored highlights must clear preceding descenders and contain italic overhang. Adjacent title lines, support, photo silhouettes and logo bands must not collide accidentally. Use source-derived positions and intervals; there is no universal x540 content spine or universal margin that can replace them. A photographic or decorative bleed may be intentional, while clipped words are not.

Do not repair a text collision by shrinking the whole layout. First choose shorter truthful wording with similar original phrase length; then inspect actual glyph metrics. Correct a clear reconstruction error to restore the source's intended spacing. Final approval requires the equal-scale visual comparison, not just a passing coordinate threshold.

## Source-grounded proof and original marks

Keep the exact role, company/product, metric definition, direction, approximation and time window. A company award is not a personal award. Prior employment is not endorsement or press coverage. The full profile headline must remain meaningful without familiarity with the company names. Omit undefined metrics rather than assigning an invented unit.

Use original transparent marks with retained source pages/URLs, exact hashes and subject relationship. Preserve their aspect ratios; tint original alpha geometry when the reference uses monochrome marks. Do not redraw a logo, infer an official identity from a lookalike, or add individual white plates. A visible company label must match the asset identity; a subsidiary cannot be labeled with its parent's mark.

Unavailable or opaque marks leave their reserved slots empty and record an omission. A source-supported company name or role can occupy its existing textual slot. Do not turn missing assets into made-up logos. Available authentic assets should be used deliberately rather than omitted simply to simplify the design.

## Photograph roles and avatar treatment

The avatar is the close recognition image. In Diandra, Lara, Matt, Rob and Jake, a separate wider banner shot adds posture or context. The other five layouts have no banner person. Exact or perceptually near-identical photo reuse is rejected; two different files can still fail visual review if the pose feels repeated.

Match each original avatar's brightness, clothing contrast and backdrop, including Clare's pink/ivory, Diandra's emerald/white, Lara's orange-coral/white, Matt's tan/light outdoor treatment, Rob and Jake's color portraits on charcoal, and Liam's navy/gold engraving with blue layers. Preserve the real subject's face, age, glasses and hairline.

The banner shot must preserve the original's direction and broad silhouette: Matt looks viewer-left into the copy; Rob is seated and grayscale while his avatar stays in color; Jake uses a wider seated black-shirt pose. A clothing color may match the avatar when the reference calls for it, but the frame and pose must remain visibly distinct. Inspect anatomy, hands, shoulders, cutout edges and lighting in the assembled profile.

## Independent review and acceptance

Review all ten separately. A designer simulation receives original/output comparisons and assembled previews and judges fidelity without implementation arguments. A buyer simulation receives only neutral desktop/mobile profiles and a persona and judges offer, specificity, credibility, naturalness and material readability. Neither is a real prospect interview or an independent factual audit.

Acceptance is unproven until current rendered pixels, source evidence and review records establish it. Old approvals or a green test suite do not establish visual quality. Changed output invalidates prior image coverage. Runtime Kie reviews bind the current images, persona and review-prompt hashes. AI reviews are simulations and do not certify likeness, factual accuracy, or customer response.
