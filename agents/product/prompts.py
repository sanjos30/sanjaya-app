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
    conventions: str = None
) -> str:
    """
    Build a prompt for generating a feature design contract.
    
    Args:
        idea: Simple feature idea description
        project_context: Additional project context
        tech_stack: Technology stack information
        conventions: Project conventions and patterns
        
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
    
    if tech_stack:
        prompt_parts.append(f"Technology Stack: {tech_stack}")
        prompt_parts.append("")
    
    if conventions:
        prompt_parts.append(f"Project Conventions: {conventions}")
        prompt_parts.append("")
    
    if project_context:
        prompt_parts.append("Additional Context:")
        for key, value in project_context.items():
            prompt_parts.append(f"- {key}: {value}")
        prompt_parts.append("")
    
    prompt_parts.append(
        "Generate the complete design contract in markdown format, "
        "ready for code generation. Be specific and comprehensive."
    )
    
    return "\n".join(prompt_parts)

