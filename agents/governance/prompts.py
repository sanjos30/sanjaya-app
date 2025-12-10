"""Governance rules and policy checking."""

# Governance rules are primarily rule-based, not LLM-driven
# This file contains rule definitions and helper functions

FORBIDDEN_PATHS_DEFAULT = [
    "**/.env",
    "**/.env.*",
    "**/secrets/**",
    "**/credentials/**",
    "**/*.key",
    "**/*.pem",
    "**/*.p12",
]

REQUIRE_TESTS_FOR_CODE_PATTERNS = {
    "python": ["**/*.py"],
    "javascript": ["**/*.js", "**/*.ts", "**/*.jsx", "**/*.tsx"],
    "php": ["**/*.php"],
}

ALLOWED_DEPENDENCIES_DEFAULT = {
    "python": [],  # Empty means no restrictions
    "javascript": [],  # Empty means no restrictions
    "php": [],
}

