# Literature and novelty audit

Search date: 23 September 2026. Search engines plus primary full texts; this is a scoped search, not proof that no equivalent result exists. PDFs/HTML were read locally, including relevant model sections. Local third-party copies are excluded from the public repository.

## Search clusters

- AI financial systemic risk, shared model providers, model homogeneity, operational resilience.
- Failover/fallback with systemic risk, liquidity, concentration, and model routing.
- Risk-aware LLM routing; batch-level routing; portfolio/covariance approaches to LLM ensembles.
- Fire-sale spillovers, indirect contagion, liquidity-weighted portfolio overlaps.
- Randomized load balancing, dependent rounding, indivisible decisions and quadratic objectives.

## Closest verified sources and boundaries

| Source | Established contribution relevant here | Boundary of this manuscript |
|---|---|---|
| [FSB (2024), The Financial Stability Implications of Artificial Intelligence](https://www.fsb.org/uploads/P14112024.pdf) | Third-party dependency, concentration, market correlation and model risk are recognized financial-stability concerns. | We do not claim discovery of AI concentration risk. |
| [Kleinberg and Raghavan (2021), Algorithmic Monoculture and Social Welfare](https://doi.org/10.1073/pnas.2018340118); [author preprint](https://arxiv.org/abs/2101.05853) | Collective consequences of using a common algorithm differ from its individual accuracy; matching-market analysis. | Our setting is exogenous endpoint removal and market-impact-weighted routing, not a new general monoculture claim. |
| [Greenwood, Landier and Thesmar (2015), Vulnerable Banks](https://doi.org/10.1016/j.jfineco.2014.11.006); [earlier full text](https://conference.nber.org/confer/2012/IFMs12/Greenwood_Landier_Thesmar.pdf) | Overlapping holdings and deleveraging create fire-sale spillovers; exposure and leverage matter. | Portfolio-network amplification is inherited. |
| [Cont and Schaanning (2017), Fire Sales, Indirect Contagion and Systemic Stress Testing](https://mfm.uchicago.edu/wp-content/uploads/2017/06/Cont_Schaanning_Fire-Sales-Indirect-Contagion-and-Systemic-Stress-Testing-2017.pdf) | Liquidity-weighted overlap matrix, indirect exposures, endogenous fire-sale rounds, thresholds and nonlinear effects. | We use a local linear response, not their full threshold model or their empirical bank calibration. |
| [Ong et al. (2024), RouteLLM](https://arxiv.org/abs/2406.18665) | Learning a cost-quality router from preference data. | We do not train a new capability router. The objective is the joint financial consequence of assignments. |
| [Hao et al. (2026), RACER](https://arxiv.org/abs/2603.06616) | Calibrated sets control the probability of excluding all optimal models. | Our second moment of aggregated financial error is a different risk object, with different assumptions and no distribution-free misrouting claim. |
| [Markovic-Voronov et al. (2026), Robust Batch-Level Query Routing](https://arxiv.org/abs/2603.26796) | Joint resource-constrained batch assignment with robust performance estimates and instance allocation. | Batch optimization and hard model capacities are not new. The distinction is cross-institution financial externalities, contingent eligibility, and explicit random-routing correction. |
| [Leytes (2026), Cyber-Financial Contagion](https://arxiv.org/abs/2609.10350) | Four-layer vendor/bank/interbank/customer network, operational impairment and clearing cascades. Sections III-V and VIII inspected. | Vendor-to-financial contagion is not new. This study changes the assignments after endpoint loss and quantifies the routing intervention. No claim to reproduce its reported GNN results. |
| [Meng and Chen (2026), Artificial Intelligence and Systemic Risk](https://arxiv.org/abs/2604.03272) | A preprint linking performativity, herding and cognitive dependency. | We neither reproduce nor validate its empirical claims; our result does not require endogenous adoption or those three channels. |
| [Gandhi et al. (2006), Dependent Rounding and Its Applications to Approximation Algorithms](https://doi.org/10.1145/1147954.1147956) | Established techniques for dependent integral assignments and degree constraints. | Our simple pair-swap heuristic is not a new dependent-rounding theorem. Independent conditional-expectation rounding has no hard-quota guarantee. |
| [Bertsimas, Teo and Vohra (1999), On Dependent Randomized Rounding Algorithms](https://doi.org/10.1016/S0167-6377(99)00010-3) | Dependence in rounding can improve integral optimization. | The general distinction between fractional and integral solutions is established. |

## Additional overlap leads

Search results for a concept/code project titled *Beyond Benchmark Rankings: Information-Aware and Risk-Aware Optimization of Large Language Model Ensembles* describe error-covariance portfolio selection. A primary citable paper with verified publication metadata was not located during this audit. It reinforces the decision not to claim novelty for covariance-aware model portfolios. Non-authoritative blog/tutorial examples of fallback chains were not used as research evidence.

## Claim supported by the scoped search

The manuscript proposes a specific synthesis: outage-contingent assignments weighted by a financial response matrix, exact indivisible-routing risk with an effective-exposure granularity diagnostic, finite-agent derandomization bounds, and a quota-preserving implementation evaluated against identical endpoint-count controls. The closest inspected papers do not present this complete formulation and experiment. This is a bounded methodological contribution, not a claim of an undiscovered field, patentability, industry-wide validation, or guaranteed conference acceptance.

## Issues discovered and resolved

- Generic AI herding and AI-vendor contagion topics were already covered; those were rejected as novelty claims.
- Fractional objective values cannot be presented as implemented random-route risk; an exact correction is included.
- A feasible convex objective is not a minimization lower bound; the implementation now constructs a feasible dual supporting-hyperplane lower bound.
- More diversity need not lower risk when model errors differ; the common-best baseline is retained even where it wins.
- API tasks have an exact deterministic solution. That control is disclosed; this workload demonstrates the error-propagation experiment, not a reason to replace arithmetic software with an LLM.
