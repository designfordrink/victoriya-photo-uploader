# Stage 2 — Technical Requirements / Technical Design (TRD)
## Victoriya Photo Assistant — MVP 1

**Status:** Draft — Gate 2 pending technical and product-owner acceptance  
**Version:** 0.1  
**Date:** 2026-11-18  
**Discovery:** [Stage 0 — Discovery Report](../discovery/discovery-report.md) — ACCEPTED  
**PRD:** [Stage 1 — PRD v0.1](../prd/prd-v0.1.md) — ACCEPTED  
**Repository:** https://github.com/designfordrink/victoriya-photo-uploader  
**Development process:** [Standard Project Development Pipeline — Github Stage-Gated](https://app.notion.com/p/3f1937a9fdd181dbb1bae975bd77c4f7)

---

## 1. Technical recommendation

Use a **hybrid local architecture**:

1. **Hermes Desktop** is the conversational agent and workflow coordinator.
2. A project-owned **Python photo engine** performs repeatable operations on images and files.
3. A local **MCP server** exposes narrowly defined photo-job tools to Hermes. It runs as a local process over standard input/output, not as an internet-facing web service.
4. **Playwright + Chromium** collect product-gallery images from public manufacturer pages in a controlled, testable browser session.
5. **Pillow** performs deterministic image work and validates dimensions and file sizes.
6. Optional AI image services are isolated behind adapters for visual ranking, watermark masks and background extension. They are not hard-wired into the core pipeline.

This keeps Hermes replaceable: if another agent interface is preferred later, it can call the same local photo engine through MCP or its command interface.

**Important:** Hermes is the orchestrator, not the image editor. The exact image transformations must be performed by code and dedicated image models, then checked from the files actually saved.

## 2. Architecture overview

```text
Salon employee
      |
      | Public product-page URL
      v
Hermes Desktop
  Victoriya Photo Assistant skill
      |
      | Local MCP tools (stdio)
      v
Victoriya Photo Engine (Python)
      |
      +-------------------------------+
      |                               |
      v                               v
Product Page Collector             Image Pipeline
Playwright + Chromium              Pillow / OpenCV
      |                               |
      v                               +--> crop / resize / JPG
Public product gallery                +--> compression
      |                               +--> watermark cleanup adapter
      v                               +--> background extension adapter
Original image files                  +--> visual validation
      |                               |
      +---------------+---------------+
                      |
                      v
             Local job workspace
             source / output / report
                      |
                      v
             Completion report in Hermes
```

The AI model routing is split by task: DeepSeek V4.1 Flash 1017 is the proposed primary Hermes chat/tool model; Jev 1.14 is called directly by the photo engine through OpenRouter's Decisions API for typed image judgments; Gemini 3 Flash Preview is an optional escalation model for ambiguous visual or agent tasks. The image engine handles measurable transformations and file checks.

## 3. Component design

### 3.1 Hermes Desktop — agent interface

**Responsibility**

- Receive the product URL from the user.
- Use the configured primary OpenRouter chat model for conversation, planning, tool selection and exception handling.
- Follow the reusable `Victoriya Photo Assistant` skill.
- Call the local photo-job tools in the required order.
- Review the contact sheet returned by the collector and rank candidates against the PRD criteria.
- Pass the chosen lead-image asset ID to the processing tool.
- Explain the result, fallback choice and exceptions in plain language.

**Why Hermes is the preferred first candidate**

The current official documentation confirms a native desktop application for Windows, macOS and Linux. It shares its agent core, configuration, sessions and skills with the CLI and gateway. Its tool registry includes browser, file, terminal, vision and skill capabilities, and Hermes can connect to local or remote MCP servers.

Official references:
- [Hermes Desktop](https://hermes-agent.nousresearch.com/docs/user-guide/desktop)
- [Built-in Tools Reference](https://hermes-agent.nousresearch.com/docs/reference/tools-reference)
- [Hermes MCP Integration](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)

**Limitations and safeguards**

- The selected AI model must support image input to inspect the contact sheet. This must be verified with the actual model/provider used in the pilot.
- Hermes tool availability varies by installation, platform and configuration.
- The agent must only see the tools needed for this project. Avoid giving the skill unrestricted filesystem access if the photo engine can perform the required writes itself.
- Do not expose the Hermes Webapp or gateway to the public internet for this local workflow.

### 3.2 Victoriya Photo Engine — project-owned processing service

A Python package owned by this repository. It is responsible for the operations that must be repeatable and testable.

**Responsibilities**

- Validate the product URL and create a job.
- Collect the product gallery and download images.
- Store untouched source images.
- Generate a contact sheet and metadata for AI selection.
- Prepare lead and secondary photos.
- Validate exact output properties.
- Write a manifest and a human-readable report.
- Never overwrite source files or silently replace previous outputs.

The engine should have a small, stable interface. Image processing must not depend on the Hermes conversation transcript.

### 3.3 Local MCP server

The engine exposes its functions to Hermes through a local MCP server using the stdio transport. Hermes supports local stdio MCP servers and allows tools to be filtered per server.

Proposed tool contract:

| Tool | Input | Result |
|---|---|---|
| `discover_product_gallery` | `product_url` | `job_id`, brand/model candidates, product title, asset list, dimensions, file sizes, contact-sheet image, warnings |
| `prepare_product_images` | `job_id`, `lead_asset_id` | prepared main and secondary assets, validation results, output paths |
| `get_photo_job_report` | `job_id` | complete job status, manifest, output list and warnings |

The agent executes these tools in sequence within one user request. It does not ask the user to approve every intermediate crop or download. The employee reviews the completed output after processing.

**Tool rules**

- Tools must validate all arguments and reject unknown job IDs.
- `prepare_product_images` must accept only assets belonging to the specified job.
- The server must return explicit failure states, not a success-shaped response after partial failure.
- Do not enable parallel execution for tools that mutate the same job or output folder.
- The initial server should expose no general-purpose shell or arbitrary file-read tool.

Reference: [Hermes MCP Integration](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp).

### 3.4 Product Page Collector

**Recommended technology:** Playwright for Python, with its own managed Chromium installation.

**Why a dedicated browser worker instead of relying only on free-form agent browsing**

- Gallery discovery must be repeatable and covered by tests.
- Product pages can load gallery content with JavaScript, lazy loading and responsive image variants.
- Playwright provides explicit browser download handling and a predictable browser context.
- The extractor can record which page element or gallery entry produced each image.

Hermes may still use its own browser for investigation, but production gallery extraction should be performed by the repository-owned collector.

**Collector workflow**

1. Accept only a valid `http://` or `https://` product URL.
2. Resolve the hostname and reject loopback, private, link-local and reserved network targets.
3. Open the public page in a clean browser context without salon or personal login credentials.
4. Wait for page readiness and inspect rendered product-gallery elements.
5. Scroll or interact with the public gallery as needed to load normal visible gallery images.
6. Collect image URLs and available metadata such as alt text, image dimensions and gallery order.
7. Prefer the largest available product-image variant where it is clearly the same asset.
8. Download each unique image and calculate a SHA-256 hash.
9. Ignore logos, UI icons, banners, unrelated recommendations, tiny thumbnails and duplicates.
10. Save a contact sheet and candidate metadata for the agent's visual ranking.

The collector must not try to defeat CAPTCHAs, paywalls, anti-bot measures, authentication or access restrictions. If ordinary public access fails, stop and report the reason.

Reference: [Playwright — Downloads](https://playwright.dev/python/docs/downloads).

### 3.5 Lead photo ranking

The candidate images are presented to the visual-decision adapter with stable asset IDs. Jev 1.14 evaluates structured visual questions against the PRD criteria:

1. Front-facing model.
2. Full-length view.
3. Dress visible in its entirety, including hem/train where possible.
4. Sharpness and sufficient source resolution.
5. Low risk of destructive cropping or reconstruction.

The first gallery image gets preference only when it meets the criteria. Otherwise, select the strongest alternative and label it as a fallback.

**Important design rule:** ranking and file preparation are separate. The agent must select an existing downloaded asset ID; it must not invent a source image or point to an image outside the current job.

A confidence field should be recorded for the selection. The workflow still chooses the best available image at low confidence, but the final report must flag that selection.

**Jev-specific implementation notes:**
- OpenRouter model ID: `typesafe/jev-1.14` (or the versioned latest alias only after it has been revalidated).
- Jev is a typed decision model, not a conversational LLM: it returns decisions/probabilities rather than explanations or free-form text.
- Its primitives include Choice (select a candidate), Noul (test a yes/no condition), Score (rate on an ordered scale) and Box (locate a region in an image).
- Image input and Box are documented for Jev 1.14. Box always returns coordinates and has no native “not found” result; pair it with a Noul presence check when locating an object such as a watermark.
- OpenRouter/TypeSafe currently documents image requests as using a slower, less accurate long-context mode. Therefore Jev must be evaluated on the actual dress-photo test set and must not be treated as an infallible gate.
- Use Jev's typed result and confidence to select or flag; use a chat model only when a human-readable explanation or escalation is needed.

References: [Jev documentation](https://openrouter.ai/docs/guides/community/jev), [Multimodal Decisions](https://openrouter.ai/docs/guides/community/multimodal-decisions).

### 3.6 Model routing and task allocation

The project should use separate models for conversational orchestration and small, structured judgments. A single model should not be called for every subtask.

### Proposed model roles

| Role | Model | OpenRouter model ID | Responsibility |
|---|---|---|---|
| Main Hermes model | DeepSeek V4.1 Flash 1017 | `deepseek/deepseek-v4.1-flash-1017` | User conversation, multi-step planning, browser/photo-engine tool calls, exception handling and final report |
| Visual decision model | Jev 1.14 | `typesafe/jev-1.14` | Structured image decisions: choose between candidate photos, test frontal/full-length criteria, score suitability and locate a target region |
| Escalation / second opinion | Gemini 3 Flash Preview | `google/gemini-3-flash-preview` | Ambiguous visual ranking, difficult page interpretation or cases where the primary model/Jev confidence is insufficient |

### Why DeepSeek V4.1 Flash 1017 for the main agent

The OpenRouter model page currently lists:
- input price: $0.036 per million tokens;
- output price: $0.50 per million tokens;
- context length: 1,048,576 tokens;
- text and image input;
- tool calling and structured-output support.

OpenRouter also lists Hermes Agent among its high-usage applications for this model. This makes it a strong low-cost starting candidate for the main Hermes loop, but not an unconditional quality guarantee. Verify the current provider route and tool-call reliability with this project's actual workflows.

Source: [DeepSeek V4.1 Flash 1017 on OpenRouter](https://openrouter.ai/deepseek/deepseek-v4.1-flash-1017).

### Why Jev 1.14 for visual decisions

Jev 1.14 accepts image input through the OpenRouter Decisions API and returns typed judgments rather than free-form prose. This fits narrowly defined questions such as:

- Which of these candidate images is the best lead photo?
- Is the model facing the camera?
- Is the model visible full-length?
- Is the dress hem/train cut off?
- Where is a suspected watermark located?

The relevant decision primitives are:
- `Choice`: select one candidate from a set;
- `Noul`: estimate whether a condition is true;
- `Score`: score a candidate on an ordered scale;
- `Box`: return normalized coordinates of a target region.

Use `typesafe/jev-1.14`, not Jev 1.13, for image-based Box questions. Box returns a bounding rectangle and does not itself return a pixel-level mask. It also has no native “target absent” answer, so a Noul presence check is required before using its coordinates.

Important limitation: the current TypeSafe documentation says every request containing an image uses its long-context mode, which is slower and less accurate than the default short-text mode. Treat Jev as a very cheap structured judge to benchmark, not as a guaranteed superior vision model. The PRD pilot must establish actual accuracy and confidence thresholds for wedding-dress images.

Sources:
- [Jev Documentation](https://openrouter.ai/docs/guides/community/jev)
- [Multimodal Decisions](https://openrouter.ai/docs/guides/community/multimodal-decisions)
- [TypeSafe models and current Jev pricing](https://openrouter.ai/typesafe)

**Terminology note:** OpenRouter documents Jev 1.14's image-input capability and multimodal Decisions interface; it does not list a separate official model ID named `Jev Vision` in the TypeSafe model family. In this TRD, “Jev Vision” means using Jev 1.14 for image-based decisions. If the project later uses a separate custom JEV Vision endpoint, it should be added as a distinct adapter and benchmarked separately.

### Why Gemini 3 Flash as an escalation option

Gemini 3 Flash Preview accepts image input, tool calls and structured outputs, with a 1M-token context. Its listed standard price is $0.50/M input and $3/M output tokens. This is materially more expensive than the proposed DeepSeek primary model and Jev's input-token price, so it should be called only when a case is ambiguous or an independent second opinion is useful.

Source: [Gemini 3 Flash Preview on OpenRouter](https://openrouter.ai/google/gemini-3-flash-preview).

### Proposed routing policy

1. Deterministic code handles file formats, dimensions, compression, hashing and path safety. Do not spend model tokens on facts that can be measured by code.
2. Hermes uses DeepSeek V4.1 Flash 1017 for the main conversation and tool orchestration.
3. Jev 1.14 handles structured photo judgments and suspected-region localization.
4. If Jev confidence is low, candidate rankings disagree, or the image is unusually difficult, send only that case to Gemini 3 Flash as an escalation.
5. Keep the reason for every escalation in the job report.
6. Do not let a visual model authorize a destructive edit by itself. The image pipeline must protect source pixels and validate output; the user reviews final images.

### Hermes configuration direction (illustrative)

The main model and its provider are configured in Hermes `config.yaml`. A separate auxiliary vision chat model can also be configured there, but Jev must **not** simply be configured as Hermes' ordinary auxiliary chat-vision model: Jev uses the Decisions API and returns typed judgments, not chat completions.

The exact initial Hermes configuration should be generated and tested during the implementation stage, not copied blindly from this illustrative block.

```yaml
model:
  provider: openrouter
  model: deepseek/deepseek-v4.1-flash-1017

# Jev 1.14 is called by the Photo Engine's
# OpenRouter Decisions API adapter, not as a chat model.
```

### OpenRouter cost and privacy controls

- Store the OpenRouter API key outside Git, preferably in Hermes' credential store or its local environment file.
- Set a monthly or project-level spending limit and inspect actual per-job usage.
- Where supported, use OpenRouter provider routing with `data_collection: "deny"`; confirm the selected upstream provider meets the salon's image-handling requirements.
- Disclose when photos are sent to external model providers. Public product photos may still be commercially licensed assets.
- Keep all image transfers to the minimum needed: use resized contact sheets for visual ranking and send full-resolution images only to image-processing backends that need them.

References:
- [Hermes OpenRouter provider setup](https://hermes-agent.nousresearch.com/docs/integrations/providers)
- [Hermes auxiliary model configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration)
- [Hermes OpenRouter provider routing](https://hermes-agent.nousresearch.com/docs/user-guide/features/provider-routing).

## 3.7 Image processing engine

#### Deterministic operations

**Recommended library:** Pillow.

Use it for:

- reading and verifying supported image formats;
- applying EXIF orientation;
- converting color modes and handling transparency;
- converting to JPEG;
- resizing without stretching;
- calculating exact crop coordinates;
- saving at precisely 600 × 800 px;
- optimizing secondary images to meet the file-size limit;
- verifying the actual saved file dimensions and byte count.

The lead photo must never be stretched to force a 3:4 ratio. Use a crop only when the model and dress remain visible. If there is insufficient horizontal canvas, route the job to background extension.

References:
- [Pillow ImageOps documentation](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html)
- [Pillow ImageOps examples](https://github.com/python-pillow/Pillow/blob/main/docs/reference/ImageOps.rst)

#### Background extension

Implement an adapter interface rather than committing the whole product to one inpainting model.

Proposed process:

1. Create a 3:4 canvas at the target composition.
2. Place the untouched source image without distortion.
3. Define masks only in newly added background areas.
4. Protect the model and dress using a foreground mask.
5. Generate the side background using the selected local or cloud inpainting/outpainting backend.
6. Composite the original model/dress pixels back over the generated background where applicable.
7. Inspect the result and validate that the source subject has not been changed.
8. Save the final 600 × 800 JPG.

The mask should never overlap the dress or model intentionally. If the model cannot produce a reliable subject mask, do not run generative extension automatically; use the safest non-generative alternative and report that manual review is required.

**Candidate for subject masking:** Meta SAM 2. Its official repository describes image and video segmentation and lists Apache 2.0 licensing for its code and model checkpoints. It is a candidate, not yet a locked dependency.

Reference: [Meta SAM 2 repository](https://github.com/facebookresearch/sam2).

#### Watermark cleanup

The salon's existing Hugging Face tool is useful as a prototype reference, but not as a complete automatic solution.

Observed implementation:
- The Space uses Gradio's image editor with a manually drawn mask.
- Its processing function passes the image and mask to `SimpleLama`.
- Its current requirements include Gradio, PyTorch and OpenCV.

That means it demonstrates the inpainting step, but it does not automatically locate watermarks or create masks. It should not be treated as a ready-made end-to-end agent tool.

References:
- [Existing Inpaint-Objectremover Space](https://huggingface.co/spaces/bacancydataprophets/Inpaint-Objectremover)
- [Space app.py](https://huggingface.co/spaces/bacancydataprophets/Inpaint-Objectremover/blob/main/app.py)
- [OpenCV LaMa model card](https://huggingface.co/opencv/inpainting_lama)

**Recommended design**

- Separate watermark detection/mask creation from inpainting.
- Use a visual model or a dedicated detector to identify likely watermark regions.
- Expand masks carefully around the detected mark.
- Run LaMa or another selected inpainting backend only on authorized images and appropriate masks.
- Compare the edited output with the source.
- If a watermark crosses the dress, face or important product details and a faithful repair cannot be assured, preserve the best permitted source and flag it instead of inventing garment detail.

Do not assume that a model that removes a small object cleanly can remove a large translucent watermark across lace or fabric without damaging the product.

### 3.7 Secondary photo processing

Proposed default: convert all secondary photos to JPEG for consistency with the current website workflow.

Processing steps:

1. Keep source composition and aspect ratio.
2. Apply EXIF orientation.
3. Convert to a web-safe RGB color profile.
4. Apply authorized watermark cleanup where safe.
5. Save as JPEG.
6. If the file is above 2.5 MB, reduce JPEG quality in controlled steps; resize only if necessary and only while preserving the aspect ratio.
7. Reopen the saved file and verify it is valid and no larger than 2.5 MB.

This default remains a product decision to confirm: the user has not explicitly said that every secondary image must be JPEG.

### 3.8 Storage and job files

The configured base directory is the local `Victoriya` directory. It must be set explicitly; never assume a drive letter.

Proposed structure:

```text
Victoriya/
└── Collections/
    └── wedding/
        └── <Brand>/
            └── <Model>/
                ├── source/
                │   └── <job-id>/
                ├── output/
                │   ├── <Model>-main.jpg
                │   ├── <Model>-02.jpg
                │   └── ...
                └── reports/
                    └── <job-id>.json
```

If a target output name already exists, use a unique job suffix or version suffix. Never overwrite an existing output without an explicit later feature and separate acceptance requirement.

Recommended job manifest:

```json
{
  "job_id": "uuid",
  "source_url": "https://manufacturer.example/product",
  "brand": "Pronovias",
  "model": "SUFI",
  "status": "completed",
  "assets": [
    {
      "asset_id": "image-001",
      "source_path": "source/<job-id>/image-001.webp",
      "source_sha256": "...",
      "width": 1800,
      "height": 2400,
      "selected_role": "main",
      "output_path": "output/SUFI-main.jpg",
      "output_width": 600,
      "output_height": 800,
      "output_bytes": 123456,
      "processing_method": "crop",
      "warnings": []
    }
  ]
}
```

The manifest is the machine-readable record of what happened. A readable Markdown or text report is generated from it.

### 3.9 Configuration

Use one local configuration file, excluded from Git, containing:

- absolute `victoriya_root` path;
- default collection (`wedding`);
- main output width and height (600, 800);
- secondary image maximum bytes (2.5 MB);
- default secondary output format (proposed: JPG);
- maximum download and job limits (to be calibrated during implementation);
- allowed image-processing backends;
- whether remote image processing is allowed;
- model/provider identifiers, but no API keys in the file if they can be stored in the OS credential store or environment.

Secrets, API keys, cookies and login credentials must never be committed to the public repository.

## 4. Technology choices and alternatives

| Layer | Recommended choice | Alternative | Reason |
|---|---|---|---|
| User-facing agent | Hermes Desktop | Other agent UI or a custom app | The desired interaction is conversational; Hermes supports desktop sessions, skills and MCP. |
| Agent integration | Local MCP server over stdio | Direct shell/CLI calls | Typed, narrow tool contracts reduce free-form shell access and make the engine reusable. |
| Main agent model | DeepSeek V4.1 Flash 1017 via OpenRouter | Gemini 3 Flash Preview | Strong cost/context/tool support as the initial candidate; validate on the project workflow. |
| Structured visual decisions | Jev 1.14 via Decisions API | Chat model with vision | Very low input-token price and typed answers; use only after dress-photo accuracy tests. |
| Product page extraction | Playwright Python + managed Chromium | Hermes browser tool alone | Dedicated extractor is easier to test and maintain than free-form browser actions. |
| Image processing | Python + Pillow | Photoshop scripting / ImageMagick | Reproducible pixel-level output and easy validation. |
| Subject masking | SAM 2 candidate + fallback strategy | Other segmentation model | A subject mask helps protect the model and dress during side-background extension. |
| Local inpainting | LaMa/SimpleLama candidate | SDXL inpainting or another model | LaMa is close to the current prototype; exact quality and hardware suitability require tests. |
| Cloud image processing | Optional adapter only | Local models | Can reduce local hardware requirements, but sends brand images to an external provider and may incur costs. |

### Agent alternatives considered

**Hermes Desktop + local engine — recommended first option**

- Natural URL-to-result chat interaction.
- Native Windows desktop app.
- Reusable skills and MCP integration.
- Local browser and file workflow.
- The image engine remains independent of Hermes.

**Custom desktop app + local engine**

- Could provide a simpler one-purpose interface.
- Requires building and maintaining a separate UI, installer, update process and agent integration.
- Not justified before the image workflow and processing quality are validated.

**Agent-only workflow (Hermes browsing and editing files without a project-owned engine)**

- Quick to demonstrate.
- Harder to test exact 600 × 800 dimensions, 2.5 MB limits, no-overwrite behavior and image selection.
- Too dependent on model judgment for repeatable file operations.
- Not recommended for the production workflow.

## 5. Runtime and deployment

**Provisional target:** the same local Windows x64 computer used for salon photo work.

- Hermes Desktop: installed natively on the user's computer.
- Python Photo Engine: isolated Python environment managed by the project.
- MCP server: started locally by Hermes using stdio.
- Playwright: uses its managed Chromium browser.
- Outputs: written to the configured local folder.
- Remote image APIs: disabled until the user explicitly accepts external processing and the chosen provider is documented.

Hermes officially documents native Windows installation and its local browser setup. Exact supported Windows build and runtime prerequisites must be checked at installation time.

References:
- [Hermes Windows Native Guide](https://hermes-agent.nousresearch.com/docs/user-guide/windows-native)
- [Hermes Browser Automation](https://hermes-agent.nousresearch.com/docs/user-guide/features/browser)

## 6. Security and permissions

### Browser and network

- Accept only HTTP and HTTPS product URLs.
- Reject local/private/link-local network destinations and unsafe redirects.
- Do not use browser credentials, saved personal sessions or private manufacturer logins in MVP 1.
- Do not circumvent bot protection, login requirements, CAPTCHAs or paywalls.
- Keep browser execution isolated from the photo engine's filesystem permissions where practical.
- Treat all page text, image metadata and filenames as untrusted content, not agent instructions.

### Local files

- The photo engine may write only within the configured `Victoriya` root.
- Resolve and validate every path before use; reject path traversal and paths escaping the root.
- Never execute downloaded files.
- Validate file content as an image before processing it.
- Keep source images read-only after download.
- Log every generated file and its source hash.
- Avoid accidental overwrite of any existing source or output.

### AI and third-party services

- Do not send image bytes to a cloud provider unless remote processing is enabled in configuration and disclosed to the user.
- No provider API keys or credentials in Git.
- Record which external service/model processed an image.
- Watermark cleanup must remain within the salon's actual usage and editing permissions.

Hermes includes write-safety controls, but those controls do not replace the photo engine's own root-directory restrictions.

Reference: [Hermes Security](https://hermes-agent.nousresearch.com/docs/user-guide/security).

## 7. Data flow and state model

A photo job has the following states:

```text
CREATED
  ↓
PAGE_OPENED
  ↓
GALLERY_DISCOVERED
  ↓
SOURCES_DOWNLOADED
  ↓
CANDIDATES_READY
  ↓
LEAD_SELECTED
  ↓
PROCESSING
  ↓
VALIDATING
  ↓
COMPLETED
```

Failure states:

- `PARTIAL`: some images processed successfully but one or more failed.
- `FAILED`: no usable set could be created.
- `NEEDS_REVIEW`: files were generated but a key visual quality check is uncertain.

A job must store:
- source URL;
- brand/model identity and identification confidence;
- created timestamp;
- image candidates and local source paths;
- source hashes and image metadata;
- lead selection and selection rationale;
- operations applied to each output;
- validation results;
- warnings and failure reasons;
- output and report paths.

The job record should be stored locally as JSON. A database is not necessary for MVP 1.

## 8. Error handling

| Failure | Required behavior |
|---|---|
| Invalid or unsupported URL | Stop before browsing; explain the allowed URL format. |
| Product page unavailable | Mark job failed and report page-access problem. |
| Gallery loaded only partially | Process accessible images and report incomplete gallery retrieval. |
| No relevant images | Stop; do not generate substitute product photography. |
| Brand/model uncertain | Ask the user to identify it before saving into a guessed folder. |
| Selected image too small | Use best available image, flag quality limitation; do not claim that upscaling restores detail. |
| Unsafe crop | Try background extension if the subject mask and backend are reliable; otherwise save the best candidate and flag review. |
| Watermark mask overlaps product details | Do not force removal; preserve source and report. |
| Inpainting/model unavailable | Continue non-generative processing where possible; report skipped edits. |
| Secondary photo exceeds 2.5 MB | Retry controlled compression; if still too large, report failure rather than silently violate the limit. |
| Output folder is unavailable | Do not save elsewhere; return a clear path/permission error. |
| Existing output file | Use a unique name; never overwrite. |
| Model/API unavailable | Retry within a bounded policy, then use safe non-generative processing or report partial failure. |

## 9. Logging and monitoring

For each job, log:

- job ID and product URL;
- browser/page load result;
- number of discovered, downloaded, deduplicated and skipped images;
- file hashes, dimensions and byte sizes;
- selected lead asset ID and selection reason;
- crop or background-extension method;
- watermark mask and inpainting backend used, if any;
- validation results;
- duration of each stage;
- warnings and errors.

Logs must not contain secrets or authentication data. Keep a per-job report that can be shared for troubleshooting without uploading the original images.

## 10. Performance and resource considerations

No strict runtime target is added to the PRD. The pilot should establish a realistic processing time.

- Browser collection should be bounded by timeouts and maximum download/job size.
- Use thumbnails/contact sheets for model ranking; retain originals for full-resolution processing.
- Avoid loading every full-resolution photo into memory simultaneously.
- Release image/model memory between jobs where possible.
- Prefer CPU-compatible deterministic operations for routine conversion and compression.
- Generative inpainting/outpainting can require materially more memory and time than ordinary resizing. Whether it runs locally or through an external service depends on the user's hardware and privacy decision.

**Hardware decision still open:** GPU model and video memory have not been provided. The recommended main conversational model and Jev visual judgments run through OpenRouter, so they do not require a local GPU. A local generative model for inpainting/outpainting would still depend on local hardware; alternatively, a cloud image-editing backend can be evaluated with explicit image-transfer and cost controls.

## 11. Testing strategy

### Unit tests

- URL and hostname validation.
- File path safety and root-directory enforcement.
- Image decode and format validation.
- EXIF orientation and color-mode handling.
- Crop coordinate calculations.
- Exact 600 × 800 output validation.
- Secondary image compression to ≤ 2.5 MB.
- No-overwrite and source hash preservation.
- Manifest and report generation.

### Integration tests

- Playwright page loading and product gallery collection.
- Gallery deduplication and thumbnail filtering.
- Contact-sheet generation with stable candidate IDs.
- Local MCP server tool contracts.
- Image processing backends with test fixtures.
- Output path creation and job-state transitions.

### End-to-end pilot

Test SUFI and several other permitted public product pages with different conditions:

- first image already frontal/full-length;
- first image unsuitable but a later image is suitable;
- narrow source image needing side-background extension;
- no perfect lead image, requiring a fallback;
- watermark on background only;
- watermark crossing fabric or other product details;
- large secondary images requiring compression;
- mixed image formats and EXIF orientations.

Every output is checked by both automated file validation and human visual review before it is used on the website.

## 12. Architecture decisions (ADR)

### ADR-001 — Hermes Desktop as the initial agent host

**Decision:** use Hermes Desktop as the first integration target, while keeping the processing engine independent.

**Reason:** it provides a native desktop UI, skills and MCP connections; it is a strong fit for a user who wants to send a link and get files back.

**Status:** proposed; validate on the actual Windows computer.

### ADR-002 — Separate Python Photo Engine

**Decision:** keep all predictable image and filesystem operations in a project-owned Python package.

**Reason:** exact dimensions, file sizes, hashes, no-overwrite behavior and testability should not depend on an LLM's free-form behavior.

**Status:** proposed.

### ADR-003 — Local MCP over stdio

**Decision:** expose a small number of photo-job operations through a local stdio MCP server.

**Reason:** Hermes documents support for local MCP server processes. No public network port is needed, and the tools can be narrowly scoped.

**Status:** proposed.

### ADR-004 — Playwright-managed Chromium for production extraction

**Decision:** use Playwright inside the collector for product gallery discovery and downloads.

**Reason:** controlled, repeatable browser execution is easier to validate than relying only on agent-driven browsing.

**Status:** proposed.

### ADR-005 — Pillow for deterministic image transformations

**Decision:** use Pillow for format conversion, crop, resize, JPEG output, file-size optimization and final file validation.

**Reason:** these operations require exact, testable pixel and byte-level results.

**Status:** proposed.

### ADR-006 — Inpainting models behind adapters

**Decision:** do not make the project dependent on one public Hugging Face Space or one specific model. Provide separate interfaces for watermark cleanup and background extension.

**Reason:** the current Space uses a manually drawn mask and SimpleLama, which is not enough for a fully autonomous workflow. Hardware, image quality and external-data policy have not yet been resolved.

**Status:** proposed.

## 13. Open technical decisions

| ID | Decision needed | Current recommendation |
|---|---|---|
| TD-01 | Actual Windows version, CPU, RAM, GPU and VRAM | Collect before choosing a local generative image model. |
| TD-02 | Local-only or cloud-assisted image processing | Prefer local by default; enable cloud only after explicit approval. |
| TD-03 | Which model handles watermark masks and cleanup | Evaluate SimpleLama/LaMa first; test quality on real salon samples. |
| TD-04 | Which method handles side-background extension | Compare local model and cloud option after hardware is known. |
| TD-05 | Vision-capable model for lead-image ranking | Validate with contact sheets from actual manufacturer galleries. |
| TD-06 | Secondary output format | Proposed JPG; needs product-owner confirmation. |
| TD-07 | Absolute local `Victoriya` root path | Configure once during installation. |
| TD-08 | File naming and repeat-job layout | Use unique names/job IDs; confirm preferred final pattern. |
| TD-09 | Maximum number/size of gallery assets | Establish safe initial limits during implementation and record them. |
| TD-10 | Primary OpenRouter model | Proposed: `deepseek/deepseek-v4.1-flash-1017`; benchmark tool-call reliability and cost on the actual Hermes skill. |
| TD-11 | Jev visual decision model | Proposed: `typesafe/jev-1.14` through Decisions API; validate Choice/Noul/Box accuracy and confidence thresholds on labeled dress photos. |
| TD-12 | Escalation vision model | Proposed: `google/gemini-3-flash-preview`, called only on ambiguous or low-confidence cases. |

## 14. Requirements traceability

| PRD requirement | Technical component | Verification |
|---|---|---|
| FR-01–FR-05: URL and gallery retrieval | MCP + Playwright Collector | URL/page/gallery integration tests |
| FR-06–FR-07: lead-photo selection | Contact sheet + Jev 1.14 Decisions adapter; optional DeepSeek/Gemini escalation | Candidate-ranking test set and human review |
| FR-08–FR-10: main-image preparation | Pillow + crop/extension adapters | Exact dimension test + visual review |
| FR-11–FR-13: secondary images and watermark cleanup | Pillow + cleanup adapter | Byte-size tests + visual review |
| FR-14–FR-15: file storage and source preservation | Storage manager + manifest | Path, hash and overwrite tests |
| FR-16: completion report | Job reporter | Report/schema tests |
| FR-17: partial failures | Job state machine | Fault-injection integration tests |
| FR-18: variable brand/model folders | Config + storage manager | Multi-brand path tests |
| FR-19: clear errors | Collector and job error handling | Negative end-to-end tests |

## 15. Gate 2 — TRD Acceptance

| Gate 2 condition | Status |
|---|---|
| Proposed architecture covers the PRD | Drafted |
| Main components and their responsibilities are defined | Drafted |
| Data and tool interfaces are described | Drafted |
| Browser, image and filesystem integrations are identified | Drafted |
| Security and file permissions are considered | Drafted |
| Error handling and logging are described | Drafted |
| Testing strategy covers PRD requirements | Drafted |
| Critical technical uncertainties are recorded | Open: hardware, local/cloud policy, model selection |

**Gate 2 status: READY FOR TECHNICAL REVIEW — NOT YET ACCEPTED.**

After the technical design is accepted, proceed to **Stage 3 — Detailed Specification**. Do not implement the photo engine before Gate 2 and the following specification gate are accepted.
