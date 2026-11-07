# Public release checks

Use a separate clean source checkout for publication. Keep live credentials in ignored `.env` or environment variables. A local project export is broader than a public source release: inspect its assets and scan it independently before sharing.

Run the offline test suite:

```bash
.venv/bin/python -m unittest discover -s tests -q
```

Scan the public working files against all known local key values, including credentials shadowed by environment variables. Point `--credentials` at a private credentials file or its containing folder; do not pass key values:

```bash
.venv/bin/python scripts/check_public_release.py --credentials /path/to/private/working-folder
```

After reviewing and staging the intended files, scan the **exact complete Git index**:

```bash
.venv/bin/python scripts/check_public_release.py --staged --credentials /path/to/private/working-folder
```

Use repeated `--credentials` options for multiple sources. The scanner reads every relevant assignment from `api_keys*` and `.env*` files, excluding `.env.example`, and matching current environment variables without precedence-based replacement. It checks raw, Base64, URL-encoded and fully percent-encoded known values, common token/private-key patterns, suspicious long credential assignments, and nested ZIP/gzip contents. It reports filenames, categories and aggregate counts, never matched secret values. An incomplete or empty scan fails.

Working-file mode excludes local configuration, install/cache directories and generated output. Index mode checks everything staged, including accidentally staged ignored files. Review the staged file list as well: automated pattern matching cannot identify every possible secret or data-ownership issue.

Do not publish commercial font files or HTML that embeds them. The public example gallery uses final raster outputs. Raw public-profile datasets, website tracking captures, private source dossiers, `.env` backups and provider caches belong outside the public source tree. See [third-party notices](../THIRD_PARTY.md).

`build_reference_pack.py` and related authoring scripts are retained because they are useful development helpers and are covered by synthetic tests. Their historical calibration archives are not included. The ordinary CLI does not need those archives.
