# Adeeb ceiling-fan reproducibility audit

Date: 2026-09-17. Decision: **NO-GO for a matched experimental reproduction with currently verified inputs.** This is an evidence-access decision, not a rejection of the research.

## Verified source facts

[Journal paper](https://www.jafmonline.net/article_1855_6ae07dcb33ec3b7c814df797cbda0f87.pdf), DOI 10.29252/jafm.09.06.25808. Page numbers below are printed journal pages.

| Field | Reported value / status | Page |
|---|---|---|
| Rotor | 1.4224 m diameter; three blades, 120° spacing | 2907 |
| Blades | 0.568 m span; approximately 0.001 m thick | 2907 |
| Room | 6.5 × 6.5 × 3.5 m | 2907 |
| Installation | Fan 2.5 m above floor; duct diameter 1.56 m | 2907 |
| Samples | 1.5 m below fan; 14 radial positions, 0.03–0.81 m; four directions | 2907–08 |
| Statistic | Maximum reading after two minutes; directional means tabulated | 2907–08 |
| Simulation | 300 RPM, 288 K, 101325 Pa; stationary/rotating domains; no-slip walls | 2909 |
| Geometry description | Elliptical variant construction; optimization ranges are not explicitly assigned to the tested baseline | 2908, 2910 |

[Publisher record](https://www.jafmonline.net/JournalArchive/article_1855.html) lists PDF/XML, no CAD attachment, and displays CC BY-NC 4.0. Public access alone does not establish permission to redistribute material within a commercial product.

## Reproduction assessment — our conclusions

- **Known:** overall dimensions and sampling layout above.
- **Reconstructable only by inference:** nominal sample height is 1.0 m above the floor. This does not resolve probe orientation or time statistic.
- **Unverified essentials:** complete baseline blade outline, chord distribution, camber/twist, hub and attachment geometry; duct length/end positions and its representation in CFD; correspondence between experimental RPM and simulation RPM; measurement uncertainty and exact velocity component.
- A radial span and swept diameter do not uniquely determine the hub or blade solid. Do not derive a supposedly exact hub by subtraction.
- Maximum-based observations cannot automatically serve as time-mean RANS targets. Directional averaging does not remove that mismatch.
- Geometry optimization ranges cannot be substituted for the tested baseline without a documented mapping.
- Torque predictions in a design study do not supply independent measured torque validation.

## Inspection limits and stopping decision

Read accessible PDF text through the geometry, experiment, computational setup and validation sections; checked the publisher files and searched the exact title/DOI for geometry supplements. Web screenshots failed; a local PDF retrieval returned HTTP 403. Figure 1 could not be visually audited. Therefore missing dimensions are **not verified**, rather than asserted absent from every possible source. No CAD or experimental dataset was acquired.

Do not spend meshing/solver time on a guessed reproduction. Retain this as a methodology reference. No new solver run, code change or change to archived cases occurred.

## Concrete next action

Inspect the existing Dryad ceiling-fan lead (DOI 10.6078/D1V67R): retrieve its file manifest and README, establish the fan model, experimental conditions and whether matching blade geometry is available. Record an explicit decision. If it provides measurements only, label it room-flow evidence; do not call it blade-design validation or start a surrogate fan run. FAN-01 remains paused and company CFD-team assistance remains unavailable.
