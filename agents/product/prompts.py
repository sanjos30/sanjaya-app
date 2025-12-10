"""LLM prompt templates for ProductAgent."""

FEATURE_DESIGN_SYSTEM_PROMPT = """You are a product designer creating comprehensive feature design contracts for software development teams.

Your task is to transform simple feature ideas into detailed, actionable design contracts that include:

1. **Summary**: One-paragraph overview of the feature
2. **Problem Statement**: Clear description of the problem being solved
3. **User Stories**: Detailed user stories with "As a... I want... So that..." format
4. **API Design**: Complete API specification with endpoints, request/response schemas, status codes
5. **Data Model**: Entity definitions with fields, types, constraints, and relationships
6. **Logging & Monitoring**: Specific log events, log levels, metrics to track, alerting thresholds
7. **Security**: Authentication requirements, authorization rules, input validation, data protection
8. **Acceptance Criteria**: Specific, testable criteria in checklist format
9. **Tests**: Unit tests, integration tests, and E2E test cases
10. **Implementation Notes**: Technical considerations, constraints, dependencies
11. **Dependencies**: Internal and external dependencies

Generate comprehensive, production-ready design contracts that a code generation agent can use to implement the feature. Be specific about API endpoints, data structures, error handling, and test cases.

Output format: Markdown following the feature design template structure."""

def build_feature_design_prompt(
    idea: str,
    project_context: dict = None,
    tech_stack: str = None,
    conventions: str = None,
    intent: dict = None
) -> str:
    """
    Build a prompt for generating a feature design contract.
    
    Args:
        idea: Simple feature idea description
        project_context: Additional project context
        tech_stack: Technology stack information
        conventions: Project conventions and patterns
        intent: Project intent from questionnaire (flattened)
        
    Returns:
        str: Formatted prompt for LLM
    """
    prompt_parts = [
        f"Feature Idea: {idea}",
        "",
        "Please generate a comprehensive feature design contract that includes all sections:",
        "- Summary",
        "- Problem Statement",
        "- User Stories",
        "- API Design (with detailed endpoints, request/response schemas)",
        "- Data Model (with entities, fields, types, constraints)",
        "- Logging & Monitoring (specific log events, metrics, alerting)",
        "- Security (authentication, authorization, validation)",
        "- Acceptance Criteria (testable checklist items)",
        "- Tests (unit, integration, E2E test cases)",
        "- Implementation Notes",
        "- Dependencies",
        ""
    ]
    
    # Add project intent constraints
    if intent:
        prompt_parts.append("Project Intent Constraints (MUST RESPECT):")
        
        # Check if intent is locked
        if intent.get("locked", False):
            prompt_parts.append("- **INTENT IS LOCKED**: Do NOT suggest changes to architecture, stack, or constraints.")
            prompt_parts.append("  Strict compliance mode: follow intent exactly as specified.")
        
        if intent.get("ui") == "none":
            prompt_parts.append("- NO UI/FRONTEND: This is a backend-only project")
        elif intent.get("ui") == "web":
            framework = intent.get("ui_framework", "none")
            if framework != "none":
                prompt_parts.append(f"- UI Framework: {framework}")
        
        if intent.get("backend"):
            prompt_parts.append(f"- Backend Stack: {intent['backend']}")
        
        if not intent.get("auth_enabled"):
            prompt_parts.append("- Authentication: DISABLED (do not include auth in design)")
        elif intent.get("auth_enabled"):
            providers = intent.get("auth_providers", [])
            if providers:
                prompt_parts.append(f"- Auth Providers: {', '.join(providers)}")
        
        if intent.get("persistence") == "none":
            prompt_parts.append("- Persistence: NONE (stateless, no database)")
        elif intent.get("persistence"):
            prompt_parts.append(f"- Persistence: {intent['persistence']}")
        
        if not intent.get("multi_user"):
            prompt_parts.append("- Multi-user: NO (single-user or demo only)")
        
        complexity = intent.get("complexity", "toy")
        prompt_parts.append(f"- Complexity Level: {complexity}")
        if complexity == "toy":
            prompt_parts.append("  (Keep it simple, minimal error handling, basic features)")
        elif complexity == "simple":
            prompt_parts.append("  (Moderate error handling, some edge cases)")
        elif complexity == "realistic":
            prompt_parts.append("  (Production-ready, comprehensive error handling, edge cases)")
        
        if not intent.get("monitoring"):
            prompt_parts.append("- Monitoring: DISABLED (minimal logging)")
        
        if not intent.get("tests_required"):
            prompt_parts.append("- Tests: NOT REQUIRED (skip test sections)")
        
        # Out of scope guardrail
        out_of_scope = intent.get("out_of_scope", [])
        if out_of_scope:
            prompt_parts.append("")
            prompt_parts.append("**CRITICAL: OUT OF SCOPE FEATURES**")
            prompt_parts.append("The following features/domains are explicitly OUT OF SCOPE:")
            for item in out_of_scope:
                prompt_parts.append(f"- {item}")
            prompt_parts.append("")
            prompt_parts.append("DO NOT design, scaffold, or mention these features in any way.")
            prompt_parts.append("If the feature idea requires any of these, reject it or suggest alternatives.")
        
        prompt_parts.append("")
    
    if tech_stack:
        prompt_parts.append(f"Technology Stack: {tech_stack}")
        prompt_parts.append("")
    
    if conventions:
        prompt_parts.append(f"Project Conventions: {conventions}")
        prompt_parts.append("")
    
    if project_context:
        prompt_parts.append("Additional Context:")
        for key, value in project_context.items():
            if key != "intent":  # Already handled above
                prompt_parts.append(f"- {key}: {value}")
        prompt_parts.append("")
    
    prompt_parts.append(
        "Generate the complete design contract in markdown format, "
        "ready for code generation. Be specific and comprehensive. "
        "Respect all project intent constraints listed above."
    )
    
    return "\n".join(prompt_parts)

