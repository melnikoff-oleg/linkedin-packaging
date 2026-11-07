"""Run isolated buyer reviews of the current rendered test packages."""
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from linkedin_pack.cli import _run_independent_review
from linkedin_pack.core import ROOT, load_keys
from linkedin_pack.providers.kie import KieClient
from linkedin_pack.styles import STYLES

AUDIENCE = ('A business founder, CEO or potential referral partner considering part-time technology '
            'leadership for a growing business. They are commercially experienced but not necessarily '
            'a software specialist, and do not know the companies or internal project names on this profile. '
            'They want to understand the work, its business relevance and the evidence behind it.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--style', choices=STYLES)
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error('--workers must be positive')
    key = load_keys()['KIE_AI_API_KEY']
    def review(slug):
        client = KieClient(key, ROOT/'.cache/blind-reviews-v2', request_timeout=240)
        return _run_independent_review(ROOT/'test_account/results'/slug, AUDIENCE, client)
    slugs = [args.style] if args.style else list(STYLES)
    failed = False
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(review, slug): slug for slug in slugs}
        for future in as_completed(futures):
            slug = futures[future]
            try:
                accepted = future.result()
                failed = failed or not accepted
                print('REVIEW', slug, 'accepted' if accepted else 'needs_revision', flush=True)
            except Exception as exc:
                failed = True
                print('REVIEW ERROR', slug, type(exc).__name__, str(exc), flush=True)
    return 2 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
