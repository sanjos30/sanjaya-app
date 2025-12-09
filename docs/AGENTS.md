# Sanjaya Agents — Role Summary

This document summarizes the roles and responsibilities of each agent in the Sanjaya Autopilot platform.

## 1. product-agent

**Purpose**: Works with the human to define features, clarify requirements, and create design contracts.

**Responsibilities**:
- Collaborates with humans to understand feature ideas and requirements
- Clarifies ambiguous requirements through dialogue
- Creates design contracts that guide code generation
- Ensures design contracts follow the feature design template

## 2. orchestrator

**Purpose**: Reads design contracts, delegates tasks to agents, coordinates workflows, and manages PR flow.

**Responsibilities**:
- Reads and parses design contracts
- Delegates tasks to appropriate agents (codegen, bugfix, etc.)
- Coordinates multi-step workflows
- Manages pull request creation and flow
- Ensures proper sequencing of agent actions

## 3. codegen-agent

**Purpose**: Writes initial code + tests from design contracts and project stack definitions.

**Responsibilities**:
- Reads design contracts created by product-agent
- Generates code according to project stack definitions
- Creates corresponding test files
- Ensures code follows project conventions
- Produces PR-ready code changes

## 4. bugfix-agent

**Purpose**: Creates scoped bugfix patches + regression tests based on errors/logs.

**Responsibilities**:
- Analyzes error logs and stack traces
- Identifies root causes of bugs
- Generates minimal, scoped bugfix patches
- Creates regression tests to prevent recurrence
- Produces PR-ready bugfix changes

## 5. monitor-agent

**Purpose**: Observes logs/metrics, identifies recurring issues, and triggers bugfix workflows.

**Responsibilities**:
- Monitors application logs and metrics
- Detects patterns indicating issues
- Identifies recurring problems
- Triggers bugfix workflows when issues are detected
- Tracks issue frequency and severity

## 6. governance-agent

**Purpose**: Enforces safety rules, validates risk, and ensures compliance with `autopilot.yaml`.

**Responsibilities**:
- Validates all proposed changes against safety rules
- Ensures compliance with project `autopilot.yaml` configuration
- Assesses risk levels of proposed changes
- Blocks or flags unsafe operations
- Enforces guardrails and boundaries

## 7. marketing-agent

**Purpose**: Generates marketing drafts only (no auto-posting).

**Responsibilities**:
- Generates marketing content drafts based on project updates
- Creates blog posts, release notes, and promotional content
- Does NOT auto-post or publish content
- Produces drafts for human review and approval

