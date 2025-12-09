# Sanjaya Autopilot — High-Level Approach

## Overview

Sanjaya Autopilot is a **multi-agent, multi-project, stack-agnostic SDLC and operations assistant** that operates under strict human-in-the-loop (HITL) principles.

## Core Architectural Principles

### Multi-Agent System

Sanjaya employs a specialized agent architecture where each agent has a focused responsibility:

- **product-agent**: Feature design and requirements clarification
- **orchestrator**: Workflow coordination and task delegation
- **codegen-agent**: Code generation from design contracts
- **bugfix-agent**: Bug identification and patch generation
- **monitor-agent**: Log/metric observation and issue detection
- **governance-agent**: Safety rule enforcement and compliance
- **marketing-agent**: Marketing content generation

Agents work together through the orchestrator, which coordinates workflows and ensures proper sequencing of operations.

### Multi-Project Support

Sanjaya is designed to manage multiple projects simultaneously. Each project is:

- **Isolated**: One project's logic cannot affect another
- **Independently configured**: Each project has its own `.sanjaya/autopilot.yaml` configuration
- **Stack-agnostic**: Projects can use different technology stacks

The platform maintains project isolation at all levels, ensuring that operations, configurations, and workflows are scoped to individual projects.

### Stack-Agnostic Design

Sanjaya does not assume a specific technology stack. Instead:

- Each project declares its own tech stack in `autopilot.yaml`
- Code generation adapts to the declared stack
- Workflows respect stack-specific conventions and patterns
- No hardcoded assumptions about frameworks or languages

This allows Sanjaya to work with diverse projects—from Python FastAPI services to Node.js applications, Go microservices, or any other stack.

### PR-Only, Human-in-the-Loop (HITL)

All changes proposed by Sanjaya follow a strict workflow:

1. **Propose**: Sanjaya generates code, bugfixes, or other changes
2. **Review**: Changes are presented as pull requests
3. **Approve**: Human reviews and approves before merging
4. **Deploy**: Only after human approval are changes merged

**Sanjaya never**:
- Directly pushes to main/master branches
- Deploys to production
- Makes changes without human review
- Bypasses the PR workflow

The platform operates on the principle: **Sanjaya proposes → YOU approve**.

### Per-Project Configuration

Each project that uses Sanjaya contains a `.sanjaya/autopilot.yaml` file that defines:

- Technology stack and conventions
- Safety rules and guardrails
- Allowed operations and boundaries
- Project-specific workflows
- Integration settings

This configuration ensures that Sanjaya respects each project's unique requirements and constraints.

### Document-Driven Workflows

Sanjaya uses design contracts as the primary mechanism for feature development:

1. **Design Contract**: Product-agent creates a detailed design document
2. **Code Generation**: Codegen-agent reads the contract and generates code
3. **Validation**: Governance-agent ensures compliance
4. **PR Creation**: Orchestrator creates a pull request

This document-driven approach ensures clarity, traceability, and consistency.

### Safe Autonomy

Sanjaya operates with "safe autonomy" principles:

- **Small scoped changes**: Only focused, limited-scope modifications
- **Guardrail-first**: Governance rules define safe boundaries
- **Risk assessment**: All changes are evaluated for risk
- **No large refactors**: Avoids sweeping changes across large codebases

## What Sanjaya Is NOT

To maintain clarity and set proper expectations:

- **NOT** a fully autonomous agent (requires human approval)
- **NOT** a production deployer (only generates PRs)
- **NOT** a code refactorer across large surfaces (small scoped changes only)
- **NOT** a DB migration engine (out of scope)
- **NOT** a business logic generator (works from design contracts)

## Workflow Patterns

### Feature Development Workflow

1. Human provides feature idea
2. Product-agent creates design contract
3. Orchestrator delegates to codegen-agent
4. Codegen-agent generates code + tests
5. Governance-agent validates safety
6. Orchestrator creates PR
7. Human reviews and approves

### Bugfix Workflow

1. Monitor-agent detects issue from logs/metrics
2. Orchestrator triggers bugfix workflow
3. Bugfix-agent analyzes and creates patch
4. Governance-agent validates safety
5. Orchestrator creates PR
6. Human reviews and approves

## Constraints and Boundaries

- **Human approval required**: All changes go through PR review
- **Project isolation**: No cross-project operations
- **Stack respect**: Follows each project's declared stack
- **Small scope**: Only focused, limited changes
- **Document-driven**: Features require design contracts
- **Safety first**: Governance rules are non-negotiable

