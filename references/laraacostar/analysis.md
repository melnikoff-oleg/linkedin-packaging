# Lara Acosta — reference breakdown

Source: [LinkedIn profile](https://www.linkedin.com/in/laraacostar/), collected through Apify on 2026-11-06. Based on direct inspection of `banner.jpg` (1400 × 350) and `portrait.jpg` (800 × 800). All geometric/type measurements are approximate source-raster estimates. Font suggestions are plausible replacements, not original-file identification. Banner credentials are observed claims and have not been independently validated.

## Banner structure and copy

This direction uses a black editorial stage, a warm halo behind a sharply extracted central portrait, and a large right-hand statement. The composition is asymmetrical: the lower-left third stays empty for LinkedIn's avatar, the person occupies the middle, and the message plus proof occupy the right. A small upper-left CTA uses otherwise empty space.

| Element | Approximate source-pixel bounds | Normalized bounds (x, y, width, height) | Treatment |
|---|---:|---|---|
| YouTube CTA | 37, 27, 350, 27 | .026, .077, .250, .077 | White bold sans, fire emoji, smaller gray parenthesis |
| Subject cutout | 457, 11, 282, 339 | .326, .031, .201, .969 | Black high-neck clothing, folded arms, frame-bottom crop |
| Main statement | 775, 58, 575, 87 | .554, .166, .411, .249 | Two dense lines, white/red sans |
| Credential row | 776, 176, 537, 28 | .554, .503, .384, .080 | Small icons and tracked uppercase labels |
| Proof footer | 739, 246, 661, 104 | .528, .703, .472, .297 | Dark charcoal/pixel texture, white marks |
| AS SEEN IN label | 540, 300, 104, 17 | .386, .857, .074, .049 | Tiny widely tracked white uppercase |

The headline is `Personal branding that moves / the needle online (and offline).` The phrases `that moves` and `the needle` are red, continuing a single highlighted thought across the line break. The upper-left instruction reads `Subscribe to my YouTube 🔥 (link below)`. Beneath the main claim are a UK-themed icon with `#1 UK FEMALE CREATOR`, then a gold wreath and `#1 LINKEDIN PROGRAMME`. These are the reference's claims and are not reusable proof for another person.

The bottom strip contains Forbes, AdAge, University of Exeter, and LinkedIn News marks in white. The `AS SEEN IN` label extends left of the strip over the clothing. The marks are not all the same size; each is sized to similar visual weight. A university mark under an `AS SEEN IN` grouping may be semantically ambiguous without additional context; adaptations should label affiliations accurately rather than copy this ambiguity.

## Background, fonts and hierarchy

Most of the frame is near black (`#000000` to `#141414`), with a soft rusty-red radial halo centered around the person's head/upper torso. The halo helps dark hair separate from the field and links the face to the red words. The bottom proof area has a subdued, blocky texture; it is visibly different from the smooth upper field without becoming a competing focal point.

Headline appears to be a heavy grotesque sans, similar to Inter/Helvetica Neue Bold. Approximate apparent size 43–46 px, line height 46–48 px, and letter spacing -1.6 to -2 px. Tight tracking and short line spacing make the statement feel firm and dense. Supporting labels are 12–13 px uppercase, roughly 3 px tracking, medium/bold weight. CTA is 21 px bold, with `(link below)` around 11 px regular. The horizontal gap from cutout shoulder to message is only ~35 px, making the person and statement a single composition.

The white text has excellent contrast against black. Red (`#D34833`-like) is lower-contrast than white but acceptable as large bold display text; it should not be reused for tiny body copy. The footer's white logos are legible at large sizes, but their details become decorative proof cues on mobile. This is intentionally a three-tier hierarchy: promise, authority labels, recognized marks.

## Portrait

The square profile image is a very close head-and-shoulders portrait. Top hair is around 28–35 px (4%). Eye line is around 329–345 px (41–43%). Chin near y622 (78%) means the face occupies more of the circular crop than the other references. Shoulders and a white sleeveless top appear at the bottom edges. Direct eye contact and a composed, neutral expression support the premium editorial feel.

The background is a warm orange-to-red gradient, about `#E78427` at the upper left and muted red toward the right. It translates the banner's small red accents into a broad color field. Dark hair separates strongly against it. Lighting is soft but directional enough to retain cheek and nose structure; natural skin texture remains visible. Hair has fine strands and slight flyaways, rather than an overly smooth cutout.

## Interaction with LinkedIn and headline

The profile portrait sits against the empty black lower-left zone and becomes a warm circular counterweight to the right-hand red/white text. The center cutout is far enough right not to collide with the desktop avatar. On mobile, the left CTA may be close to crop edges and may compete with the overlaid portrait; prioritize the main claim, not exact placement of every reference detail.

Exact saved headline:

> Entrepreneur and investor building businesses online | Forbes 30u30 | Helped 5,000+ people build their personal brands, go viral and land clients on LinkedIn.

It mixes identity, prestige credential, quantified scope and three outcomes. `Land clients` turns attention into commercial value. The banner concentrates the promise into “moves the needle”; the headline explains what that means. The long final clause may be truncated, but the beginning establishes role and credibility early. The numbers and credential are reference-specific and must never migrate to another profile.

## Quality gates

- Keep at least the lower-left 28% clear; place the target's face outside that overlap area.
- Confirm the accented phrase reads naturally across the line break.
- Use actual supported experience rather than media, award or audience claims from this reference.
- Inspect dark-hair edges against the halo and avoid heavy artificial skin smoothing.
- Check the portrait gradient and red banner accent remain cohesive after PNG export.

**Specificity check:** Cover the name and portrait. If most people in the same industry could use the remaining text unchanged, revise the case, company, metric or distinctive detail. Check the combined profile, not just each asset. Logos must preserve the true relationship; approximate figures and their definitions must remain intact.

## Applying this reference

Use only the new subject's supported facts, photographs and authentic marks. Preserve the original slot geometry and hierarchy; leave unsupported proof empty. The renderer requires explicit `reference_content`. See the [design system](../../docs/design-system.md) and [reference fidelity guide](../../docs/reference-fidelity.md).
