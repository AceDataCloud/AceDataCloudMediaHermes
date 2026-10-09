# Ace Data Cloud Media for Hermes

![Ace Data Cloud](assets/catalog.png)

One plugin with 17 independently selectable service toolsets and a Nano Banana
`image_generate` backend. The `acedatacloud` model provider remains a separate
plugin. New services are released as version and catalog-pin updates to this
plugin, not new catalog entries.

**Billing and data disclosure:** each generate call spends Ace Data Cloud credits
on your `ACEDATACLOUD_API_KEY` with **no Hermes approval prompt**. The model can
choose costly options, including pro models, 4K and up to 4 images where the service
supports them. Prompts and reference URLs go to **api.acedata.cloud**. Search and
face analysis also use paid Credits. Enabling a service allows the agent to invoke
its tools with your key; a schema limit is not a spending budget or confirmation.

## Install and select services

Requires Hermes **0.21.6 or newer**, an Ace Data Cloud key with the appropriate
service access, and sufficient Credits. Check current pricing and obtain your key
at [Ace Data Cloud](https://platform.acedata.cloud).

Install a reviewed version from its full 40-character source commit:

```sh
hermes plugins install https://github.com/AceDataCloud/hermes-acedatacloud-media --ref <40-character-SHA> --enable
hermes config set ACEDATACLOUD_API_KEY '<your-api-key>'
hermes tools
```

Enter the key only into your active Hermes profile, never into a chat prompt.
In `hermes tools`, select only the service toolsets you want the agent to use and
start a new session. Each service has its own row, for example `acedata-veo` and
`acedata-suno`. Normal Hermes CLI selection also works:

```sh
hermes tools disable acedata-veo
hermes tools enable acedata-suno
hermes tools list
```

When this plugin is available in the official catalog, install by name with
`hermes plugins install acedatacloud-media --enable`. Catalog presence, installation
and enabling toolsets are separate steps. This plugin does not modify your
toolset preferences or approval settings.

If you installed earlier standalone Ace media candidates, remove or disable them
before enabling this plugin: their tool names are retained for compatibility.
Keep the separate `acedatacloud` model provider. No tools are overridden and no
other plugin or credential store is modified automatically.

## Services

The [service schemas](services/) define the supported inputs and defaults.
This release preserves the previously tested primary operations; it does not
imply every advanced action or option from the broader APIs/Dify integrations.

| Toolset | Primary operation | Generate/search/analysis tool |
| --- | --- | --- |
| `acedata-nano-banana` | Image generation and HTTPS reference-image editing | `acedata_nano_banana_generate` |
| `acedata-veo` | Veo 3.1 Fast text/image-to-video | `acedata_veo_generate` |
| `acedata-suno` | Music from prompts or custom lyrics | `acedata_suno_generate` |
| `acedata-fish` | Speech with optional saved voice reference | `acedata_fish_generate` |
| `acedata-gpt-image` | GPT Image 2 generation | `acedata_gpt_image_generate` |
| `acedata-seedance` | Seedance 2.0 Mini text/video and first-frame animation | `acedata_seedance_generate` |
| `acedata-seedream` | Seedream 5.0 Lite image generation | `acedata_seedream_generate` |
| `acedata-happyhorse` | Happy Horse text-to-video | `acedata_happyhorse_generate` |
| `acedata-qwen-image` | Qwen Image 3.0 generation | `acedata_qwen_image_generate` |
| `acedata-google-search` | Google web/news results with links and snippets | `acedata_google_search_search` |
| `acedata-grok` | Grok Imagine fast video | `acedata_grok_generate` |
| `acedata-face` | Face landmarks in an HTTPS image | `acedata_face_analyze` |
| `acedata-midjourney` | Midjourney image generation | `acedata_midjourney_generate` |
| `acedata-flux` | FLUX Dev image generation | `acedata_flux_generate` |
| `acedata-minimax` | MiniMax H3 text/video and first-frame animation | `acedata_minimax_generate` |
| `acedata-wan` | Wan 2.6 text-to-video | `acedata_wan_generate` |
| `acedata-kling` | Kling 3 Turbo text-to-video | `acedata_kling_generate` |

Each of the 15 media services also has its own `acedata_<service>_task` tool in
the same toolset (hyphens become underscores). Google Search and Face return
synchronous structured results. The manifest declares all 32 tools.

Example for `acedata_nano_banana_generate`:

```json
{"prompt":"A teal ceramic cube on a cream background.","model":"nano-banana-2-lite","count":1,"resolution":"1K"}
```

Generation submits once with `async: true`. Save `task_id` and retrieve that same
ID with the corresponding task tool, for example:

```json
{"task_id":"returned-task-id","wait_seconds":60}
```

Only `status: succeeded` is success. Pending previews and unfinished response
errors are not terminal results. Media links are filtered to the requested media
type; Suno returns playable audio URLs rather than artwork or unrendered video.
A query failure retains the task ID. A submit timeout can mean the request was
accepted: recover its ID from your Ace request history before any resubmission.
There is no automatic submit retry, model fallback, callback or background poller.

## Native image generation

In `hermes tools` → Image Generation select **Ace Data Cloud Nano Banana** to use
the native `image_generate` backend, registered as `acedatacloud-nano-banana`.
This backend uses `nano-banana-2-lite`, one image, and maps square/landscape/portrait
to 1:1/16:9/9:16. It accepts up to four HTTPS image references, not local paths.
If its bounded wait expires, use `acedata_nano_banana_task` with the returned ID.
Do not generate again to recover the result.

The native `image_generate` entry belongs to Hermes's image-generation toolset.
Its enablement is separate from `acedata-nano-banana`: to stop all Nano requests,
also disable Image Generation or select a different backend. The backend incurs
the same Credits and data transmission described above, without a confirmation
prompt. The direct Nano tool exposes the wider model/resolution/count schema.

## Privacy and permissions

- Only HTTPS calls to the fixed `https://api.acedata.cloud` origin, at the paths
  in each service schema. Prompts, text, queries and reference URLs are sent for
  processing. Returned media URLs may expire.
- Reads only `ACEDATACLOUD_API_KEY` through Hermes's active profile secret scope
  at call time. No cached keys, OAuth tokens or sibling plugin credentials.
  Credentials are not forwarded across origin redirects or to media hosts.
- Reads only bundled schemas during registration. No user-file reads, local
  media uploads/downloads, subprocesses, background processes, telemetry,
  self-updaters, dependency installers or core overrides in plugin runtime.
- Does not store credentials, prompts or media. Hermes may retain tool messages
  in session history. Results allowlist public fields and omit raw service errors.
- The existing `fish-audio` plugin targets a direct Fish account with broader
  speech/transcription features. This original Ace-account adapter is not a fork
  and does not claim Fish affiliation. Bundled OpenAI and other community image,
  video and search integrations are unchanged.

## Validation

```sh
python -m unittest discover -s tests -v
hermes plugins validate . --install-deps
```

CI uses official Hermes 0.21.6 and its locked dependency environment. Unit tests
make no API calls. `scripts/check_runtime.py` tests real plugin discovery,
per-service selection, scoped credential availability, dispatch and the native
image provider in a fresh profile, including host isolation, without paid calls.

[Historical live evidence](tests/evidence/) records the 17 primary operations
before consolidation, with source provenance and media decoding. Service schemas,
the HTTP/task client and the Nano backend are preserved; the consolidation changes
registration and distribution. The separate consolidation regression record
identifies subsequent checks and existing-task recovery. Historical evidence is
not presented as a new billable generation or proof of catalog publication.

No third-party Python dependencies are added. `assets/logo.png` is the unmodified
[official logo](https://cdn.acedata.cloud/assets/logo.png), SHA-256
`3e2c6e2d1a61a549dae2374ec4444c77f4c2617c8f3772bdd4cd6e52bf20767e`.
The transparent 1200×600 catalog image preserves the complete logo proportionally.
AI-assisted implementation using Codex; validation is documented in the source PR.
MIT licensed.
