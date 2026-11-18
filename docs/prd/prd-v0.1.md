# Stage 1 — Product Requirements Document (PRD)
## Victoriya Photo Assistant — MVP 1

**Status:** Draft — Gate 1 pending product-owner acceptance  
**Version:** 0.1  
**Date:** 2026-11-18  
**Discovery:** [Stage 0 — Discovery Report](../discovery/discovery-report.md) — ACCEPTED  
**Repository:** https://github.com/designfordrink/victoriya-photo-uploader  
**Development process:** [Standard Project Development Pipeline — Github Stage-Gated](https://app.notion.com/p/3f1937a9fdd181dbb1bae975bd77c4f7)

---

## 1. Product summary

Victoriya Photo Assistant is a helper for preparing dress product photographs for the Victoriya salon website.

The user gives the assistant a public product-page link from a dress manufacturer. The assistant finds the accessible product-gallery images, downloads them, chooses the best lead image, prepares the lead image in the required format and dimensions, prepares the remaining gallery images, and saves the results in the correct local folder.

The intended user experience is **one link in, a prepared image set out**. The agent should carry out the workflow without asking the user to approve each intermediate crop or image. The user reviews the completed files and the short report at the end.

The first delivery focuses only on photo acquisition and preparation. It does not create or publish WordPress portfolio items.

## 2. Problem statement

Preparing photographs for a new dress currently involves several manual steps and applications: opening manufacturer websites, downloading product images, converting formats, cleaning authorized watermarks, making the lead image vertical at 600 × 800 px in Photoshop, and checking that the entire dress remains visible.

The most difficult steps are watermark cleanup, extending the background when the source image is too narrow, and selecting a crop that does not cut off the model or dress.

The current reported baseline is approximately **5 dresses per week** and **10–15 minutes per dress**. The assistant should reduce repetitive preparation work while keeping image quality and the salon's rights to use the photographs intact.

## 3. Target user

**Primary user:** the salon owner or employee who prepares new dress photographs for the Victoriya website.

The user should not need to understand image-editing tools or technical commands. The user interaction should be simple:

1. Send a public product-page URL.
2. Let the assistant complete the preparation.
3. Open the output folder and review the result.

## 4. Goals

1. Turn a public product-page URL into a locally saved set of prepared product images.
2. Automatically select the most suitable lead photo using the salon's visual criteria.
3. Produce the lead photo at exactly 600 × 800 px without unnecessarily cutting off the model or dress.
4. Preserve and prepare all relevant, unique secondary product-gallery images at no more than 2.5 MB each.
5. Use watermark cleanup only for images the salon is authorized to edit and only where the cleanup can be performed without unacceptable damage.
6. Save outputs in the folder structure specified by the user.
7. Make failures, fallback choices and uncertain edits visible in a short completion report.
8. Preserve original downloaded source files so processed images can be regenerated.

## 5. Non-goals

The first version will not:

- create a WordPress Portfolio item;
- fill in WordPress title, description, brand, model or categories;
- upload, publish or update a WordPress page;
- log into private manufacturer portals or use private credentials;
- bypass CAPTCHAs, paywalls, authentication, anti-bot controls or other access restrictions;
- guarantee access to every manufacturer's website or every image gallery;
- silently publish an image without the user's later review;
- alter the design, cut, pattern, color or other product-defining features of the dress;
- perform unrelated marketing, SEO or catalogue work.

These may be considered as later, separate product stages.

## 6. Main user story

**As a salon employee**, I want to send the assistant a public product page for a dress, so that it can download and prepare the product photos for the website without me manually editing each file.

Example source URL:

https://www.pronovias.com/int_en/bridal-dress-a-line-sweetheart-neckline-lace-sufi

Expected result:

- one lead image in JPG format, exactly 600 × 800 px;
- the remaining useful, unique product-gallery images, each no larger than 2.5 MB;
- all prepared files saved under the matching brand/model output directory;
- a report showing the result and any exceptions.

## 7. User workflow

### 7.1 Start a job

- The user provides a publicly accessible product-page URL.
- The assistant identifies the brand and model from the page where possible.
- If brand or model cannot be identified confidently, the assistant asks one short question rather than guessing a folder name.
- The assistant confirms the destination folder in its completion report.

### 7.2 Find and acquire images

- The assistant opens the public product page and inspects its product gallery.
- It downloads accessible, full-quality product-gallery images using normal public-page behavior.
- It prefers original image files or the best available resolution rather than small thumbnails.
- It skips duplicate image variants, icons, banners, unrelated recommendations and other non-product imagery.
- It does not try to access private areas or defeat access restrictions.
- If some gallery images cannot be accessed, it continues with the images it can obtain and reports the limitation.

### 7.3 Select the lead photo

The assistant evaluates the product-gallery images and selects one lead photo automatically.

**Preferred criteria, in order:**

1. The model is standing front-facing.
2. The model is visible full-length.
3. The dress is clearly visible and important garment details are not hidden.
4. The image is sharp and large enough for the required output.
5. The original framing allows the image to be prepared without an excessive crop or risky reconstruction.

The first/main image on the manufacturer's page is normally the starting candidate. It is not automatically selected if it does not meet the visual criteria.

If no image fully matches the preferred criteria, the assistant chooses the best available alternative and labels it as a fallback in the report. The workflow should continue rather than stop solely because the ideal photo is absent.

### 7.4 Prepare the lead photo

The lead image must:

- be saved as JPG;
- have exact dimensions of **600 × 800 px**;
- use a vertical 3:4 composition;
- keep the model and the dress visually complete wherever the source permits;
- avoid cutting off the head, feet, dress hem, train or other important details.

The assistant automatically chooses one of two methods:

**A. Crop:** use a 3:4 crop when it can produce the required composition without losing important parts of the model or dress.

**B. Extend the background:** when the source is too narrow or a safe crop is not possible, extend the background on the left and/or right to fit the 3:4 frame.

Background extension must be limited to surrounding background areas. The assistant must not invent or modify the dress, the model's body, garment details, or product-defining elements. If safe framing cannot be achieved, it must save the best non-destructive candidate and flag it for review rather than silently producing a misleading result.

### 7.5 Prepare secondary photos

- Include the useful, unique images from the product gallery, excluding the selected lead photo.
- Preserve each image's original composition and aspect ratio.
- Each prepared secondary image must be **2.5 MB or smaller**.
- Prefer a clean version without a visible watermark when the salon is authorized to remove that watermark.
- If watermark cleanup is not permitted, technically unavailable or likely to damage important image content, do not force it; preserve the best permitted version and report the exception.
- Do not crop or reconstruct secondary photos merely to make their dimensions match the lead photo.

### 7.6 Save results

The user-defined folder structure is:

```text
Victoriya/
└── Collections/
    └── wedding/
        └── <Brand>/
            └── <Model>/
                ├── source/
                └── output/
```

- `source/` is the proposed location for downloaded, unmodified source files.
- `output/` contains prepared images.
- The base path to the `Victoriya` directory must be configurable and validated before the first job. The assistant must not guess a drive letter or silently save elsewhere.
- Original source files must never be overwritten.
- If the output folder already contains files, the assistant must avoid accidental overwrites. It should use a job-specific subfolder or a safe unique filename and report what it did.

**Proposed file names:**

- `<Model>-main.jpg` for the lead photo.
- `<Model>-02.jpg`, `<Model>-03.jpg`, etc. for secondary photos.

The exact naming convention is a product-owner decision to confirm before detailed specification.

### 7.7 Report completion

At the end of a job, the assistant returns a concise report containing:

- source page and detected brand/model;
- selected lead image and whether it met the preferred criteria or was a fallback;
- lead-image processing method: crop or background extension;
- confirmation that the lead output is JPG and 600 × 800 px;
- number of secondary images saved and confirmation that each is ≤ 2.5 MB;
- output folder location;
- any skipped files, download failures, watermark-cleanup limitations or images that need human review.

The report must not claim success for an image it failed to create or validate.

## 8. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Accept a public manufacturer product-page URL as the job input. | Must |
| FR-02 | Identify the product brand and model, or ask the user when identity is uncertain. | Must |
| FR-03 | Inspect the public product gallery, including content loaded dynamically in the browser. | Must |
| FR-04 | Download accessible, relevant product-gallery images at the best available resolution. | Must |
| FR-05 | Detect and skip duplicate, thumbnail-only and unrelated gallery assets where possible. | Must |
| FR-06 | Select one lead image automatically using the full-length, front-facing composition criteria. | Must |
| FR-07 | Select the best available fallback if the ideal lead image does not exist, and report the fallback. | Must |
| FR-08 | Prepare the lead image as JPG at exactly 600 × 800 px. | Must |
| FR-09 | Automatically choose safe crop or side-background extension for the lead image. | Must |
| FR-10 | Preserve the model, dress and product-defining details; flag unsafe or uncertain image edits. | Must |
| FR-11 | Prepare all useful, unique secondary gallery images without changing their composition. | Must |
| FR-12 | Ensure every secondary output file is no larger than 2.5 MB. | Must |
| FR-13 | Perform watermark cleanup only where authorized and technically safe; report exceptions. | Must |
| FR-14 | Save source and prepared files separately in the configured local folder hierarchy. | Must |
| FR-15 | Never overwrite original downloads and prevent accidental output-file overwrites. | Must |
| FR-16 | Produce a completion report with validated properties and exceptions. | Must |
| FR-17 | Continue with accessible images if some gallery files fail, rather than failing the whole job unnecessarily. | Should |
| FR-18 | Support different brand and model folder names using the same folder pattern. | Must |
| FR-19 | Provide a clear error when the product page is inaccessible or no relevant images can be found. | Must |

## 9. Non-functional requirements

### Usability

- The normal start action is sending one URL to the agent.
- The agent should run the workflow without requesting approval for every intermediate image operation.
- Exceptions should be described in plain language.
- The user must be able to locate the output files without understanding technical internals.

### Quality and integrity

- Image dimensions and file sizes must be measured from the actual saved files, not inferred.
- Originals must remain unchanged.
- The assistant must not silently substitute unrelated product images.
- The product's design and appearance must not be altered by background generation or cleanup.

### Reliability

- A partial failure must produce a clear report.
- Interrupted jobs must not leave a misleading success report.
- Re-running a job must not silently overwrite previously prepared files.

### Privacy and handling of images

- The user must be told whether images are sent to any external image-processing service.
- No image may be sent to an external service without a documented processing choice and appropriate user awareness.
- Credentials for private manufacturer portals are not part of this MVP.

### Maintainability

- The workflow must be testable on saved sample images and representative public product pages.
- Failures in page extraction, image selection, image processing and file saving should be distinguishable in the report.

## 10. Permissions and content-use rules

The salon states that it is an official representative of the manufacturers and has permission to use their product photography.

The assistant must still respect the actual scope of those permissions:

- only process photographs the salon is authorized to use;
- remove a watermark only when the salon's permission covers that edit;
- do not bypass access restrictions to acquire images;
- if the permission status for a particular source or watermark is unclear, keep the best permitted image and flag the issue.

## 11. Scope and release boundary

### Included in MVP 1

- Public URL input.
- Public browser-based product-gallery discovery.
- Download of accessible images.
- Automatic lead-photo selection.
- Main image preparation to JPG 600 × 800 px.
- Crop or side-background extension selected automatically.
- Secondary-image preparation to ≤ 2.5 MB each.
- Authorized and safe watermark cleanup.
- Local folder organization and source preservation.
- Completion report and exception reporting.

### Explicitly excluded from MVP 1

- WordPress access, Portfolio item creation, category assignment and publishing.
- Automated catalogue-page verification.
- Private manufacturer download portals.
- Bulk processing of multiple product URLs in one request.
- Autonomous scheduled processing.
- A public customer-facing web application.
- Automatic acceptance or publication without human review.

## 12. Success criteria

The MVP is successful when a user can provide a supported public product-page URL and, without manually editing the files:

1. receive one valid JPG lead image at exactly 600 × 800 px;
2. receive the useful, unique secondary gallery images, each ≤ 2.5 MB;
3. find the files in the correct brand/model folder;
4. recover the original downloaded files;
5. see a truthful report of the chosen lead photo, fallback status, processing method and any exceptions.

### Pilot evaluation

The pilot should use the Pronovias SUFI page and several other permitted public product pages that vary in image framing and gallery behavior.

For each test page, record:

- whether the gallery images were found and downloaded;
- whether the selected lead image met the visual criteria;
- whether the 600 × 800 composition preserved the important parts of the dress;
- whether each secondary image met the 2.5 MB limit;
- whether the correct files were saved;
- how much human correction was needed;
- total user time compared with the current 10–15 minutes per dress.

No numerical time-saving commitment is made before the pilot results are measured.

## 13. Acceptance criteria

A processing job is accepted as successful only if all applicable checks below pass:

- [ ] Brand and model are correctly identified or explicitly confirmed by the user.
- [ ] Relevant product-gallery images are obtained, or failures are reported.
- [ ] One lead image is selected; fallback use is identified.
- [ ] The lead file opens as a valid JPG.
- [ ] The lead image dimensions are exactly 600 × 800 px.
- [ ] The lead image does not unintentionally cut off the model or important dress details.
- [ ] Background extension, if used, has not changed the dress or model.
- [ ] Each secondary image preserves its original composition.
- [ ] Each secondary image is no larger than 2.5 MB.
- [ ] Watermark cleanup is performed only within the authorized scope.
- [ ] Original downloads are preserved unchanged.
- [ ] Files are saved in the correct brand/model output location.
- [ ] The final report accurately lists output files and exceptions.

## 14. Assumptions and open product decisions

The following are not fully specified yet. They must be resolved before the detailed specification or implementation.

| ID | Question | Current proposal |
|---|---|---|
| PD-01 | Where is the absolute local path to the `Victoriya` folder? | Set it once as a required user configuration; do not assume a drive letter. |
| PD-02 | What format should secondary images use? | Proposal: JPG for consistent website uploads, unless preserving another format is important. |
| PD-03 | Should the assistant download every unique, relevant product-gallery image? | Proposal: yes, all useful gallery images; exclude duplicates and unrelated assets. |
| PD-04 | How should existing files be handled? | Never overwrite; use unique names or a job-specific folder. |
| PD-05 | What exact permissions apply to watermark removal? | Confirm that salon permissions cover removal for the relevant manufacturer's images. |
| PD-06 | May cloud image-processing services be used? | Require transparent disclosure; choose local/cloud policy in TRD. |
| PD-07 | What file-name pattern should be final? | Proposal: `<Model>-main.jpg`, then numbered secondary files. |

## 15. Traceability to Discovery

| Discovery item | PRD coverage |
|---|---|
| Public URL as the input | FR-01, FR-03 |
| Browser-based retrieval of public gallery | FR-03 to FR-05 |
| Front-facing, full-length lead photo | FR-06, FR-07 |
| 600 × 800 JPG main image | FR-08, FR-09 |
| Crop or side-background extension | FR-09, FR-10 |
| Secondary images ≤ 2.5 MB | FR-11, FR-12 |
| Authorized watermark cleanup | FR-13; Section 10 |
| Exact local output hierarchy | FR-14, FR-18 |
| Preserve source images | FR-15 |
| Human review and truthful report | FR-16; Section 13 |
| WordPress outside first assistant | Section 11 |

## 16. Gate 1 — PRD Acceptance

| Gate 1 condition | Status |
|---|---|
| Product and user are clear | Complete |
| Problem and goals are defined | Complete |
| User workflow is described | Complete |
| Functional requirements are testable | Complete |
| Non-functional requirements are stated | Complete |
| Scope and non-goals are explicit | Complete |
| Success and acceptance criteria are defined | Complete |
| Open decisions are recorded | Complete |

**Gate 1 status: READY FOR PRODUCT-OWNER REVIEW — NOT YET ACCEPTED.**

After the PRD is accepted, proceed to **Stage 2 — TRD**. Do not start technical design or implementation before this gate is accepted.
