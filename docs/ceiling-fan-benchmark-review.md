# Public ceiling-fan benchmark review

Date: 2026-09-17. Initial source audit, not a validation claim.

## Decision

Keep the product focused on ceiling fans. Pause FAN-01, preserve its assets, and establish matched experimental evidence before further simulation. No candidate below is yet confirmed fully reproducible. No company CFD-team support is required or assumed.

| Source | Evidence inspected | Gap / decision |
|---|---|---|
| Adeeb et al. (2016), Parametric Study and Optimization of Ceiling Fan Blades for Improved Aerodynamic Performance | Public journal PDF: three-blade ceiling fan, baseline dimensions and Table 1 experimental velocity values. Measurements are 1.5 m below the fan. | Audited: no-go with currently verified inputs; see detailed audit. Complete baseline blade shape, RPM correspondence, measurement component/uncertainty and test boundaries need verification. The experiment includes a duct: do not silently model it as an unobstructed room. CAD availability/licensing not established. |
| Chen et al. (2018), Experimental and numerical investigations of indoor air movement distribution with an office ceiling fan | Institutional full text: measured Haiku 60, diameter 1.5 m; 72/124/182 RPM; occupied-zone speed profiles. Section 2.2 explicitly says its three digital fans differ from the measured Haiku; four-station blade parameters are reported. | Useful room-flow methodology and reconstruction lead. Not an exact matched-geometry benchmark. Do not pair with another dataset merely because both involve Berkeley. Matching CAD and raw data not verified. |
| Liu et al. (2018), Detailed experimental investigation of air speed field induced by ceiling fans; Dryad DOI 10.6078/D1V67R | Public indexed dataset record identified. | Audited 2026-09-18: API metadata/manifest saved, CC0, two CSVs only and no CAD/README. CSV downloads returned 401/403; contents not imported. Conditions verified from paper. See ../benchmarks/ceiling-fan-dryad/README.md. |

## Primary sources

- [Adeeb journal PDF](https://www.jafmonline.net/article_1855_6ae07dcb33ec3b7c814df797cbda0f87.pdf), DOI 10.29252/jafm.09.06.25808; inspect sections 2/2.1, Figures 1–2 and Table 1.
- [Chen institutional full text](https://escholarship.org/content/qt37s8h4w4/qt37s8h4w4_noSplash_6590e9bf4cb2eeba7f0cfa45273b232c.pdf), DOI 10.1016/j.buildenv.2017.12.016; inspect sections 2.1–2.2 and Table 1.
- [Dryad dataset record](https://datadryad.org/dataset/doi%3A10.6078/D1V67R); associated paper DOI 10.1016/j.buildenv.2018.06.037. Record discovery is not file verification.

## Completed audit and next action

[Adeeb audit](adeeb-reproducibility-audit.md): no-go with currently verified inputs. Geometry and measurement-definition gaps prevent a defensible matched reproduction; figure access was unsuccessful. Preserve as methodology evidence.

Dryad audit completed: see [saved evidence and access status](../benchmarks/ceiling-fan-dryad/README.md). Next: bounded alternate CSV-source and matching Haiku geometry check; do not repeat failed Dryad endpoints. No solver launch until a reproducible specification exists. Experimental room-speed evidence alone cannot validate torque or blade-design predictions.

## Recovery completed, 2026-09-18

Both CSVs recovered from pinned author repositories; 5,760 single-fan points normalized and 20,160 two-fan values checked. Their hashes differ from Dryad, including after newline normalization. Matching blade geometry was not recovered. See [provenance, importer and decision](../benchmarks/ceiling-fan-dryad/README.md). This route is closed as a room-speed reference; the next product milestone is the agreed AI study-proposal layer, with solver execution still gated.
