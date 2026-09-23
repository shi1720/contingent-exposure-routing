# FM27 contributed lecture: 15 minutes plus discussion

**Title:** Contingent Exposure Routing for Financial AI: Outage Risk and the Cost of Indivisible Decisions

**Speaker:** Shivam Gupta, Independent Researcher

1. **0:00–1:30 — Financial question.** Availability survives an outage, but the allocation of shared decision errors changes. Show Figure 1. Distinguish request counts from financial exposure.
2. **1:30–3:00 — Financial model.** Explain the response matrix A, uncentered error moment S, endpoint eligibility, and the quadratic price-displacement objective. State the local-linear assumption.
3. **3:00–5:00 — Contingent concentration.** Prove the equal-primary example in two lines. Show the growing-outage regime and explain why it is not a frequency estimate.
4. **5:00–8:00 — Main implementation result.** Derive the exact independent-routing premium by separating diagonal and off-diagonal terms. Introduce effective-exposure granularity. Use the orthogonal example to show why more institutions need not close the fractional gap.
5. **8:00–10:00 — Executable control.** Explain conditional-expectation rounding, its quota limitation, and the separate quota-preserving swap implementation. Show the dual lower-bound logic.
6. **10:00–12:00 — Synthetic evidence.** Present the 60-network matched-count comparison, uncertainty units, and common-error/homogeneous negative controls.
7. **12:00–13:30 — Recorded API replay.** Present the smaller held-out benefit and the common-best comparison. Explain the shared-advice assumption, poor arithmetic, and exact deterministic control.
8. **13:30–15:00 — Operational use and open questions.** Describe an exposure-aware contingency router. State the missing empirical calibration and state-dependent outage data. End with the actionable distinction: validate the implemented assignment law, not only its average allocation.

## Questions to prepare for

- What is new relative to portfolio theory, load balancing, and fire-sale networks? The outage-contingent financial assignment formulation, exact implementation diagnostic, and evaluated matched-count intervention; the mathematical tools themselves are established.
- Does this predict crashes? No. It quantifies a specified local quadratic displacement measure.
- Why use an LLM for a task with an exact solution? The task supplies an auditable error panel. An exact calculator is the superior execution policy; the model experiment is not a product recommendation.
- Is the rounding guarantee quota-preserving? No. The paper explicitly separates the guarantee from the quota-preserving heuristic.
- What does the confidence interval cover? Synthetic generator variability across networks, or held-out task variability conditional on fitted policies. Neither is a confidence interval for real systemic risk.
- Can institutions coordinate? This prototype assumes a platform or supervisor can evaluate a joint allocation. Decentralized incentives and privacy-preserving coordination remain open.
