"""Measure reference-preserving geometry separately from legacy readability QA."""
from .reference_layout import registry
from .render import measure_design_details


def measure_reference_design(page,style):
    report=measure_design_details(page)
    report['layout_mode']='reference-faithful'
    report['style']=style
    report['regions']=page.locator('[data-ref]').evaluate_all('''els=>els.map(e=>{const r=e.getBoundingClientRect();return {slot:e.dataset.ref,x:r.x,y:r.y,width:r.width,height:r.height,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth};})''')
    report['reference_regions']=registry()[style][2]
    return audit_reference_design(report)


def audit_reference_design(report):
    report=dict(report);failures=[]
    regions={r['slot']:r for r in report.get('regions',[])}
    expected=report.get('reference_regions',{})
    if not expected: failures.append('Missing measured original reference regions')
    differences=[]
    for slot,target in expected.items():
        if slot not in regions:
            failures.append(f'Missing reference region: {slot}');continue
        actual=regions[slot]
        delta={k:round(actual[k]-target[k],2) for k in ('x','y','width','height')}
        differences.append({'slot':slot,'delta_design_px':delta})
        if any(abs(v)>2 for v in delta.values()):failures.append(f'Reference region geometry changed: {slot} {delta}')
    for item in report.get('text',[]):
        ink=item['ink']
        if ink['x']<-.5 or ink['y']<-.5 or ink['x']+ink['width']>1584.5 or ink['y']+ink['height']>396.5:
            failures.append(f'Text outside banner: {item["text"][:80]}')
        for clip in item.get('clipping_ancestors',[]):
            clipped_x=clip['clip_x'] and (ink['x']<clip['x']-2 or ink['x']+ink['width']>clip['x']+clip['width']+2)
            clipped_y=clip['clip_y'] and (ink['y']<clip['y']-2 or ink['y']+ink['height']>clip['y']+clip['height']+2)
            if clipped_x or clipped_y:
                failures.append(f'Text clipped by {clip["element"]}: {item["text"][:80]}')
                break
    # The source references contain tiny optional attribution. Record its real
    # display size; never claim it becomes mobile-readable through upsampling.
    report['font_range_design_px']=[min((t['font_size'] for t in report['text']),default=0),max((t['font_size'] for t in report['text']),default=0)]
    report['region_differences']=differences
    report['failures']=failures;report['status']='passed' if not failures else 'failed'
    report['thresholds']={'source_region_tolerance_design_px':2,'font_policy':'fixed reference sizes; edit copy to fit'}
    report['limitations']='Matches declared source-raster region measurements; independent side-by-side inspection must establish actual optical similarity. Fine secondary text follows original reference scale and is not claimed readable on mobile.'
    return report
