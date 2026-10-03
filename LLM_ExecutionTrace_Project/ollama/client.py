"""
Client for interacting with the Ollama API.
"""
import time
import logging
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError
from config import OllamaConfig

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Client for interacting with the Ollama API.
    """
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.session = requests.Session()
        self.base_url = config.base_url
        self.model = config.model_name
        self.temperature = config.temperature

    def health_check(self) -> bool:
        """
        Check if the Ollama service is running.
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return True
        except (ConnectionError, Timeout, HTTPError) as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    def get_version(self) -> str:
        """
        Get the version of the Ollama service.
        """
        try:
            response = self.session.get(f"{self.base_url}/api/version", timeout=5)
            response.raise_for_status()
            return response.json().get("version", "unknown")
        except (ConnectionError, Timeout, HTTPError) as e:
            logger.error(f"Failed to get Ollama version: {e}")
            return "unknown"

    def generate(self, prompt: str) -> dict:
        """
        Generate a response from the Ollama model with retries.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": 2048
            }
        }
        
        retries = 3
        backoff_times = [2, 4, 8]
        
        for attempt, backoff in enumerate(backoff_times + [0]):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=300
                )
                response.raise_for_status()
                return response.json()
            except (ConnectionError, Timeout, HTTPError) as e:
                if attempt < retries:
                    logger.warning(f"Ollama generate request failed: {e}. Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                else:
                    logger.error(f"Ollama generate request failed after {retries} retries: {e}")
                    raise
        
        return {}
