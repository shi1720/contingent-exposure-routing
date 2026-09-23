# Technical review and reproducibility record

Review date: 23 September 2026. This is an internal verification record, not an independent referee report.

## Mathematical checks

- The financial response requires spectral radius below one; the network generator sets and checks this condition. The measured outcome is squared normalized price displacement.
- Endpoint moments are uncentered. Bias is included, and a common error component is invariant to routing.
- The exact random-routing formula uses independent institution assignments chosen independently of evaluated errors. It is checked by exhaustive enumeration of small instances.
- The effective-exposure formula uses the response columns, not merely institution size weights. Size concentration agrees only in the aligned-column special case.
- Conditional-expectation rounding has a finite-agent bound under row-wise eligibility, but does not enforce coupled quotas.
- Quota swaps preserve counts, unchanged primary assignments, and optional heterogeneous eligibility. The update formula is checked against full objective recomputation. The method is local search, not a global solver.
- The relaxation comparison uses a feasible dual to the linear supporting hyperplane. A feasible primal value is never labeled a lower bound. Floating-point bounds are not interval certificates.
- The spectral uncertainty envelope and the two-endpoint unequal-quality example follow directly from their stated assumptions.

## Experimental checks

- The locally frozen protocol and task hashes match the archived files. This is not external preregistration.
- The 11,340 synthetic rows come from 60 networks. Uncertainty resamples network aggregates; removal scenarios are not treated as independent networks.
- The error panel has 256 tasks and four endpoints. Calibration and held-out tasks are disjoint, and policies use calibration moments only. Paired task resampling holds those policies fixed.
- Raw responses and failed outputs are retained. API observations are a shared-advice replay on constructed arithmetic tasks. They are neither real financial deployments nor independent provider outages.
- The exact arithmetic control dominates the model-only calculation. Poor endpoint performance and the 16 post-collection probes are disclosed. The replay does not establish representative model capabilities.
- Exploratory comparators and tail diagnostics are distinguished from the primary comparison. The common-best policy is retained despite outperforming the quota-constrained method under different counts.
- Gaussian and standardized Student-t checks agree with the analytical second moment within Monte Carlo variability. Tail improvements are not implied by variance reduction.

## Artifact checks

- 48 mathematical and numerical tests pass.
- A separate source copy runs the complete offline pipeline using archived API responses, without any API requests.
- The manuscript compiles with resolved references and no overfull boxes. All 15 pages were rendered and inspected; six figures and three tables are included.
- Raw credentials, local third-party literature copies, temporary files, and private submission notes are excluded from the public repository.
- The arXiv source archive is separately compiled after extraction. Source readiness is not an arXiv submission or endorsement.

## Remaining scientific work

External validation of the financial response and state-dependent endpoint errors would be needed for operational use. Richer tasks, independent vendors, realistic capacities, changing liquidity, and more powerful assignment algorithms are research extensions. No search can establish the absence of all equivalent prior work, and conference acceptance remains an editorial decision.
