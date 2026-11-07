# Clare Kitching — reference breakdown

Source: [LinkedIn profile](https://www.linkedin.com/in/clarekitching/), collected through Apify on 2026-11-06. Inspect `banner.jpg` (1400 × 349) and `portrait.png` (800 × 800) alongside this document. The image observations below are from direct visual inspection. Coordinates and type measurements are approximate measurements of this raster, not recovered design-file properties. Font names are reproduction candidates, not verified identifications. Statements printed in this reference are observed claims, not independently verified credentials.

## Banner: the composition

This is a branded editorial system, with a particularly effective contrast between a disciplined grid and expressive type. A deep petrol field occupies almost the entire frame. A faint square grid sits behind the content; its roughly 71 px spacing provides structure without needing to be read. Several cells have a slightly lighter fill. Fine grain prevents the flat dark background from looking sterile.

The banner separates into three areas: the company mark at upper left; the message in the right half; the credibility footer at lower right. The lower-left region contains no meaningful text. It is therefore robust to the desktop profile-photo overlap. The huge left-hand void is intentional balance, not missing content.

| Element | Approximate bounds in source px | Normalized bounds (x, y, width, height) | Treatment |
|---|---:|---|---|
| Company wordmark | 49, 40, 208, 43 | .035, .115, .149, .123 | Peach symbol, white lowercase `cambiq`, small pink accent over the i |
| Headline first line | 676, 38, 547, 50 | .483, .109, .391, .143 | White high-contrast serif, `Build AI Capability that` |
| Highlight line | 669, 96, 514, 56 | .478, .275, .367, .160 | Pink rectangular slab; very dark bold italic serif, `keeps getting stronger` |
| Connecting elbow | 714, 161, 70, 40 | .510, .461, .050, .115 | Thin pink L-shaped line, no arrowhead |
| Supporting copy | 800, 164, 365, 70 | .571, .470, .261, .201 | White sans, two lines; final phrase peach and bold |
| Credibility panel | 883, 274, 517, 75 | .631, .785, .369, .215 | Slightly lighter teal trapezoid; white logos |
| Footer stripes | 0, 323, 893, 26 | 0, .926, .638, .074 | Peach to x397, pale teal thereafter |

Visible supporting copy reads: `Follow for AI & data / insights you can act on.` The emphasis is on `you can act on.` The proof row contains QuantumBlack / AI by McKinsey, McKinsey & Company, and Wesfarmers marks, all in white. Their original brand colors are suppressed to preserve cohesion. The logo sizes are visually balanced by optical mass, not equal-width boxes.

## Typography, rhythm and contrast

The headline resembles a transitional editorial serif such as Georgia, Libre Baskerville or a similar family. Its 49–53 px apparent size and fairly tight line spacing create a compressed two-line block. The italic second line has real italic stroke modulation, rather than merely slanting an upright face. An approximate -0.5 to -1 px letter spacing would recreate the density. Use an actual italic font file when rendering.

Supporting copy is a clean humanist/geometric sans, roughly 32 px with 37–39 px baseline spacing and near-normal tracking. A 3 px connector is enough because the pink already has strong contrast. The logo label is around 43 px; small proof marks have an effective text height of 18–31 px.

Sampled dark background is around `#003337`–`#003940`; pink is approximately `#F39BE6`, peach `#FFC380`, pale teal `#7AC9C4`. White on petrol is highly legible; petrol text on pink is also strong. Pink is an attention device and a connection to the portrait, while peach distinguishes the actionable phrase and footer. The three accents work because their areas are small and assigned different roles. At phone size the support text and proof logos become secondary texture; the headline remains the first useful message.

## Portrait: crop, lighting and styling

The subject faces the camera, with a calm slight smile. Hair starts around y49 (6% of the image). The head occupies about 68% of the frame height; shoulders extend beyond the bottom and sides. Eye line is approximately y310 (39%). This is a tight head-and-shoulders crop, strong at the small circular sizes used in comments.

The background is a uniform vivid light pink, matching the banner highlight. Warm brown hair and a cream blazer separate well against it; the blazer also introduces a large light shape below the face. Lighting is broad and soft from camera-left/front, with gentle modeling on the other side of the face, no dramatic hard shadow, and visible natural skin texture. Hair-edge extraction is generally clean, though some loose strands and a little softness remain. The source PNG contains partial alpha at a few background pixels; flatten against the chosen pink when producing an upload-ready file so compositing behavior is predictable.

## Banner + portrait + headline

The portrait becomes the left-hand visual anchor, and the right-hand typography becomes the second anchor. Pink appears once in each, making the pair read as a system. The cream blazer against the dark banner provides separation even with LinkedIn's white circular rim. The upper-left company mark is outside the main desktop overlap but may be less comfortable under some mobile crops; do not regard its survival as guaranteed.

Exact saved headline:

> Building AI capability so businesses can back themselves | ex-McKinsey, ex-QuantumBlack | AI & data strategy, capability and governance | Executive advisor

The first clause states an organizational outcome with a memorable conversational phrase. Prior employers provide concise authority. Three service categories qualify the scope, and `Executive advisor` identifies the buying relationship. The banner is aspirational; the headline is explanatory. Its weakness is that the later service list is long and can be truncated on compact surfaces. The first clause is therefore doing useful work.

## Quality gates specific to this direction

- Check the italic line fits inside its pink rectangle with consistent 6–9 px source-scale padding.
- Compare white serif, supporting sans and logo proportions at a 790 px-wide desktop render and a narrow mobile preview.
- Confirm the portrait pink and banner pink are the same intended hue after export.
- Keep actual proof truthful and all essential content out of overlap/crop masks.
- Preserve hierarchy: statement first, actionable support second, credentials third.

**Specificity check:** Cover the name and portrait. If most people in the same industry could use the remaining text unchanged, revise the case, company, metric or distinctive detail. Check the combined profile, not just each asset. Logos must preserve the true relationship; approximate figures and their definitions must remain intact.

## Applying this reference

Use only the new subject's supported facts, photographs and authentic marks. Preserve the original slot geometry and hierarchy; leave unsupported proof empty. The renderer requires explicit `reference_content`. See the [design system](../../docs/design-system.md) and [reference fidelity guide](../../docs/reference-fidelity.md).
