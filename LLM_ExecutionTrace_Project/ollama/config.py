"""
Configuration settings for the Ollama module.
"""

from config import OllamaConfig, ProjectConfig

def get_ollama_config() -> OllamaConfig:
    """
    Returns an instance of OllamaConfig from the global configuration.
    """
    return ProjectConfig().ollama
