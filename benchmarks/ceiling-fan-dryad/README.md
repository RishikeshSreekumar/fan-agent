# Ceiling-fan experimental reference: Dryad D1V67R

Checked 2026-09-18. **Author-version CSVs acquired and checked; Dryad-version CSVs remain unavailable; no matched blade geometry.**

## Verified manifest

[Dryad source](https://datadryad.org/dataset/doi%3A10.6078/D1V67R), version 31429, lists exactly two files: Single_Fan.csv (68,839 bytes) and Two_Fan.csv (239,147 bytes). There is no CAD or README attachment. The API declares CC0-1.0. Saved dataset.json and files.json preserve repository metadata and expected SHA-256 hashes; acquisition-status.json distinguishes expected files from acquired files.

API downloads returned 401. Public browser links, session retries and zip delivery returned 403; preview returned 500. These failures apply to the Dryad delivery only. Alternate author-source acquisition is recorded below.

## Experimental specification

[Institutional paper](https://escholarship.org/content/qt2mk3n264/qt2mk3n264_noSplash_de02101012eb8ed43abfd4ebb4e2d627.pdf), sections 2.1–2.3 and Table 2:

| Item | Specification |
|---|---|
| Fan | Haiku H-Series, 1.5 m diameter |
| Room | 5.6 × 4.3 × 2.6 m |
| Blade height | 2.3 m above floor |
| Rotation | Clockwise viewed downward; downward airflow |
| Samples | 15 × 12 grid; 0.35 m spacing; heights 0.1, 0.6, 1.1, 1.7 m |
| Observable | Omnidirectional speed, three-minute average of 90 records |
| Instrument accuracy | ±0.02 m/s ±1.5% of reading |
| Speed levels 1–7, RPM | 36, 71, 86, 122, 157, 166, 176 |
| Electrical power, W | 2, 4, 5, 9, 17, 20, 23 |

## Engineering decision

**GO for retaining a room-speed experimental reference; NO-GO for launching a matched blade-resolved validation case.** Geometry is not supplied by this dataset. A manufacturer's appearance model would still require checking against the tested blade and variant.

The following are our methodological requirements, not additional source claims:

- Compare matching locations and operating conditions only after verifying the CSV coordinate convention and actual fan position. Do not assume geometric room center from a prose description.
- The measured mean speed is not an axial velocity component. Do not integrate it into downward CMM or CFM: direction is missing.
- Mean instantaneous speed and magnitude of the mean velocity differ in fluctuating flows. State that limitation in any steady-RANS comparison.
- Electrical input power is not aerodynamic shaft power; dividing it by angular speed would not validate blade torque.
- A model calibrated using these measurements must be tested on held-out conditions. Fitting and validating against the same observations is not independent validation.
- No CSV columns, numerical residuals or experimental error statistics have been inferred from inaccessible files.

## Recovered author dataset — 2026-09-18

Both CSVs were recovered from the authors' public Berkeley repositories:

- [Single fan](https://github.com/CenterForTheBuiltEnvironment/single-fan/tree/69f19e27714043030d7dc27f2c0c1167ea7d45d7)
- [Two fans](https://github.com/CenterForTheBuiltEnvironment/two-fans/tree/63a1ae3d8b24711574252bc8d40e6b4e3edd09c9)

Original files, parsing source and repository licenses are retained in author-source/. Author-source-provenance.json records pinned commits and SHA-256 values. Neither original nor LF/CRLF-normalized bytes match the expected Dryad hashes. Treat this as a separately versioned author dataset; numerical equivalence to Dryad is unknown. Do not transfer the Dryad CC0 designation automatically to the GitHub files; the repository licenses are preserved alongside them. No author R code is integrated into the application.

Run `python3 prepare_reference.py` in this directory to reproduce single-fan-points.csv and data-checks.json. The independent Python importer checks source hashes, dimensions, block labels, finite nonnegative values and unique single-fan locations. It recovers 5,760 single-fan points and checks 20,160 two-fan values. Coordinates follow the author visualization's centimetre grid and row reversal; this does not establish the fan-center location relative to that grid. Arithmetic sample means are not whole-room area averages.

## Matching-geometry search decision

Checked the [manufacturer toolbox](https://learn.bigassfans.com/), manufacturer support/product search results and [manufacturer BIM listings](https://www.bimobject.com/en-us/bigassfan?location=us). The toolbox advertises CAD/BIM resources, but its JavaScript entry point did not expose a verified matching file in this audit. The inspected BIM listing includes 52-inch Haiku products, which are not the tested 60-inch H-Series. No authenticated account, contact request or external message was used. No matching engineering blade geometry was recovered; this does not establish that none exists.

**Close this route as an acquired experimental room-speed reference, not the selected blade-validation benchmark.** Do not keep retrying the same sites or scale an unrelated 52-inch model and label it validated.

## Next product milestone

Proceed with the already-agreed first AI milestone: plain-language ceiling-fan request to a structured study proposal, validated by the existing deterministic controls. Inspect the upstream Foam-Agent interfaces and current app schemas, then implement proposal generation with an explicit qualification gate. Benchmark discovery must no longer indefinitely postpone this independent product feature. No automatic solver launch or physics rewriting. Matching experimental blade geometry remains an unresolved engineering dependency, recorded rather than hidden.
