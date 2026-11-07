# Photographic assets

Use a real portrait of the subject. Preserve age, face structure, hairline, glasses and facial hair. Generated edits require visual inspection; a provider prompt cannot guarantee likeness.

Clare, Adrian, Chris, Charlie and Liam use only the close avatar. Diandra, Lara, Matt, Rob and Jake additionally require a different wider banner photograph with a distinct pose/frame. A duplicate, resized or recolored avatar is not a substitute.

The style registry and `linkedin_pack/visual_assets.py` contain the current portrait/banner prompt guidance. `create` can generate the separate shot and remove its background. `render` is offline and requires an already transparent banner cutout when that layout uses one.

You may supply your own background with `--background path/to/image.png` for layouts that support it. Historical generated backgrounds and source-person photo archives are not bundled. Use assets you are authorized to use and review the output alongside the saved composition reference.
