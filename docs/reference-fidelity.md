# Reference fidelity

Each layout is reconstructed from the original banner and portrait under `references/<style>/`. Its local `analysis.md` and `design.json` explain the source, and the renderer's `REFERENCE_REGIONS` and CSS define the implementation.

Preserve title lines, type hierarchy, phrase density, photo direction, logo placement and whitespace. Change the subject's identity and supported facts. Unsupported awards, logos and testimonials stay empty; an employer relationship is not an endorsement.

The normal CLI uses explicit `reference_content` slots. It never uses the example person's claims as a fallback. Rewrite phrases to fit the fixed slots rather than shrinking type or moving elements. The bundled OFL fonts are practical approximations of the source raster typography.

Compare original and output at equal banner size, then inspect the combined desktop and native 390 px mobile previews. The primary message and profile headline should communicate the offer; very small source-sized secondary text is not guaranteed to be comfortably readable on mobile.

Technical QA checks bounds, collisions, image roles, text clipping and declared slots. The separate AI buyer review checks the assembled first impression. Neither independently proves factual accuracy, identity fidelity, or real buyer response. See [the design system](design-system.md) and [CLI guide](cli.md).

The public [example gallery](../examples/index.html) contains completed raster demonstrations. Historical source dossiers and local review archives are excluded from this public release.
