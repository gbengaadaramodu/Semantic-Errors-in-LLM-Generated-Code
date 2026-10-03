"""
Ollama module for interacting with the Ollama API, building prompts, and generating code.
"""

from .client import OllamaClient
from .prompt_builder import PromptBuilder
from .generator import CodeGenerator

__all__ = ["OllamaClient", "PromptBuilder", "CodeGenerator"]
