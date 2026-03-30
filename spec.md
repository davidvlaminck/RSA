# Project Specification — AI Context Summary

## Contents

- [Purpose](#purpose)
- [Project in One Paragraph](#project-in-one-paragraph)
- [Business Goal](#business-goal)
- [Scope](#scope)
- [Domain Context](#domain-context)
- [System At a Glance](#system-at-a-glance)
- [Guiding Principles](#guiding-principles)
- [Audience](#audience)
- [Repository Map (High Level)](#repository-map-high-level)
- [Where to Continue Reading](#where-to-continue-reading)

## Purpose

This file is a compact project summary for fast context loading by humans and AI tools.
It answers: what the project does, where it fits, and which constraints define it.

For detailed requirements and engineering specifics, use:
- `analysis.md` (requirements, acceptance criteria)
- `implementation_details.md` (developer implementation patterns)
- `architecture.md` (execution model and runtime architecture)

---

## Project in One Paragraph

This repository contains a Python-based reporting service for infrastructure and asset data.
It runs many report classes from `Reports/`, queries ArangoDB and PostGIS, and publishes results as Excel files to OneDrive/SharePoint. The platform is built for daily unattended runs, with reliability, traceability, and consistent output behavior as primary goals.

---

## Business Goal

- Provide reliable, repeatable data-quality and operational reports.
- Consolidate reporting logic in one service while supporting multiple datasource types.
- Reduce manual follow-up by automating report generation, history tracking, and notifications.

---

## Scope

### In Scope
- Report execution from modular Python report definitions.
- Querying ArangoDB and PostGIS through adapter abstractions.
- Excel-first output flow (local `.xlsx` generation + OneDrive/SharePoint delivery).
- Scheduled and ad-hoc report execution entry points.

### Out of Scope
- Interactive BI dashboards or custom report UI tooling.
- General-purpose data transformation platform.
- New Neo4j feature development (legacy only).
- Google Sheets as active output backend.

---

## Domain Context

### ArangoDB
- Primary graph-oriented datasource for assets and relations.
- Used for relationship-heavy validations and hierarchy traversals.

### PostGIS
- Relational/spatial datasource for geographically-oriented and SQL-based checks.

### Legacy Neo4j
- Historical footprint remains in old reports and references.
- Not part of the target runtime path.

---

## System At a Glance

- **Report definitions:** `Reports/`
- **Datasource adapters:** `datasources/`
- **Output adapters:** `outputs/`
- **Runtime orchestration:** `lib/reports/`

The service supports both sequential and parallel execution modes, selected by configuration and operational needs.

---

## Guiding Principles

- **Reliability first:** one failing report should not invalidate a full batch.
- **Clear separation of concerns:** report logic, datasource access, and output logic remain decoupled.
- **Operational transparency:** logs and run metadata must support troubleshooting and auditability.
- **Extensibility:** adapters and report modules should remain replaceable with minimal core changes.

---

## Audience

- **AI assistants:** quick repository orientation before code-level tasks.
- **New developers:** project framing before reading implementation docs.
- **Stakeholders:** concise understanding of scope and intent.

---

## Repository Map (High Level)

```text
RSA/
├── spec.md
├── analysis.md
├── implementation_details.md
├── architecture.md
├── Reports/
├── datasources/
├── outputs/
├── lib/
└── docs/
```

---

## Where to Continue Reading

1. `analysis.md` for functional/non-functional requirements and acceptance criteria.
2. `implementation_details.md` for report contracts, adapter behavior, and developer workflows.
3. `architecture.md` for entry points, execution modes, and runtime decisions.



