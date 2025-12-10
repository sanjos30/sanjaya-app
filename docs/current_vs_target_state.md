# Current vs Target State Analysis

**Date**: December 2024  
**Version**: v0.5 (Workflow Status & Monitor MVP)

## Full Cycle Vision

```
Rough Idea → Specs → Code/Test → Monitor/Fix → Repeat → Market
```

## Current State Assessment

### ✅ **Rough Idea → Specs** (MOSTLY COMPLETE)

**Current Capabilities**:
- ✅ `POST /ideas/feature-from-idea` - LLM converts simple idea → full design contract
- ✅ `POST /ideas/feature` - Structured input → design contract
- ✅ ProductAgent generates comprehensive specs with:
  - API design
  - Data models
  - Test requirements
  - Logging/monitoring sections
  - All template sections

**Gaps**:
- ⚠️ No iterative refinement (human can't ask follow-up questions via API)
- ⚠️ No validation that specs are complete/feasible before codegen
- ⚠️ No cost/effort estimation

**Status**: **~85% Complete** - Core functionality works, needs refinement UX

---

### ✅ **Specs → Code/Test** (COMPLETE)

**Current Capabilities**:
- ✅ `POST /workflows/run` with `workflow_type="feature"`
- ✅ CodegenAgent reads design contracts
- ✅ Stack-aware code generation (FastAPI, Next.js, PHP)
- ✅ Deterministic scaffolds for missing files
- ✅ Test file generation
- ✅ Stack-specific test commands (`runtime.*.test_command`)
- ✅ Smoke tests (`runtime.*.smoke_command`)
- ✅ Workflow status gating (tests_passed, smoke_passed, governance_ok)
- ✅ PR creation (real GitHub PRs when token/repo provided)

**Gaps**:
- ⚠️ No automatic test generation from specs (tests are scaffolded, not spec-driven)
- ⚠️ No code review suggestions before PR
- ⚠️ No integration test generation

**Status**: **~90% Complete** - Full workflow works end-to-end

---

### ⚠️ **Monitor/Fix** (PARTIAL)

**Current Capabilities**:
- ✅ `POST /monitor/check` - On-demand log analysis
- ✅ MonitorAgent MVP - Rule-based error detection
- ✅ `POST /workflows/run` with `workflow_type="bugfix"`
- ✅ BugfixAgent suggests patches on test failures
- ✅ Patches returned in response (HITL - no auto-apply)

**Gaps**:
- ❌ **No automatic monitoring** - Must manually call `/monitor/check`
- ❌ **No auto-trigger from Monitor → Bugfix workflow** - Must manually trigger
- ❌ **No continuous background monitoring** - No scheduled checks
- ❌ **No metrics collection** - Only log file analysis
- ❌ **No alerting** - No notifications when issues detected
- ❌ **No issue tracking** - No persistence of detected issues
- ❌ **No regression test generation** - BugfixAgent suggests patches but doesn't generate tests

**Status**: **~40% Complete** - Core pieces exist but not connected/automated

---

### ❌ **Repeat** (NOT IMPLEMENTED)

**Current Capabilities**:
- ✅ Can manually re-run workflows
- ✅ Can manually trigger bugfix workflows

**Gaps**:
- ❌ **No workflow scheduling** - Can't schedule periodic runs
- ❌ **No workflow chaining** - Can't chain: monitor → bugfix → test → deploy
- ❌ **No retry logic** - No automatic retries on failure
- ❌ **No workflow history** - No tracking of past runs
- ❌ **No workflow templates** - Can't save/reuse workflow configs
- ❌ **No CI/CD integration** - No GitHub Actions/CI hooks

**Status**: **~10% Complete** - Manual only, no automation

---

### ❌ **Market** (NOT IMPLEMENTED)

**Current Capabilities**:
- ❌ MarketingAgent is stub only

**Gaps**:
- ❌ **No marketing content generation** - No blog posts, docs, changelogs
- ❌ **No release notes generation** - No automated release notes from PRs
- ❌ **No feature announcement** - No social media/content generation
- ❌ **No user documentation** - No auto-generated user guides
- ❌ **No API documentation** - No OpenAPI/Swagger generation from code

**Status**: **~0% Complete** - Not started

---

## Full Cycle Readiness

### Can we do the full cycle NOW?

**Partially, but with significant manual steps:**

```
✅ Rough Idea → Specs          [85% - Works, needs UX polish]
✅ Specs → Code/Test           [90% - Works end-to-end]
⚠️  Monitor/Fix                [40% - Works but manual]
❌ Repeat                      [10% - Manual only]
❌ Market                      [0% - Not implemented]
```

**Current Workflow (Manual)**:
1. ✅ Human: "I want a feature that does X"
2. ✅ API: `POST /ideas/feature-from-idea` → Design contract created
3. ✅ API: `POST /workflows/run` (feature) → Code + tests generated, PR created
4. ✅ Human: Reviews PR, merges
5. ⚠️  Human: Manually calls `POST /monitor/check` periodically
6. ⚠️  Human: If issues found, manually calls `POST /workflows/run` (bugfix)
7. ❌ Human: Must manually repeat steps 1-6 for next feature
8. ❌ Human: Must manually create marketing content

---

## Target State (Full Automation)

### What's needed for full cycle?

#### 1. **Monitor/Fix Automation** (Priority: HIGH)

**Required**:
- [ ] Background monitoring service (or scheduled jobs)
- [ ] Auto-trigger bugfix workflow when MonitorAgent detects issues
- [ ] Issue persistence/tracking (database or file-based)
- [ ] Alerting (email, Slack, webhook)
- [ ] Metrics collection (beyond logs)
- [ ] Regression test generation in BugfixAgent

**Estimated Effort**: 2-3 weeks

---

#### 2. **Repeat/Automation** (Priority: MEDIUM)

**Required**:
- [ ] Workflow scheduling API (`POST /workflows/schedule`)
- [ ] Workflow chaining (output of one → input of next)
- [ ] Retry logic with exponential backoff
- [ ] Workflow history/tracking
- [ ] Workflow templates
- [ ] CI/CD hooks (GitHub Actions integration)

**Estimated Effort**: 3-4 weeks

---

#### 3. **Market/MarketingAgent** (Priority: LOW)

**Required**:
- [ ] MarketingAgent implementation
- [ ] Blog post generation from feature specs
- [ ] Release notes generation from PRs/changelog
- [ ] Social media content (Twitter, LinkedIn)
- [ ] User documentation generation
- [ ] API documentation generation (OpenAPI from code)

**Estimated Effort**: 2-3 weeks

---

#### 4. **Polish/Refinement** (Priority: MEDIUM)

**Required**:
- [ ] Iterative spec refinement (conversational ProductAgent)
- [ ] Spec validation before codegen
- [ ] Cost/effort estimation
- [ ] Code review suggestions
- [ ] Integration test generation from specs

**Estimated Effort**: 2-3 weeks

---

## Recommended Next Steps

### Phase 1: Complete Monitor/Fix Loop (2-3 weeks)
**Goal**: Make monitoring → bugfix → test → deploy fully automated

1. **Background Monitoring**:
   - Add scheduled job system (APScheduler or similar)
   - Or: Webhook-based monitoring (external service calls Sanjaya)
   - Store monitoring results in simple DB/file

2. **Auto-Trigger Bugfix**:
   - When MonitorAgent detects critical errors → auto-trigger bugfix workflow
   - Configurable thresholds (error count, severity)
   - HITL: Still require human approval for patch application

3. **Issue Tracking**:
   - Simple issue store (SQLite or JSON file)
   - Track: issue ID, first seen, last seen, count, severity, status
   - API: `GET /issues`, `POST /issues/{id}/resolve`

4. **Regression Tests**:
   - Enhance BugfixAgent to generate regression tests
   - Auto-add test file to PR

**Outcome**: Fully automated monitor → detect → fix → test → PR cycle

---

### Phase 2: Workflow Automation (3-4 weeks)
**Goal**: Enable workflow scheduling, chaining, and retries

1. **Workflow Scheduling**:
   - `POST /workflows/schedule` - Schedule periodic runs
   - Store schedules in DB/file
   - Background scheduler executes at intervals

2. **Workflow Chaining**:
   - Define workflow chains in YAML
   - Example: `monitor → if_issues → bugfix → test → if_pass → deploy`
   - Conditional branching based on status

3. **Retry Logic**:
   - Configurable retry attempts
   - Exponential backoff
   - Retry on specific failure types

4. **Workflow History**:
   - Store all workflow runs
   - `GET /workflows/history?project_id=X`
   - Show success/failure rates, trends

**Outcome**: Can schedule and chain workflows automatically

---

### Phase 3: MarketingAgent (2-3 weeks)
**Goal**: Auto-generate marketing content from features

1. **Release Notes**:
   - Parse PR titles/descriptions
   - Generate changelog entries
   - Format for GitHub releases

2. **Blog Posts**:
   - Generate blog post from feature spec
   - Include code examples, use cases
   - Format for markdown/HTML

3. **Social Media**:
   - Generate Twitter/LinkedIn posts
   - Short, engaging summaries
   - Include links to docs/PRs

4. **Documentation**:
   - User guides from feature specs
   - API docs from code (OpenAPI generation)
   - Tutorial generation

**Outcome**: Marketing content auto-generated from features

---

## Summary

### Current State: **~50% of Full Cycle**

- ✅ Idea → Specs: **85%** (works, needs polish)
- ✅ Specs → Code/Test: **90%** (works end-to-end)
- ⚠️  Monitor/Fix: **40%** (core pieces exist, not automated)
- ❌ Repeat: **10%** (manual only)
- ❌ Market: **0%** (not started)

### To Reach Full Cycle: **~10-12 weeks of development**

**Priority Order**:
1. **Monitor/Fix Automation** (2-3 weeks) - Highest impact
2. **Workflow Automation** (3-4 weeks) - Enables "repeat"
3. **MarketingAgent** (2-3 weeks) - Completes cycle
4. **Polish/Refinement** (2-3 weeks) - Improves quality

### Can we do it NOW?

**Yes, but with manual steps:**
- ✅ Idea → Specs → Code/Test → PR: **Fully automated**
- ⚠️  Monitor → Fix: **Manual** (call APIs yourself)
- ❌ Repeat: **Manual** (re-run workflows yourself)
- ❌ Market: **Manual** (write content yourself)

**The foundation is solid. The automation layer is what's missing.**

