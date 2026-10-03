"""
CodeGenerator class for generating code using the OllamaClient and PromptBuilder.
"""
import logging
import re
from pathlib import Path

from models import Task
from .client import OllamaClient
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

class CodeGenerator:
    """
    Coordinates code generation using the Ollama client and Prompt builder.
    """
    def __init__(self, client: OllamaClient, prompt_builder: PromptBuilder, output_dir: Path):
        self.client = client
        self.prompt_builder = prompt_builder
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_code(self, response_text: str) -> str:
        """
        Extract Python code from an LLM response.
        """
        # Look for code between ```python and ```
        python_fence_pattern = re.compile(r"```python\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
        match = python_fence_pattern.search(response_text)
        if match:
            return match.group(1).strip()

        # Look for code between generic ``` and ```
        any_fence_pattern = re.compile(r"```\s*(.*?)\s*```", re.DOTALL)
        match = any_fence_pattern.search(response_text)
        if match:
            return match.group(1).strip()

        # Look for code between [PYTHON] and [/PYTHON]
        python_bracket_pattern = re.compile(r"\[PYTHON\]\s*(.*?)\s*\[/PYTHON\]", re.DOTALL | re.IGNORECASE)
        match = python_bracket_pattern.search(response_text)
        if match:
            return match.group(1).strip()

        # Fallback to returning the stripped text
        return response_text.replace("[PYTHON]", "").replace("[/PYTHON]", "").strip()

    def generate_one(self, task: Task) -> Path:
        """
        Generate code for a single task.
        If the prompt and generated code already exist, skip generation.
        """
        code_path = self.output_dir / f"{task.trace_id}.py"
        prompt_path = self.prompt_builder.prompts_dir / f"{task.trace_id}.txt"

        # Skip if both the code and the prompt are already generated
        if code_path.exists() and prompt_path.exists():
            logger.info(f"Task {task.trace_id} ({task.task_id}) already generated. Skipping.")
            return code_path

        prompt = self.prompt_builder.build_prompt(task)
        self.prompt_builder.save_prompt(task, prompt)
        
        response = self.client.generate(prompt)
        response_text = response.get("response", "")
        
        code = self.extract_code(response_text)
        
        try:
            code_path.write_text(code, encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save generated code for task {task.task_id}: {e}")
            
        return code_path

    def generate_all(self, tasks: list[Task]) -> list[Path]:
        """
        Generate code for a list of tasks.
        """
        saved_paths = []
        total_tasks = len(tasks)
        
        for i, task in enumerate(tasks, 1):
            try:
                code_path = self.generate_one(task)
                saved_paths.append(code_path)
                logger.info(f"Generated {i}/{total_tasks} {task.dataset} tasks")
            except Exception as e:
                logger.error(f"Error generating code for task {task.task_id}: {e}")
                
        return saved_paths
