> **PAUSED — 2026-09-17:** Preserved ducted-fan research, not the active ceiling-fan validation reference. Historical next steps below are inactive. Do not resume by default; read ../../docs/PROJECT_PLAN.md.

# FAN-01 benchmark workspace

Selected for independent aerodynamic validation; **not yet simulated or validated**. The [geometry checkpoint](GEOMETRY.md) now includes a recovered rotor, OpenFOAM-checked STL and reconstructed inner passage.

## Sources and attribution

FAN-01: Low pressure Axial Fan in a short Duct, Krömer, Junger, Becker, Kaltenbacher, Czwielong and Schoder. [Pinned Zenodo record](https://zenodo.org/records/10787093), DOI 10.5281/zenodo.10787093, CC BY 4.0. Preserve attribution for adapted or redistributed data. Original downloads remain unchanged; `extracted/` contains their contents.

Dataset description: Schoder and Czwielong, [Dataset FAN-01](https://arxiv.org/abs/2211.12014), locally saved as `dataset-paper.pdf`. Original experimental publication: Zenger et al., [SAE 2016-01-1805](https://doi.org/10.4271/2016-01-1805).

Published numerical study: Schoder, Junger and Kaltenbacher, [Acta Acustica 4, 22 (2020)](https://doi.org/10.1051/aacus/2020021), [accessible copy](https://pdfs.semanticscholar.org/286b/b49e1b256fd952c02e16a82df1918661442e.pdf).

## Files and reproduction

- `source-manifest.json`: four downloaded aerodynamic files, pinned URLs, byte counts, repository MD5 and independently calculated SHA-256.
- `zenodo-record.json`: full source metadata, including files not downloaded.
- `fetch_sources.py`: fetch/verify the four selected files and safely extract archives. Acoustic recordings are outside this first milestone.
- `experimental-reference.json`: 20 raw characteristic points and time-averaged LDA channels, plus explicit source-unit warnings.
- `extract_reference.py`: regenerate that JSON using Python and `reader-requirements.txt`. The installed Windows reader dependencies are isolated in `.reader-deps/`; they are not an application runtime requirement.
- `cad-audit.json`: initial Gmsh IGES import counts/bounds. Import found 3,864 surfaces and zero solids; this is not a ready fluid volume.
- `SPECIFICATION.md`: proposed test, source facts, unresolved definitions, validation plan and run limits.

Commands from this folder: `python fetch_sources.py`; install reader requirements into `.reader-deps` for the Python platform being used, then `python extract_reference.py`. The current local reader installation is Windows-specific; WSL users need their own compatible reader packages.
