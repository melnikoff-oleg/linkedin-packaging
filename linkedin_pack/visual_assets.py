"""Separate photo roles and conservative reuse detection.

These checks identify reused source pixels. They do not assess identity, pose
quality or whether a combined profile feels credible; that requires blind review.
"""
from __future__ import annotations
import hashlib
import math
import re
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter

BANNER_PHOTO_STYLES=frozenset({
    'diandraescobar','laraacostar','mattgray1','rob-hoffman-ceo','jakezward',
})

_CUTOUT_PROMPT='''Remove only the background from the supplied photograph and output the exact same subject as a clean transparent PNG cutout. Preserve the person, entire pose, camera angle, body proportions, facial details, glasses, hair, facial hair, clothes, hands, chair if present, and lighting EXACTLY. Do not redraw, restyle, beautify, change gaze, move hands or crop body. Background must be truly transparent alpha, not a checkerboard, white, black or any solid color. No added shadows, glow or outline. Keep the full subject silhouette and fine natural edges.'''


def banner_cutout_prompt():
    return _CUTOUT_PROMPT


def has_transparent_background(path):
    """Require usable subject alpha, not an opaque checkerboard or token clear pixel."""
    try:
        with Image.open(path) as image:
            if 'A' not in image.getbands() and 'transparency' not in image.info:
                return False
            alpha=image.convert('RGBA').getchannel('A')
            histogram=alpha.histogram();count=image.width*image.height
            # Some valid provider PNGs top out at alpha 254 after export.
            # Require substantial near-opaque subject area, not an exact 255 pixel.
            return histogram[0]/count>=.05 and sum(histogram[250:])/count>=.10
    except (OSError,ValueError):
        raise ValueError('Banner photograph must be a readable image file.') from None

_DIRECTIONS={
    'diandraescobar': 'Candid waist-up working portrait, body turned three-quarters, one visible natural hand gesture as if explaining an idea to an off-camera colleague. Dark teal studio environment, soft teal background light, black overshirt. Gaze toward the right, away from camera. No microphone, stage, event, audience or testimonial props.',
    'laraacostar': 'Waist-up editorial portrait. Body turned three-quarters toward the right, forearms comfortably crossed at waist level, composed confident expression, gaze toward the camera. A charcoal blazer over a black crew-neck. Near-black background with restrained burnt-orange separation light. Keep both forearms visible and anatomically natural.',
    'mattgray1': 'Environmental head-through-hips portrait, standing relaxed in a mountain landscape. Plain fitted black short-sleeved T-shirt, no jacket or overshirt. Body angled slightly toward the left, both hands naturally resting in trouser pockets, chin gently raised and gaze upward toward viewer-LEFT, into the banner copy, with a relaxed smile. Soft open-shade natural daylight. Preserve a broad clean torso silhouette for a far-right banner crop.',
    'rob-hoffman-ceo': 'Waist-up monochrome editorial portrait, seated facing the camera and leaning slightly forward, forearms relaxed down toward the thighs. Plain fitted black short-sleeved T-shirt and dark trousers, no blazer or overshirt. Calm direct gaze, restrained natural smile, visible upper arms and relaxed shoulders. Nearly black studio backdrop and soft frontal lighting; true black-and-white skin, no colored light.',
    'jakezward': 'Waist-up seated editorial portrait facing the camera, leaning slightly forward with forearms resting on thighs and hands loosely joined near the lower crop. Plain fitted black short-sleeved T-shirt and dark trousers, no overshirt or jacket. Warm natural smile and direct eye contact. Warm off-white studio background with soft peach light behind shoulders. Show both arms and the full torso; this wider seated pose must differ clearly from the separate close avatar.',
    'charlie-hills': 'Waist-up working portrait, body angled three-quarters toward the right, a natural open-hand explanation gesture near waist level, attention on an off-camera colleague. Dark blue overshirt, pale neutral background with restrained blue accents. No stage, event, guests, audience or logos.',
}


def banner_photo_prompt(style, palette=None):
    if style not in BANNER_PHOTO_STYLES:
        raise ValueError('This layout does not use a banner photograph.')
    direction=_DIRECTIONS[style]
    prompt=('Create a distinct photograph of the supplied person for a wide profile banner. '
            'The source is identity reference only. This must be a new camera frame and body pose, '
            'not a recolor, mirror, enlargement or crop of the supplied photograph. '
            'Keep the head upright rather than repeating the source head tilt; use the gaze and body angle specified below. '
            'Show head through waist with generous space around the body; face occupies no more than 22% of image height. '
            +direction+' One person only. Preserve exact facial identity, age, facial proportions, '
            'hairline or baldness, glasses and facial hair from the supplied source. Preserve realistic skin texture. '
            'No text, watermark, badges, fake event credentials, decorative logos or invented affiliations. '
            'The profile avatar will be a separate close headshot: this banner image must visibly differ in '
            'framing, pose, expression and body silhouette. Follow the specified reference clothing even when its color also appears in the avatar. Do not imitate the profile-headshot composition.')
    if palette:
        if any(k not in ('bg','fg','accent') or not isinstance(v,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',v) for k,v in palette.items()):
            raise ValueError('Banner palette must contain bg, fg or accent as #RRGGBB.')
        prompt+=f" Backdrop color direction: {palette.get('bg','neutral')}, restrained accent {palette.get('accent','neutral')}; natural skin color."
    return prompt


def _frame(path):
    with Image.open(path) as source:
        image=ImageOps.exif_transpose(source).convert('RGB')
        original_size=image.size
        frame=ImageOps.fit(image,(64,64),method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(.6))
        return frame,original_size


def _correlation(a,b):
    mean_a=sum(a)/len(a);mean_b=sum(b)/len(b)
    da=[x-mean_a for x in a];db=[x-mean_b for x in b]
    aa=sum(x*x for x in da);bb=sum(x*x for x in db)
    if aa/len(a)<16 or bb/len(b)<16:
        return None
    return sum(x*y for x,y in zip(da,db))/math.sqrt(aa*bb)


def validate_photo_pair(profile_portrait, banner_photo):
    """Reject exact or highly similar source pixels; never equate hashes with taste."""
    first,second=Path(profile_portrait),Path(banner_photo)
    if not first.is_file() or not second.is_file():
        raise ValueError('Both profile portrait and separate banner photograph must exist.')
    hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (first,second)]
    if hashes[0]==hashes[1]:
        raise ValueError('Profile portrait and banner use the same photograph. Supply a distinct shot, not a copy or crop.')
    a,size_a=_frame(first);b,size_b=_frame(second)
    gray_a=list(a.convert('L').tobytes());gray_b=list(b.convert('L').tobytes())
    gray_mirror=list(ImageOps.mirror(b).convert('L').tobytes())
    corr=_correlation(gray_a,gray_b);mirror_corr=_correlation(gray_a,gray_mirror)
    rgb_a=a.tobytes();rgb_b=b.tobytes()
    mae=sum(abs(x-y) for x,y in zip(rgb_a,rgb_b))/(64*64*3)
    if mae<2.5 or (corr is not None and corr>.995) or (mirror_corr is not None and mirror_corr>.995):
        raise ValueError('Profile portrait and banner appear to use the same photograph after resizing or restyling. Supply a genuinely distinct camera frame and pose.')
    return {
        'profile_portrait':{'role':'profile_portrait','file':first.name,'sha256':hashes[0],'dimensions':list(size_a)},
        'banner_photo':{'role':'banner_photo','file':second.name,'sha256':hashes[1],'dimensions':list(size_b)},
        'duplicate_source_check':'passed',
        'pixel_similarity':{'mean_absolute_rgb_difference':round(mae,4),'grayscale_correlation':None if corr is None else round(corr,6),'mirrored_grayscale_correlation':None if mirror_corr is None else round(mirror_corr,6)},
        'combined_profile_review':'required',
        'limitations':'This only detects source-pixel reuse. A blind reviewer must assess repeated pose, composition, credibility and overall impression in the assembled desktop and mobile profile.',
    }
