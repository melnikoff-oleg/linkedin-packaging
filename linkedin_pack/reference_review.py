"""Acceptance bound to independent visual comparisons, never legacy approvals."""
import hashlib
import json
from pathlib import Path
from .core import ROOT

FILES=('reference-comparison.png','review-desktop.png','review-mobile.png','banner.png','portrait.png','headline.txt')

def review_record(folder, *, reviews_dir=None):
    folder=Path(folder)
    try:
        qa=json.loads((folder/'qa.json').read_text())
        if qa.get('passed') is not True or qa.get('failures')!=[]:return None
        inputs={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ('brief.json','banner.html')}
        if qa.get('input_sha256')!=inputs:return None
    except (OSError,ValueError,TypeError):return None
    directory=Path(reviews_dir) if reviews_dir is not None else ROOT/'test_account/reviews'
    for path in sorted(directory.glob('reference-independent-*.json'),key=lambda p:p.stem,reverse=True):
        try:
            report=json.loads(path.read_text())
            item=report.get('reviews',{}).get(folder.name)
            if not isinstance(item,dict):continue
            hashes={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in FILES}
            if item.get('sha256')!=hashes:continue
            return {**item,'report':str(path.relative_to(ROOT)),'report_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        except (OSError,ValueError,TypeError):continue
    return None

def reference_review_passed(folder, *, reviews_dir=None):
    item=review_record(folder,reviews_dir=reviews_dir)
    return bool(item and item.get('verdict')=='accept' and isinstance(item.get('findings'),list)
                and not any(isinstance(f,dict) and f.get('required') is True for f in item['findings']))


def buyer_review_record(folder, *, reviews_dir=None):
    """The buyer sees neutral cards only, independently of the source comparison."""
    folder=Path(folder)
    # Compare stems so a later suffixed report wins over the unsuffixed initial
    # report even when both reviewed identical pixels. Do not skip rejections.
    directory=Path(reviews_dir) if reviews_dir is not None else ROOT/'test_account/reviews'
    for path in sorted(directory.glob('reference-buyer-release*.json'),key=lambda p:p.stem,reverse=True):
        try:
            report=json.loads(path.read_text())
            hashes={name:hashlib.sha256((folder/name).read_bytes()).hexdigest()
                    for name in ('review-desktop.png','review-mobile.png')}
            for item in report.get('reviews',[]):
                if isinstance(item,dict) and item.get('style')==folder.name and item.get('sha256')==hashes:
                    return {**item,'report':str(path.relative_to(ROOT)),
                            'report_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        except (OSError,ValueError,TypeError):continue
    return None


def reference_buyer_review_passed(folder, *, reviews_dir=None):
    item=buyer_review_record(folder,reviews_dir=reviews_dir)
    return bool(item and item.get('verdict')=='accept' and item.get('required_findings')==[])
