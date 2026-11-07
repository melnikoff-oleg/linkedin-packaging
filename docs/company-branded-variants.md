# Company-branded variants

The generic `linkedin_pack/company_brand.py` support accepts a local brand bundle containing a manifest, authored CSS, provenance, and font files with SHA-256 hashes. Use your own appropriately licensed assets. A publicly downloadable font is not automatically licensed for redistribution.

A prepared brief may specify `"company_brand": {"manifest": "company-brand/brand.json"}`. Keep that bundle inside every output revision. Before rendering to a new destination, use `copy_brand_bundle(source_manifest, destination / "company-brand")` from `linkedin_pack.company_brand` to copy its declared dependencies. The CLI copies prepared logos but does not copy the brand bundle automatically. Offline rendering validates the local bundle; it does not scrape or guess a company's brand system.

A manifest has this shape (replace all example values):

```json
{
  "schema_version": 1,
  "id": "example-company",
  "name": "Example Company",
  "website": "https://example.com/",
  "palette": {"ink": "#123456", "paper": "#ffffff"},
  "fonts": [{
    "family": "Company Typeface",
    "path": "fonts/company.woff2",
    "sha256": "<full SHA-256 of your font file>",
    "weight": "400",
    "style": "normal",
    "source_url": "https://example.com/company.woff2"
  }],
  "typography": {"display_family": "Company Typeface", "body_family": "Company Typeface"},
  "stylesheet": "brand.css",
  "provenance": "provenance.json"
}
```

`brand.css` contains local color/font overrides. It cannot contain imported styles, `@font-face`, external URLs or unbound assets. The source geometry and clipping checks stay active. `provenance.json` is a JSON object recording the brand observations, source URLs, dates and limitations.

Rendered HTML embeds the supplied font bytes. Keep it private if the font license does not allow distribution. The public [branded examples](../examples/index.html) are finished raster images; their commercial fonts, editable branded HTML and private source dossiers are deliberately excluded.

Company branding requires rechecking text fit, actual font loading, logo contrast, portrait coordination and the assembled mobile view. No template text is automatically shrunk to accommodate a different typeface. The feature does not establish endorsement by the company.
