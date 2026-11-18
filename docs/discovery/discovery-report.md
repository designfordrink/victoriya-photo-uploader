# Stage 0 — Discovery Report
## Victoriya Photo Assistant

**Status:** Draft — Gate 0 pending user acceptance  
**Date:** 2026-11-18  
**Repository:** [designfordrink/victoriya-photo-uploader](https://github.com/designfordrink/victoriya-photo-uploader)  
**Process:** [Standard Project Development Pipeline — Github Stage-Gated](https://app.notion.com/p/3f1937a9fdd181dbb1bae975bd77c4f7)

---

## 1. Context

The Victoriya bridal and evening dress salon regularly adds new dresses to its WordPress website. The current work is performed manually:

1. Find product photographs on a manufacturer's public product page.
2. Download the images.
3. Convert incompatible formats (for example, WebP) to JPG.
4. Remove watermarks using an inpainting tool where permitted and appropriate.
5. Prepare a vertical lead image at **600 × 800 px** in Photoshop. Depending on the source composition, either crop carefully or extend the background on the left and right.
6. Upload the dress as a WordPress Portfolio item, assign the required categories, publish it and inspect the brand catalogue page.

The owner reports processing approximately **5 dresses per week**, with **10–15 minutes per dress** spent on the current preparation flow.

The salon is an official representative of the brands and the owner confirms that it has permission to use their product photography. The exact permissions applicable to editing/removing every type of watermark must still be respected.

## 2. Problem statement

Preparing manufacturer photographs for the salon website is a repetitive manual task. It requires switching between browser downloads, format conversion, image cleanup and Photoshop. The most difficult parts are watermark cleanup, extending backgrounds and choosing a crop that preserves the complete dress and model.

The desired experience is to give an AI agent a **public product-page URL** and have it acquire and prepare the photographs with minimal manual steps.

## 3. Goal

Build the first local photo-preparation assistant so that a salon employee can:

- submit a public dress product-page URL to an AI agent;
- let the agent locate and download the publicly available product-gallery images;
- let the agent select the best lead photograph and prepare it automatically;
- receive the remaining product images in a web-ready format and file size;
- find all prepared files in a predictable local folder structure;
- review the completed result and any exceptions before using it on the salon website.

The first assistant is intended to prepare files. It does **not** publish to WordPress in this first stage.

## 4. Users

**Primary user:** salon owner or employee responsible for preparing and adding dress cards to the website.

The user is not expected to use image-editing software or write commands for each dress. The intended interaction is conversational: provide a link, receive the processed files and a concise report.

## 5. Main user scenario

Example source page:

- Pronovias — SUFI: https://www.pronovias.com/int_en/bridal-dress-a-line-sweetheart-neckline-lace-sufi

Expected interaction:

1. User sends the product-page URL to the agent.
2. Agent opens the public page in a real browser, identifies the product and brand, and inspects the product gallery.
3. Agent downloads accessible original product-gallery images, avoiding duplicate thumbnails and unrelated imagery.
4. Agent identifies the lead photo:
   - normally the first/main product image;
   - preferred visual criteria: model facing forward, full length, dress clearly visible and not cut off;
   - if the first image does not meet these criteria, evaluate the other gallery images;
   - if no image fully meets the criteria, choose the best available alternative and clearly flag that it is a fallback.
5. Agent prepares the lead photo as a **JPG at exactly 600 × 800 px**:
   - choose a careful 3:4 crop when the source framing allows it;
   - otherwise extend the background at the sides where feasible;
   - preserve the model's head, feet, dress hem/train and important garment details;
   - do not invent or alter parts of the dress to make the framing fit.
6. Agent processes the remaining product-gallery photos:
   - preserve their original composition and aspect ratio;
   - keep each output file at **2.5 MB or less**;
   - remove watermarks only where the salon's rights and the image context permit a safe edit;
   - if cleanup would damage the image or permission is unclear, keep the best legitimate version and flag it.
7. Agent writes prepared files into the agreed `output` folder and returns a short processing report.

## 6. Output folder structure

The user specified this folder structure:

```text
Victoriya/
└── Collections/
    └── wedding/
        └── Pronovias/
            └── SUFI/
                └── output/
```

The same pattern should work for other collections, brands and dress models.

**Configuration still needed:** the absolute local path that contains the `Victoriya` folder. The agent must not assume a drive letter or silently save elsewhere.

**Proposed safety rule:** downloaded originals are preserved separately from processed outputs and are never overwritten. A sibling `source/` folder is a candidate location for originals; confirm in the detailed specification.

## 7. Functional boundaries

### In scope for the first assistant

- Accept a public product-page URL.
- Open public product pages in a real browser, including pages whose gallery is loaded dynamically.
- Discover and download accessible product-gallery images.
- Identify the lead image using the user's composition criteria.
- Convert the lead image to JPG, exactly 600 × 800 px.
- Select crop versus side-background extension automatically.
- Process additional gallery images to a maximum of 2.5 MB each.
- Perform authorized watermark cleanup where it is technically safe.
- Save files into the configured folder structure.
- Produce a processing report identifying the selected lead photo, fallback choices, skipped files and warnings.

### Out of scope for the first assistant

- Logging into closed manufacturer portals or using private login/password links.
- Bypassing access restrictions, CAPTCHAs, paywalls, anti-bot measures or geographic restrictions.
- Uploading images to WordPress, creating Portfolio items, assigning categories or publishing.
- Automatically checking the live WordPress catalogue page.
- Processing evening-dress collections until the wedding-dress flow has been validated (the folder design should not prevent adding them later).

## 8. Initial platform assessment

**Hermes Desktop is a strong candidate for the agent interface, not yet a final architecture decision.**

The official Hermes documentation currently describes:

- a native desktop app for Windows, macOS and Linux;
- browser automation using a real Chromium browser;
- terminal and local-file tools;
- reusable skills that can package the repeatable workflow.

Sources:
- [Hermes Desktop](https://hermes-agent.nousresearch.com/docs/user-guide/desktop)
- [Browser Automation](https://hermes-agent.nousresearch.com/docs/user-guide/features/browser)
- [Creating Skills](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills)
- [Tools & Toolsets](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools)

**Preliminary direction:** keep image preparation in a separate, testable local tool and let Hermes (or another compatible agent) orchestrate the steps. This avoids tying core image operations to one AI desktop product.

The Pronovias SUFI example page is publicly viewable, but its gallery images were not exposed in the static text extraction used during discovery. The implementation must therefore test gallery retrieval in a real browser and cannot assume that reading the page's raw text is sufficient.

## 9. Constraints

- Main image dimensions are exact: **600 × 800 px**.
- Each secondary image must be **≤ 2.5 MB**.
- Main-image composition is more important than filling the 600 × 800 canvas by aggressive cropping.
- Background extension must be limited to the background; garment details must remain faithful to the source.
- Original downloaded images must remain recoverable.
- Output must be local and follow the exact user-provided folder hierarchy.
- Product pages may use JavaScript, lazy-loaded galleries, responsive image variants or changing page structures.
- The agent only works with images it can access through the public page and normal browser behavior.
- Watermark cleanup must stay within the salon's actual usage and editing permissions.

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| A manufacturer changes its page or gallery structure | Use browser-based extraction; test against representative pages; report when images cannot be found. |
| Gallery contains thumbnails, duplicates or non-product images | Detect duplicates and prioritize the product gallery; record skipped items. |
| Crop removes the head, feet, train or garment detail | Use full-length/composition checks and conservative crop boundaries; flag low-confidence results. |
| Background generation changes the dress | Restrict generation to masked side-background areas; preserve the original subject; make human review part of the release workflow. |
| Watermark cleanup leaves visible artifacts | Use quality checks; do not force cleanup when it damages the photograph; report exceptions. |
| Source images are too small or low quality | Do not pretend upscaling restores detail; flag source-quality limitations. |
| Compression below 2.5 MB harms quality | Measure actual file size in code and use controlled quality settings; report unusually aggressive compression. |
| Local path or permissions are wrong | Configure and validate the base folder before processing; never silently choose another location. |
| Remote image services expose brand photography to a third party | Decide in TRD whether image processing is local or cloud-based and disclose any external transfer. |

## 11. Success criteria for the first pilot

The first pilot should use several real, permitted product pages, including the SUFI example.

A dress is successfully prepared when:

- the agent retrieves the relevant product-gallery images without bypassing access controls;
- a main photo is selected according to the agreed criteria, or a fallback is clearly marked;
- the main output is a valid JPG with dimensions exactly 600 × 800 px;
- the full model and dress remain visible, with no accidental crop of important details;
- every additional output image is no larger than 2.5 MB;
- output files appear in the correct brand/model folder;
- originals remain untouched and available;
- the report identifies failures and uncertain edits rather than hiding them.

The current manual baseline is about 50–75 minutes per week for five dresses. Time saved will be measured during the pilot; no savings target is asserted before testing.

## 12. Open questions for later stages

These questions do not prevent documenting the discovery, but must be resolved before implementation:

1. What is the absolute local base path for the `Victoriya` directory?
2. Should secondary images always be converted to JPG, or should their original format be retained when suitable?
3. Should all product-gallery images be downloaded, or is there a maximum number of secondary photos?
4. What filename pattern should be used for the lead photo and secondary images?
5. Does the salon's permission explicitly include removal of the watermark types found on the manufacturers' public product photos?
6. What image-processing services may be used: local-only, cloud services, or either (with disclosure)?
7. What is the preferred fallback when the website blocks normal public image downloads?

## 13. Preliminary decisions

| Topic | Preliminary decision |
|---|---|
| User interaction | Send a public product-page URL to an AI agent. |
| Candidate agent interface | Hermes Desktop, subject to technical validation. |
| Image-processing architecture | Separate local processing tool, callable by the agent. |
| Main image | First image by default if it meets the full-length frontal criteria; otherwise best available alternative. |
| Main output | JPG, exactly 600 × 800 px. |
| Main framing | Crop if safe; otherwise extend side background. |
| Secondary images | Preserve composition; each output ≤ 2.5 MB. |
| Output path | `Victoriya/Collections/wedding/<Brand>/<Model>/output/`. |
| Originals | Preserve separately; never overwrite. |
| WordPress | Not included in the first assistant. |
| Access | Public pages only; no login or access-control bypass. |
| Acceptance | Human reviews pilot output before it is used on the live website. |

## 14. Gate 0 — Discovery Accepted?

| Gate 0 condition | Status |
|---|---|
| Problem is understood | Complete |
| Primary user is identified | Complete |
| Main user scenario is described | Complete |
| Main output requirements are known | Complete |
| Constraints and major risks are identified | Complete |
| Critical unknowns are recorded | Complete |
| Scope of the first assistant is bounded | Complete |

**Gate 0 status: READY FOR USER REVIEW — NOT YET ACCEPTED.**

After user acceptance, proceed to **Stage 1 — PRD**. Do not start TRD or implementation before the PRD is reviewed and accepted.
