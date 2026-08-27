# PUMKIT Canonical Asset Extraction — Pass 01

## Capability status

- `CANONICAL_ASSET_EXTRACTION = VERIFIED_FOR_PRIMARY`
- `PRIMARY_PUMKIT_ASSET_APPROVED = YES`
- `FRONTEND_CHARACTER_INTEGRATION = UNBLOCKED`
- `NOVEL_POSE_RECONSTRUCTION = EXPERIMENTAL / NOT_REQUIRED_FOR_FRONTEND`
- `LOCAL_REFERENCE_EDIT_PIPELINE = NOT_VERIFIED`
- `MULTI_REFERENCE_CONDITIONING = PREPARED / NOT_EXECUTED`
- `REGIONAL_REPAIR = NOT_REQUIRED_FOR_PRIMARY`
- `INDEPENDENT_QA = PASSED_FOR_PRIMARY_EXTRACTION`

## Approved asset

`Frontend-Designs/Pumkit-Frontend-Design/assets/pumkit/pumkit-primary.png`

This is a newly exported transparent-background asset created from canonical source pixels. It is not a full concept sheet and is not a rectangular sheet crop in the frontend.

## Source provenance

- Source filename: `IMG_1168.png`
- Source path: `Frontend-Designs/Pumkit-Frontend-Design/Concept-Art_and_references/IMG_1168.png`
- Source dimensions: `1199 × 1312`
- Source SHA-256: `39f3b7e182ab95ea60b39dcd7eff547e9135901dac4a28570848d1bfb33333ee`
- Crop coordinates, native pixels, XYXY: `[378, 74, 900, 690]`
- Output dimensions: `474 × 582`
- Output SHA-256: `8df09702cb934f88b77e6e3f567da3881084e102b3c23895280be3497649a5b6`
- `GENERATIVE_MODIFICATION = FALSE`

## Extraction method

`SOURCE → EXPLICIT NATIVE CROP → LIGHT-PAPER COLOR-DISTANCE MASK → MEDIAN FILTER → LOW-RADIUS GAUSSIAN EDGE SOFTENING → ALPHA ATTACHMENT → TRANSPARENT-BOUNDS TRIM → LOSSLESS PNG`

Original foreground RGB pixels are preserved. No face, eyes, ears, markings, limbs, paws, tail, fur, or proportions were redrawn or generatively changed.

The extraction script is reproducible at `scripts/media/pumkit_extract.py`.

## QA evidence

Generated automatically under:

`Frontend-Designs/Pumkit-Frontend-Design/assets/pumkit/pumkit-primary-qa/`

- `white.png`
- `black.png`
- `gray.png`
- `bright.png`
- `source-overlay.png`
- `contact-sheet.png`

The white, black, gray, and bright-background views expose fringe, halos, matte contamination, and missing edges. The source overlay verifies the extracted character against its source position.

## Primary QA result

The approved extraction retains:

- canonical compact puma-cub anatomy
- oversized layered ears and warm inner-ear planes
- amber feline eyes and dark pupils
- forehead diamond/chevron marking system
- articulated grounded paws
- full curved tufted tail
- charcoal painterly fur and warm value variation

A first crop was rejected because residual sheet fragments appeared below the contact shadow. The crop boundary was tightened from `[378, 74, 900, 724]` to `[378, 74, 900, 690]`, the full QA set was regenerated, and the residual fragments were removed without changing character pixels.

## Primary fidelity score

All dimensions below scored 4/4 in actual visual inspection:

- `SILHOUETTE_FIDELITY`
- `HEAD_BODY_PROPORTION`
- `EAR_FIDELITY`
- `EYE_FIDELITY`
- `FACE_FIDELITY`
- `MARKING_FIDELITY`
- `LIMB_FIDELITY`
- `PAW_FIDELITY`
- `TAIL_FIDELITY`
- `COLOR_FIDELITY`
- `FUR_SURFACE_FIDELITY`
- `STYLE_FIDELITY`
- `EXPRESSION_FIDELITY`
- `RECOGNIZABILITY`
- `NON_GENERICITY`
- `EDGE_CLEANLINESS`

## Secondary pose attempts

Initial pose-strip crops were rejected after QA revealed neighboring specimen fragments. Those candidate files were deleted and are not promoted. Additional poses require individually bounded source analysis.

## Frontend integration

The approved primary asset is integrated compositionally, not as a concept-sheet card:

- hero silhouette overlaps the nocturnal composition and typography
- dossier image sits inside orbital annotation geometry
- sensory section uses the real canonical character within detection rings
- liquid stage uses the canonical asset as the solid-state source of the transition
- behavioral stage uses the real canonical specimen on the authored plane
- footer uses the character as a resting closing composition

Unavailable alternate states are not replaced with fabricated poses. The current frontend uses the verified primary only where its neutral pose remains semantically appropriate.

## Novel reconstruction status

No generative character reconstruction was run in this pass. Novel pose reconstruction remains experimental and does not block the frontend. The preferred future local candidate is Qwen-Image-Edit with a reviewed native workflow; hosted 9Router edit models remain optional experiments and are not treated as local/open capability evidence.
