# Kie.ai provider

This tool uses the same `KIE_AI_API_KEY` for portrait editing and structured copy. It does not require a separate OpenAI key.

## Configured models and data flow

The source currently configures `gpt-image-2-6/sunburst-image-to-image` for photo edits and `gpt-6.1-sol` for copy/review. These are defaults in `linkedin_pack/providers/kie.py`, not a promise of ongoing provider availability. Check [Kie documentation](https://docs.kie.ai/) and your account before changing models or starting a large run.

Images are submitted through `/api/v1/jobs/createTask` and polled through `/api/v1/jobs/recordInfo`. Copy/review use `/codex/v1/responses`. Local PNG/JPEG/WebP photos up to 10 MB are uploaded for the requested edit. Completed results are downloaded immediately and saved locally. Review sends the neutral desktop/mobile previews and audience persona to Kie. LinkedIn intake separately sends the profile URL to Apify; `--website` sends the requested website URL to Firecrawl.

Square profile edits use 2K output. A distinct banner image and a transparent 1K cutout may be separate paid requests. Inspect the resulting person's identity, body, pose and clothing against the original portrait.

## Costs

Provider requests use your account credits. Prices, model availability, quotas and retention policies can change; [Kie's pricing page](https://kie.ai/pricing) and your dashboard are the billing reference. This tool records reported `credits_consumed` when supplied by the provider. It does not top up your account or make payments.

An explicit style uses one copy request; automatic selection uses two. A complete style can also require an avatar edit, a distinct banner shot, a cutout and a buyer review. `--all-styles` multiplies this work across ten compositions before cache and supplied-asset savings. Rejected visual reviews require your attention and never trigger automatic image regeneration.

## Resuming without duplicate charges

The provider saves a request fingerprint before submitting a paid task. It includes the source image hash, prompt, model and rendering options; different destination paths reuse the same result. Cache keys are scoped to the credential's hash, and raw keys are never written to task records.

- Poll timeout: rerun the exact command. The saved task ID is queried; no new image is submitted.
- Download failure after completion: the client tries Kie’s official [temporary download URL](https://docs.kie.ai/common-api/download-url) once, which returns a signed download URL. If that also fails, rerun the exact command to download the saved result; no image is regenerated.
- Failed image task: the failure is retained, and the provider refuses to resubmit automatically.
- Ambiguous network failure during submission: the provider raises `SubmissionUnknown`. Check Kie's dashboard first. If a task exists, add its ID as `task_id` and set `state` to `waiting` in the referenced image record, then rerun. Delete the record only after verifying that no task was created or after deliberately choosing to pay for a new request.
- Interrupted process: a `.lock` file may remain. Verify that its process is no longer running before removing that lock. The record still prevents blind resubmission.
- Brief failures are not retried automatically, because synchronous text requests may already have been charged. Inspect the dashboard and cached record before explicitly retrying.

Keep `.cache/` private. It includes job IDs, signed media URLs, copy and prompts. It is excluded from the portable export. Never put the key in a URL or command-line argument; load it from `.env` or the environment.

## Python contract

```python
from linkedin_pack.providers.kie import KieClient

client = KieClient(api_key, cache_dir='.cache/kie')
portrait = client.generate_headshot(
    source='person.png',
    prompt='Keep the same person and face; create a soft studio headshot...',
    output_path='output/portrait-master.png',
    resolution='2K',
    timeout=600,
)
brief = client.generate_brief(
    context=verified_context,
    references=reference_analyses,
    system_prompt=brief_instructions,
    schema=brief_json_schema,
)
```

Image generation remains nondeterministic. Caching makes repeat runs stable; deliberately changing the prompt creates another paid request. The caller must inspect facial features, crop, lighting and coherence and must reject unsupported claims before delivery.
