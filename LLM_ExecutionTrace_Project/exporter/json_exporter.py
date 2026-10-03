"""
Exports execution results to a JSON file.
"""
import json
import logging
from pathlib import Path

from models import ExecutionResult

logger = logging.getLogger(__name__)

class JsonExporter:
    """Exports execution results to JSON format."""
    
    def __init__(self, output_path: Path):
        self.output_path = output_path
        
    def export(self, results: list[ExecutionResult]) -> Path:
        """Write all results as a JSON array."""
        logger.info(f"Exporting results to JSON at {self.output_path}")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = [r.to_dict() for r in results]
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        logger.info("JSON export complete")
        return self.output_path
