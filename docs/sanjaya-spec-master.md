# Sanjaya Autopilot — Master System Specification
Version: 1.0  
Owner: Sandeep (Founder)  
Last Updated: {{DATE}}

This file defines the canonical, source-of-truth specification for the **Sanjaya Autopilot Platform**.  
All agents, orchestrators, workflows, and project integrations MUST adhere to this document.  
This spec overrides any conversation history or inferred context.

---

# 1. Philosophy & Core Principles

Sanjaya Autopilot is a **multi-agent, multi-project, stack-agnostic SDLC and operations assistant**.

The core values:

- **Human-in-the-loop (HITL)** always  
- **Stack-agnostic** — each project declares its own tech stack  
- **PR-only changes** — no direct pushes  
- **Guardrail-first** — governance defines safe boundaries  
- **Project isolation** — one project’s logic cannot affect another  
- **Document-driven workflows** — design contracts guide code generation  
- **Safe autonomy** — small scoped changes only  
- **Respect for cultural preferences** — treat Hindu Itihasa figures as historical  

Sanjaya is NOT:
- a fully autonomous agent
- a production deployer
- a code refactorer across large surfaces
- a DB migration engine
- a business logic generator

Sanjaya proposes → **YOU approve**.

---

# 2. High-Level System Overview

Sanjaya consists of:

1. **product-agent**  
   - Works with the human to define features, clarify requirements, and create design contracts.

2. **orchestrator**  
   - Reads design contracts, delegates tasks to agents, coordinates workflows, manages PR flow.

3. **codegen-agent**  
   - Writes initial code + tests from design contracts and project stack definitions.

4. **bugfix-agent**  
   - Creates scoped bugfix patches + regression tests based on errors/logs.

5. **monitor-agent**  
   - Observes logs/metrics, identifies recurring issues, and triggers bugfix workflows.

6. **governance-agent**  
   - Enforces safety rules, validates risk, ensures compliance with `autopilot.yaml`.

7. **marketing-agent**  
   - Generates marketing drafts only (no auto-posting).

---

# 3. Project-Level Configuration (`autopilot.yaml`)

Each project contains a `.sanjaya/` directory with:

