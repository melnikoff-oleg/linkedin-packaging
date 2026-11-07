# Brief compatibility and renderer selection

## Reference-faithful mode is checked first

New generation sets `layout_mode: "reference-faithful"` and supplies the selected template's complete `reference_content` tree explicitly. This branch takes precedence over the presence of `proof_cards`. The tree's object keys, field types and array counts must match the registry; another person's fixture is never a fallback. `proof_cards` and `proof_points` must both be empty.

Reference mode preserves the original layout, type sizes, phrase lengths, line counts and hierarchy. It does not apply the old universal 48 px support floor or one-proof-unit rule. Generated copy is checked against the slot budgets; rendered glyph fit and direct original/output comparison remain authoritative. Legacy `banner_title`, `banner_subtitle` and `cta` are metadata here and cannot supply hidden evidence for otherwise generic visible reference content.

`--website` can provide source evidence, but the reference palette stays fixed. `--use-website-colors` is rejected clearly before network/paid generation in reference mode, including prepared reference briefs. Empty unavailable logo slots retain geometry; a nonempty key must identify a subject-supported original asset. Changed output requires fresh review and cannot inherit a historical acceptance.

## Existing evidence-card and legacy briefs remain supported

When reference mode is absent, an explicit `proof_cards` field selects the existing evidence layout, including an empty list. An empty list does not select old typography or fabricate proof. These briefs must set `proof_points` to `[]`; supported facts belong in their actual visible title, subtitle or cards. The validator rejects hidden legacy proof lists, and source-retention checks follow the same visible-field routing.

Older briefs without `proof_cards` remain readable through the legacy path. The evidence/legacy branches retain their existing 48 px support and 56 px headline checks, glyph/highlight clearance, bounds and avatar exclusions. Those historical constraints apply to those branches; they do not override reference mode. Missing markup or a failed layout does not obtain approval merely because the brief is old.

Prepared legacy briefs can still use an explicitly requested website palette with the existing contrast/provenance checks. Both foreground and accent require at least 4.5:1 contrast in that mode. No implicit website recoloring occurs for newly generated reference packages.

## Migration

To keep an old evidence layout, preserve its supported fields and existing routing; adding an explicit empty `proof_cards` array is the evidence-layout migration, not a reference reconstruction.

To move to a faithful reference, select a supported style, set `layout_mode: "reference-faithful"`, provide its complete explicit `reference_content` tree, clear both proof arrays and prepare its actual original logo assets. Rewrite copy to fit the original slots, preserving facts and qualifications rather than moving or resizing the layout. Source-check the visible fields, rerender, compare the original and assembled output, and obtain a new independent review. See [CLI usage](cli.md) and [the active design system](design-system.md).
