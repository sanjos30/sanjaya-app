"""Prompt templates for CodegenAgent."""

CODEGEN_SYSTEM_PROMPT = """You are a senior software engineer generating production-quality code and tests.
Follow the project's stack and conventions. Return minimal, clean code that compiles."""


def build_codegen_prompt(design_contract: str, project_config: dict) -> str:
    """
    Build a prompt for code generation based on design contract markdown and project config.
    """
    stack = project_config.get("stack", {})
    backend = stack.get("backend", stack if isinstance(stack, str) else "unspecified")
    frontend = stack.get("frontend", "none") if isinstance(stack, dict) else "none"
    database = stack.get("database", "none") if isinstance(stack, dict) else "none"
    codebase = project_config.get("codebase", {})
    runtime = project_config.get("runtime", {})
    backend_runtime = runtime.get("backend", {}) if isinstance(runtime, dict) else {}
    conventions = project_config.get("conventions", "standard conventions")

    lines = [
        f"Backend stack: {backend}",
        f"Frontend stack: {frontend}",
        f"Database: {database}",
        f"Codebase dirs: root={codebase.get('root','')}, backend_dir={codebase.get('backend_dir','')}, frontend_dir={codebase.get('frontend_dir','')}, tests_dir={codebase.get('tests_dir','')}",
        f"Backend dev_command: {backend_runtime.get('dev_command','')}",
        f"Backend test_command: {backend_runtime.get('test_command','')}",
        f"Conventions: {conventions}",
        "",
        "Design contract:",
        design_contract,
        "",
        "Generate concise, production-ready code and tests aligned to the stack and directories.",
    ]
    return "\n".join(lines)

