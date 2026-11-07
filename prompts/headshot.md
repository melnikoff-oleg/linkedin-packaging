# Identity-preserving headshot

Use case: identity-preserve.
Asset: square professional LinkedIn portrait.
Input image 1: the target person's actual supplied/scraped photograph, the sole identity source.
Reference style: the selected reference informs crop, light, palette and setting only.

This asset is the profile avatar, whose job is recognition in a small circle. It is not a banner photograph. Diandra, Lara, Matt, Rob and Jake require a separate waist-up or environmental banner shot; Clare, Adrian, Chris, Charlie and Liam have no person in the banner. Never reuse, enlarge, mirror or recolor this avatar to fill a banner slot.

Edit the supplied photograph of this same person. Preserve head shape, facial proportions, eye shape and spacing, nose, mouth, ears, hairline or baldness, hair color, age, facial hair, complexion, recognizable asymmetry and the same eyeglasses. Do not rejuvenate, reshape, slim, beautify into a different person, remove glasses, change ethnicity or add a new smile with invented teeth. Keep natural skin detail. Identity takes priority over polish.

Create a photorealistic professional head-and-shoulders portrait with a clean reference-aligned background, soft directional or diffused light, and natural color. Use target-appropriate simple clothing. Keep enough headroom for a circular crop; eyes should remain comfortably above the midpoint and shoulders visible. Preserve the source's expression unless a small natural adjustment is requested. Remove distracting event props only when they are unrelated to the portrait. One person; no text, watermark, invented jewelry, logos or additional objects.

Generate using the configured Kie image-edit provider and its supplied source image. Do not send a reference person's portrait as the target identity. Save the original provider output before producing the 800×800 delivery version. Reuse the saved job on timeout; do not submit a duplicate paid request blindly.

When a banner shot is required, generate it separately from the person's real identity source or use a supplied distinct photograph. Give it a new camera distance, body posture, gaze and clothing, retaining the same actual person. Keep the body and natural hand positions visible instead of repeating the avatar's head tilt and close framing. Its background-only cutout is another operation: preserve that existing photograph exactly while extracting genuine alpha, without restyling the face or pose. The image-pair hash and perceptual guard can detect near-identical source reuse; it cannot certify distinct pose, likeness or good composition.

Compare source and result side by side at full size and avatar size. Specifically check glasses geometry/reflections, hairline, ears, eyelids, nose, smile, jawline, age, skin texture, shoulder anatomy, edge halos and circle crop. Also inspect the avatar and any banner photograph in the assembled desktop and mobile profile. Reject the same-pose-twice effect even when each asset looks polished on its own; compare expression, gaze, body framing, wardrobe and face scale. If likeness fails, reject the result, make one targeted prompt adjustment and regenerate deliberately. A model cannot certify identity preservation. Leave an honest review status, do not imply a human has already approved likeness, and keep the original available as an alternative if generation remains less faithful.
