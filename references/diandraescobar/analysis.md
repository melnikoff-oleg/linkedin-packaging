# Diandra Escobar — reference breakdown

Source: [LinkedIn profile](https://www.linkedin.com/in/diandraescobar/), collected through Apify on 2026-11-06. Directly inspected `banner.jpg` (1400 × 349) and `portrait.png` (800 × 800). Pixel bounds and type specifications are visual estimates of the raster. Suggested font families are substitutes, not verified original fonts. Testimonials and counts below are transcribed observations, not independently validated claims.

## Banner: the composition

The banner is a miniature conversion page: proof on the left/middle, the founder speaking in the center-right, and the named offer at the far right. Its deep near-black teal field contains soft luminous circular/orb-like gradients and a faint grain. The lighting creates depth while leaving text zones dark. A white `TE` mark at upper left establishes the offer identity without consuming meaningful space.

| Element | Approximate source-pixel bounds | Normalized bounds (x, y, width, height) | Purpose |
|---|---:|---|---|
| TE mark | 40, 39, 71, 43 | .029, .112, .051, .123 | Small brand cue |
| Clear proof cards | x289–806, y31–309 | .206, .089, .369, .797 | Staggered evidence collage |
| Speaker cutout | 711, 12, 286, 337 | .508, .034, .204, .966 | Human authority and motion |
| Offer title | 1051, 38, 247, 173 | .751, .109, .176, .496 | Main readable message at right |
| CTA | 1062, 237, 228, 23 | .759, .679, .163, .066 | Join instruction |
| Member avatars | 1062, 274, 288, 26 | .759, .785, .206, .074 | Social proof below CTA |

Exact title is `The / LinkedIn / Engine`. `LinkedIn` and `Engine` have teal rectangular underline/highlight bands behind their bottom portions. CTA reads `Join my skool community`; `skool` is bold. The avatar row ends with `+100`.

Readable message-card content includes `Win!!! generated 2 inbound leads with a single post`, `Got invited for a podcast` followed by microphone/megaphone symbols, `A discovery (sales) call booked from my LinkedIn feed!!!`, `Eyes from global brands on my LinkedIn newsletter - all inbound`, and a partially visible lower message beginning `Now I am daily getting inbound from tech`. Other cards are blurred or obscured intentionally. They should not be treated as complete transcripts. Each legible card includes a tiny avatar, name, metadata and message, giving it the visual grammar of an authentic community screenshot.

## Typography, spacing and layering

The title is a heavy neo-grotesque sans, visually close to Helvetica/Arial Bold or a slightly more geometric equivalent. Apparent size is roughly 60–63 px; line height about 59–62 px; tracking slightly tight, approximately -1 to -1.8 px. The title is deliberately stacked in a narrow column and its left edge is fixed. Recreating it as one long line would destroy this identity.

CTA text is about 19 px, light/regular weight except the product name. Message body is about 13–14 px; metadata 5–7 px; corner radius 11–14 px; pale gray borders roughly 2–3 px. These tiny cards are proof texture at normal display size, not content that every viewer is expected to read. Their near-white surfaces carry the strongest luminance peaks outside the headline, but perspective, blur and the speaker occlusion keep them subordinate.

The foreground cutout is sharp around face and microphone; the bottom edge is cropped by the frame. It overlaps the proof collage, suggesting the person is the engine behind those results. Leftmost lower quarter is mostly dark atmosphere; the nearest proof card begins around x408, so desktop profile overlap affects little essential information. A low card may still be affected on wider mobile portrait masks.

Sampled background is `#012324`–`#012E31`, with black-green shadows. White title has strong contrast. Teal highlights are approximately `#48A2A4` but vary under antialiasing. The source has a subtle left glow and a brighter far-right arc, rather than a simple flat linear gradient.

## Portrait

The smiling face is large, eye line roughly y282–300 (35–38%). Top of hair begins around y32 (4%). Chin is near y519 (65%), leaving enough shoulders to read as a portrait. The head is tilted slightly, giving warmth and energy. Direct eye contact and a broad natural smile contrast with the concentrated speaking expression in the banner.

A dark saturated teal background matches the banner's hue while being a little brighter. Long dark hair separates through highlights, and the white top creates a clean light base. Lighting is soft, frontal and slightly above/camera-left, with bright eyes and mild shadows. The cutout has a tidy but not mechanically sharp hair boundary. Preserve flyaways and natural texture when adapting, rather than making a helmet-like silhouette. Source PNG has some partially transparent edge/background pixels; flatten to the intended teal for predictable output.

## Combined effect and headline

The pair creates both friendliness (profile portrait) and capability (stage/speaker image). Repetition of teal ties them together; repeated appearances of the same subject are purposeful and at different scales. The headline underneath supplies the broader business context missing from a single offer banner.

Exact saved headline:

> Building content engines across LinkedIn, YouTube & newsletters | Founder, Distinctiva.io → we grow brands through organic content | Speaker

It opens with a mechanism, names distribution channels, identifies the business and outcome, and closes with a visible authority role. The arrow supplies conversational emphasis. `Content engines` and `The LinkedIn Engine` reinforce each other. The potential weakness is offer fragmentation: three channels and an agency in the headline versus a single-channel community in the banner. The branded system and repeated “engine” metaphor keep that manageable.

## Quality gates

- Avoid packing essential text into tiny cards; treat them as short scannable supporting content.
- Keep white cards behind, rather than across, the main portrait face.
- Preserve the 3-line title, narrow right column, and generous right margin (~50–100 px source scale).
- Do not fabricate customer feedback, community metrics or speaking history.
- Verify on mobile that the offer title remains readable and the left profile crop hides only atmosphere.

**Specificity check:** Cover the name and portrait. If most people in the same industry could use the remaining text unchanged, revise the case, company, metric or distinctive detail. Check the combined profile, not just each asset. Logos must preserve the true relationship; approximate figures and their definitions must remain intact.

## Applying this reference

Use only the new subject's supported facts, photographs and authentic marks. Preserve the original slot geometry and hierarchy; leave unsupported proof empty. The renderer requires explicit `reference_content`. See the [design system](../../docs/design-system.md) and [reference fidelity guide](../../docs/reference-fidelity.md).
