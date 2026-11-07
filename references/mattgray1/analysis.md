# Matt Gray — reference breakdown

Source: [LinkedIn profile](https://www.linkedin.com/in/mattgray1/), collected through Apify on 2026-11-06. Directly inspected `banner.jpg` (1400 × 350) and `portrait.jpg` (800 × 800). Approximate bounds and type sizes refer to these rasters; font identity is not recoverable reliably from this image alone. Revenue figures are observed copy, not independently verified claims.

## Banner structure

This is the least “marketing layout” of the five examined here. An expansive alpine landscape fills the frame, with wooded slopes, a valley, distant pale peaks and open sky. A large person in black occupies the right side, looking upward and to the left. A single sentence across the upper-left/middle gives the commercial proposition. There is no logo row, no CTA, no badges, no cards and no subtitle.

| Element | Approximate source-pixel bounds | Normalized bounds (x, y, width, height) | Treatment |
|---|---:|---|---|
| Landscape | 0, 0, 1400, 350 | 0, 0, 1, 1 | Full bleed photograph, dark left woods, light right mountains |
| Main sentence | 138, 76, 817, 35 | .099, .217, .584, .100 | Thin/regular white serif, small lime emphasis |
| Person | 976, 49, 227, 301 | .697, .140, .162, .860 | Dark shirt and beanie, cropped at bottom |

Exact visible sentence: `The operating system behind 7 to 9-figure founder brands.` The words `operating system` are a lime/yellow-green. The remainder is white. It fits on one line and leaves a gap before the right-hand person. A scenic background is part of the communication: distance and scale are visual metaphors for successful founder freedom/ambition, but those interpretations are design inferences rather than facts about the person's lifestyle.

The forest on the left appears darkened, likely with an overlay or selective grading; the valley and right mountain retain more luminance. This creates a usable text field without a visible box. The far-left lower quarter can be covered by the LinkedIn avatar without losing content. Crucially, the sentence is high enough in the frame to survive that overlap, though at mobile scale it becomes very small.

## Typography, spacing and palette

The type resembles a classical editorial serif such as Georgia or a related old-style/transitional face. Apparent font size is roughly 34–36 px, normal/light weight, near-normal tracking, about 0 to -0.4 px. The baseline is around y103. A broad left margin (~138 px, 9.9%) makes the sentence look intentionally placed within the scenic composition rather than pasted against an edge.

The photographed greens are muted and natural: deep forest `#131C1B`, olive greens, pale stone and cool sky blue. The display accent is a bright lime close to `#C6DD61`; it is the only deliberately artificial color cue. Its brightness is sufficient over the dark woods, but a different scenic photograph would need contrast validation behind each word. No single color contrast ratio describes text over this varying photographic background.

Because the typography is light and the text is long, this composition privileges desktop calm over compact-screen readability. At a 400 px-wide banner, the sentence is only about 10 px high. A reproduction should retain its restraint while shortening the phrase or making the type modestly larger rather than blindly copying this weakness. The eye first notices the scene/person, then reads the sentence; the brand is conveyed through atmosphere as much as text.

## Portrait

The profile image is natural outdoor photography with a shallow-depth background. The subject is smiling, looking slightly off-camera to the right, with hair tied back and a beard. Hair begins around y58 (7%); eyes around y307 (38%); beard/chin reaches around y600 (75%). Brown/caramel crew-neck clothing fills the lower fifth. The head and shoulders occupy almost the whole width at the bottom.

Lighting appears to be soft available daylight, with gentle facial contrast rather than a studio key/rim setup. Background buildings and greenery are blurred enough to avoid recognizable distraction. The palette is warm brown clothing, gray/brown hair, muted green foliage and a cool pale sky/building field. Unlike the other references, it does not use a flat, brightly colored cutout background. Its credibility comes from looking relaxed and photographic.

## Combined composition and headline

The banner and avatar use different locations, clothing and hairstyles but share outdoors, natural light and a relaxed mood. The overlap places the close smiling face in front of a wide scenic view, offering both intimacy and scale. There is no attempt to force exact color matching. The coherence is photographic and emotional, rather than a strict brand palette.

Exact saved headline:

> The operating system behind 7 to 9-figure founder brands. Founder & CEO, Founder OS

This repeats the banner proposition almost verbatim, then names the company and role. Repetition supports recognition and avoids competing messages. It uses “operating system” as a positioning metaphor, and the revenue range signals a high-value audience. The weakness is that the concrete service remains implicit; a new visitor may need to investigate what the operating system includes. This is workable for an established brand but less suitable for a person who needs immediate clarity.

## Quality gates

- Inspect background detail behind every letter; do not approve readability from a solid-color contrast calculation.
- Keep landscape imagery high resolution and original, without another person's likeness or branded assets.
- Keep the composition calm, but make its short sentence a named case or specific audience/result; whitespace must not remove the evidence that makes the person distinctive.
- Check whether the small-screen sentence is actually legible; enlarge/shorten if needed.
- Retain photographic texture and believable outdoor light in the target portrait.

**Specificity check:** Cover the name and portrait. If most people in the same industry could use the remaining text unchanged, revise the case, company, metric or distinctive detail. Check the combined profile, not just each asset. Logos must preserve the true relationship; approximate figures and their definitions must remain intact.

## Applying this reference

Use only the new subject's supported facts, photographs and authentic marks. Preserve the original slot geometry and hierarchy; leave unsupported proof empty. The renderer requires explicit `reference_content`. See the [design system](../../docs/design-system.md) and [reference fidelity guide](../../docs/reference-fidelity.md).
