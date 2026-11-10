# Caldova shared data assets for the L400 workshop

The `L300-TW-Data` directory name is retained for source compatibility. These files
supply the **core** data profile for [Exercise 1](../../Instructions/Labs/01-trusted-context.md)
in [L400: Deliver real impact with Agents](../../index.md); they are not a separate
90-minute L300 delivery in this repository.

## Contents

- `data/core/`: six source CSV files, 318 rows in total.
- `notebooks/curate_caldova_tables.ipynb`: learner curation notebook.
- `event-simulator/`: replay templates, publisher, dependency and KQL setup/verification.
- `agent/`: business-context instructions and ontology entity descriptions.

The original notebook date-normalization repair remains learner work. Preserve the
source fixtures and use the exercise's actual replay cohort for validation. Optional
L300 knowledge documents and hoster-only VM requirements are not required for this workshop.

The separate qualification-repair fixture is in `Labfiles/04-caldova-agents` at the
repository root. Do not combine its identifiers, dates, quantities or policies with
this core dataset.

See [setup](../../Instructions/Setup.md). Integrity and provenance records are in
`tools/shared-assets.lock.json` and `tools/development-assets.lock.json`; source
license notices are retained in `licenses`.
