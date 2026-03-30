# Documentation Structure

This project uses a **four-document documentation strategy** designed for different audiences and purposes:

---

## 📄 spec.md (Project Summary)
**Audience:** AI, new developers, project managers  
**Purpose:** High-level overview  
**Scope:** What is this project? Why? Scope and boundaries.  
**Length:** ~113 lines  

**Read this first to:**
- Understand project goals and scope
- Understand domain context (ArangoDB, PostGIS, legacy Neo4j)
- See high-level repository map
- Know where to continue reading for details

**Topics:**
- Purpose and intended audience
- Project in one paragraph
- Business goals
- In-scope / out-of-scope boundaries
- Domain context
- High-level repository map

**Audience Example:** "I'm new to the project; give me the 10,000-foot view"

---

## 📋 analysis.md (Requirements & Criteria)
**Audience:** Architects, QA, project stakeholders  
**Purpose:** Functional requirements, data contracts, acceptance criteria  
**Scope:** What needs to be built? How do we verify it?  
**Length:** ~420 lines

**Read this next to:**
- Understand functional requirements (FR1-FR6)
- See non-functional requirements (NFR1-NFR5)
- Review data contracts (QueryResult, adapters)
- Understand rollout phases (Phase 0-3)
- See acceptance criteria and traceability matrix

**Topics:**
- Problem Statement
- Functional Requirements (FR1-FR6)
  - Excel Output Backend
  - Datasource Abstraction
  - QueryResult Data Contract
  - Retry Logic & Fault Handling
  - Mail Notifications
  - History & Summary Sheets
- Non-Functional Requirements (NFR1-NFR5)
  - Reliability, Observability, Testability, Extensibility, Performance
- Acceptance Criteria (testable statements)
- Rollout Plan (Phase 0-3 with timelines)
- Configuration Schema
- Traceability Matrix

**Audience Example:** "What are we building? How do we know it works?"

---

## 💻 implementation_details.md (Developer How-To)
**Audience:** Developers, QA engineers  
**Purpose:** Report types, API contracts, adapters, configuration, code examples  
**Scope:** How do I build and test reports? How do datasources work? How do I configure the system?  
**Length:** ~835 lines

**Read this before coding to:**
- Understand report types (DQReport, LegacyReport, KladRapport)
- Learn the Report API contract (init_report, run_report)
- See datasource adapter implementation (ArangoDB, PostGIS)
- Learn output adapter patterns (Excel)
- Understand QueryResult conversion and helpers
- See configuration schema with examples
- Understand where operational, export, utility, and legacy scripts live
- Learn logging strategy and context injection
- Get testing patterns and mocking examples
- Create a new report from template

**Topics:**
- Report Architecture Overview
- Report Types (5 types explained)
- Report API Contract
  - init_report()
  - run_report(sender)
  - DQReport walkthrough
- Datasource Adapters
  - Contract and Protocol
  - ArangoDB implementation checklist
  - PostGIS implementation checklist
  - Responsibility matrix
- Output Adapters
  - Excel adapter design
  - Memory strategy (iter_rows vs to_rows_list)
- QueryResult & Conversion
  - Dataclass definition
  - Conversion responsibility
- Configuration & Settings
  - settings.json schema with examples
  - Environment variables
  - Loading configuration
- Scripts Layout
- Logging Strategy
  - Context injection (ContextVar)
  - Custom filter setup
  - Example output
- Testing & Mocking
  - Unit test pattern (datasources)
  - Integration test pattern (outputs)
- Creating a New Report (checklist + template)
- Backwards Compatibility

**Audience Example:** "How do I create a new report? How does the PostGIS adapter work?"

---

## 🏗️ architecture.md (System Design & Execution)
**Audience:** Architects, DevOps, senior developers  
**Purpose:** Execution modes, entry points, connection strategies, performance, debugging  
**Scope:** How does the system execute? How are reports run in parallel? How do we debug?  
**Length:** ~917 lines

**Read this to understand:**
- System overview and three entry points
- Sequential vs. Parallel execution modes
- Entry point behaviors (main.py, run_single_report.py, main_selection_list.py)
- Shared code structure and reuse metrics
- Database connection strategies
- Logging and observability setup
- Performance characteristics and tuning
- Testing checklist
- Debugging guide with common issues
- Future enhancements

**Topics:**
- System Overview
  - Three entry points, shared engine diagram
- Execution Modes
  - Sequential (in-process, ~6-8 hours)
  - Parallel-by-Datasource (subprocess, ~3-4 hours)
  - Decision matrix (when to use which?)
- Entry Points & Behaviors
  - main.py (all reports, scheduled daily)
  - run_single_report.py (1 report, flexible)
  - main_selection_list.py (4 test reports)
  - Code examples for each
- Shared Code Structure
  - selection_runner.py (35 lines)
  - pipeline_runner.py (80 lines)
  - ReportLoopRunner.py (150 lines)
  - worker.py (188 lines)
  - Duplication reduction metrics (92% → 5%)
- Database Connection Strategy
  - Sequential mode (singletons shared)
  - Parallel mode (subprocess isolation)
  - Connection lifecycle diagrams
- Logging & Observability
  - Log format with report context
  - ContextVar + custom filter pattern
  - Grep examples
- Performance Characteristics
  - Memory usage per mode
  - Execution time per mode
  - Performance tuning tips
  - Formulas for capacity planning
- Testing Checklist
  - Test matrix (3 entry points × 2 modes)
  - Smoke test commands
  - Verification steps
- Debugging Guide
  - Enable verbose logging
  - Stream output in real-time
  - Monitor resource usage
  - Common issues & solutions
- Future Enhancements

**Audience Example:** "How do we scale to 1000 reports? How do we debug parallel execution?"

---

## 📚 Quick Navigation by Role

### New Developer (First Week)
1. Read **spec.md** (15 min)
2. Read **implementation_details.md** § Report API Contract (20 min)
3. Read **implementation_details.md** § Creating a New Report (30 min)
4. Run: `python run_single_report.py --once --report Report0002` (10 min)
5. Read **architecture.md** § Debugging Guide (15 min)

**Total:** ~2 hours to productive

### QA / Tester
1. Read **analysis.md** (30 min)
2. Read **architecture.md** § Testing Checklist (20 min)
3. Run: `python main_selection_list.py --parallel` (varies)
4. Reference **architecture.md** § Debugging Guide for troubleshooting

**Total:** ~1 hour to start testing

### DevOps / Architect
1. Read **architecture.md** (45 min)
2. Read **analysis.md** § Rollout Plan (15 min)
3. Read **spec.md** (15 min)
4. Configure settings.json based on **implementation_details.md** § Configuration (20 min)

**Total:** ~1.5 hours for deployment planning

### Data Team / Report Author
1. Read **spec.md** § Scope + Domain Context (10 min)
2. Read **implementation_details.md** § Report Types & API Contract (30 min)
3. Read **implementation_details.md** § Creating a New Report (20 min)
4. Use template from **implementation_details.md** to create report

**Total:** ~1 hour to write first report

---

## 📖 Search & Cross-Reference

**Looking for... Read this section:**

| Topic | Document |
|-------|----------|
| How to create a report? | implementation_details.md → Creating a New Report |
| What are the requirements? | analysis.md → Functional Requirements |
| How does parallel execution work? | architecture.md → Execution Modes |
| How do I debug a failing report? | architecture.md → Debugging Guide |
| What is QueryResult? | analysis.md → FR3 (Data Contract) |
| How do I configure the system? | implementation_details.md → Configuration & Settings |
| Where do scripts live now? | implementation_details.md → Scripts Layout |
| What are the entry points? | architecture.md → Entry Points & Behaviors |
| What datasources are supported? | spec.md → Domain Context |
| How do I run tests? | architecture.md → Testing Checklist |
| What's the project scope and boundary? | spec.md → Scope |

---

## 🗂️ Old Documentation Status

| Old File | Status | Reason |
|----------|--------|--------|
| `spec.md.backup` | Archived | Replaced by new spec.md |
| `QUICK_REFERENCE.md` | Merged | Content in architecture.md + implementation_details.md |
| `context.md` | Merged | Content in spec.md |
| `context_reports.md` | Merged | Content in implementation_details.md |
| `ARCHITECTURE.md` | Replaced | New architecture.md is comprehensive revision |
| `README_main_selection_list.md` | Merged | Content in architecture.md § Entry Points |
| `docs/excel_output_spec.md` | Referenced | Content in implementation_details.md |
| `steps.md` | Partial merge | Dev workflow → implementation_details.md |

---

## 📝 Maintenance Notes

### When to Update Each Document

**spec.md:** When project goals, scope, boundaries, or audience changes  
**analysis.md:** When requirements change; add phase to rollout plan  
**implementation_details.md:** When report patterns change; add new adapter docs  
**architecture.md:** When execution modes change; update performance metrics  

---

## 💡 Tips for Reading

- **Skim first:** Read section headers to understand structure
- **Use Table of Contents:** Jump to sections you need
- **Cross-reference:** Links between docs show related info
- **Code examples:** Each doc includes Python code snippets; reference them
- **Diagrams:** architecture.md has ASCII flow diagrams; follow them
- **Checklists:** implementation_details.md has step-by-step checklists for new reports


