"""
Structured logging setup.
"""
import logging
from pathlib import Path

def setup_logging(log_dir: Path, level: int = logging.INFO) -> logging.Logger:
    """Configure root logger with console and file handlers."""
    log_dir.mkdir(parents=True, exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')
    console_handler.setFormatter(console_format)
    
    file_handler = logging.FileHandler(log_dir / 'experiment.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s | %(name)s | %(levelname)-8s | %(message)s')
    file_handler.setFormatter(file_format)
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger
