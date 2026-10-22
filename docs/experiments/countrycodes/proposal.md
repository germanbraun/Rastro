# Proposed transfer experiment: published country and currency codes

Status: **proposed; business-question approval and independent reference review pending**.
This proposal is not evidence that the method generalizes. No human approval or model evaluation is recorded.

The public-source profile is in `source-profile.json`, with the fetched file hashes and row counts. Downloaded CSVs
remain in ignored `data/raw/countrycodes-proposal/`. Both sources responded successfully over verified HTTPS:

- `datasets/country-codes`, `data/country-codes.csv`: 249 published entries in the observed snapshot.
- `datasets/currency-codes`, `data/codes-all.csv`: 449 published currency/entity rows in the observed snapshot.

Licensing, refresh policy and dataset versions must be reviewed before accepting the scope. The hashes identify
what was inspected; the mutable source URLs alone are not reproducible version pins.

## Scope to approve

Use only published ISO code and currency fields. "Country entry" means a row in the country-code dataset, including
territories, without deciding sovereignty. "Active currency row" means a source row whose `WithdrawalDate` is empty;
it is a dataset definition, not a claim about legal tender today. Link by published currency code, not country name.
Inspect and propose a parsing rule for fields containing multiple currency codes; keep missing keys and conflicting
currency descriptions visible instead of silently choosing a match.

## Business questions to approve

1. How many published country entries have at least one currency code matching an active row in the currency dataset?
2. For each published country code, which matching currency codes, names and minor units do the two sources report?
   Retain conflicting descriptions explicitly, without selecting one by opinion.
3. Which nonempty published currency codes have no active match in the currency dataset, and which entries use them?

Expected answer types are a number, a table, and an exception table. An empty exception table is allowed only when
independent source calculations establish it. Exact answers are not supplied by the semantic mapping itself.

## Execution and acceptance

After scope and definitions are approved, initialize a registered domain with `start-domain`; record approval
artifacts and adopt `method.lifecycle` and `method.source_manifest`. Use the same generic quality runner, ontology
checker, app template and experiment runner. Populate independent query expectations, then:

```bash
python layer/experiment.py countrycodes --expectations layer/countrycodes/query-checks.yaml --measure --publish
```

The command requires the registered domain and its services; this proposal does not register an unapproved domain.
Keep independently isolated B/D/C evaluators, original prompts, retries, source hashes and adjudications. Record
agent/person hours and interventions while the work occurs. A technical gate run does not establish human approval
or generalization. Repeat with a second independently approved domain without changing the skills before claiming
that the method transfers.
