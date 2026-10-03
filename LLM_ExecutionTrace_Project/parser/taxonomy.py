"""
Taxonomy module for the parser.
"""

from models import ErrorCategory

def get_all_categories() -> list[str]:
    """Returns all category display names."""
    return [category.value for category in ErrorCategory]

def get_error_categories() -> list[str]:
    """Returns only error category names (excluding Correct)."""
    return [category.value for category in ErrorCategory if category != ErrorCategory.CORRECT]

def describe_category(category: ErrorCategory) -> str:
    """Returns a one-line description of each category."""
    descriptions = {
        ErrorCategory.CORRECT: "All tests pass successfully.",
        ErrorCategory.SYNTAX_ERROR: "Code cannot be parsed due to syntax issues.",
        ErrorCategory.RUNTIME_EXCEPTION: "Uncaught exception during execution.",
        ErrorCategory.WRONG_OUTPUT: "Code ran but failed a benchmark test assertion.",
        ErrorCategory.ASSERTION_FAILURE: "Internal assertion within the generated code failed.",
        ErrorCategory.TIMEOUT: "Execution exceeded time limit.",
    }
    return descriptions.get(category, "Unknown category.")