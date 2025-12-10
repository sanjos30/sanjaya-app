"""LLM prompt templates for BugfixAgent."""

BUGFIX_SYSTEM_PROMPT = """You are a senior software engineer specializing in debugging and fixing test failures.

Your task is to analyze test failures and generate precise, minimal patches that fix the root cause.

When analyzing a test failure:
1. Read the error message, stack trace, and test output carefully
2. Identify the root cause (not just symptoms)
3. Generate a unified diff patch that fixes the issue
4. Provide a retry command to verify the fix
5. Include brief notes explaining the fix

Output format:
- Patch: Unified diff format (starting with @@)
- Retry command: Command to rerun the test
- Notes: Brief explanation of the fix

Be precise and minimal - only change what's necessary to fix the issue."""


def build_bugfix_prompt(
    command: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    changed_files: list = None,
    project_config: dict = None
) -> str:
    """
    Build a prompt for generating bugfix patches.
    
    Args:
        command: Command that failed
        exit_code: Exit code from the command
        stdout: Standard output
        stderr: Standard error output
        changed_files: List of files that were changed (optional)
        project_config: Project configuration (optional)
        
    Returns:
        str: Formatted prompt for LLM
    """
    prompt_parts = [
        "Test failure analysis:",
        "",
        f"Command: {command}",
        f"Exit code: {exit_code}",
        "",
        "Standard output:",
        "---",
        stdout or "(empty)",
        "---",
        "",
        "Standard error:",
        "---",
        stderr or "(empty)",
        "---",
        ""
    ]
    
    if changed_files:
        prompt_parts.append("Recently changed files:")
        for f in changed_files:
            prompt_parts.append(f"- {f}")
        prompt_parts.append("")
    
    if project_config:
        stack = project_config.get("stack", {})
        language = project_config.get("language", "python")
        prompt_parts.append(f"Project stack: {stack}")
        prompt_parts.append(f"Language: {language}")
        prompt_parts.append("")
    
    prompt_parts.extend([
        "Please analyze this test failure and provide:",
        "1. A unified diff patch that fixes the root cause",
        "2. A retry command to verify the fix",
        "3. Brief notes explaining what was wrong and how the fix addresses it",
        "",
        "Format your response as:",
        "PATCH:",
        "<unified diff here>",
        "",
        "RETRY_COMMAND:",
        "<command to rerun test>",
        "",
        "NOTES:",
        "<explanation>"
    ])
    
    return "\n".join(prompt_parts)

