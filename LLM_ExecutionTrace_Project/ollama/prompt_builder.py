"""
PromptBuilder class for constructing prompts for code generation.
"""
import logging
from pathlib import Path
from models import Task

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Builds and saves prompts for the LLM.
    """
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def build_humaneval_prompt(self, task: Task) -> str:
        """
        Build a prompt for a HumanEval task.
        """
        return f"[INST] Complete the following Python function. Return ONLY the function implementation, no explanations.\n\n{task.prompt}\n[/INST]"

    def build_mbpp_prompt(self, task: Task) -> str:
        """
        Build a prompt for an MBPP task.
        """
        first_test = ""
        if task.test_code:
            lines = task.test_code.splitlines()
            for line in lines:
                if line.strip():
                    first_test = line
                    break

        return f"[INST] Write a Python function for the following task. Return ONLY the function implementation, no explanations.\n\nTask: {task.prompt}\n\nExample test: {first_test}\n[/INST]"

    def build_prompt(self, task: Task) -> str:
        """
        Build a prompt based on the task dataset.
        """
        if task.dataset.lower() == "humaneval":
            return self.build_humaneval_prompt(task)
        elif task.dataset.lower() == "mbpp":
            return self.build_mbpp_prompt(task)
        else:
            logger.warning(f"Unknown dataset '{task.dataset}', defaulting to HumanEval format.")
            return self.build_humaneval_prompt(task)

    def save_prompt(self, task: Task, prompt: str) -> Path:
        """
        Save the generated prompt to a text file.
        """
        prompt_path = self.prompts_dir / f"{task.trace_id}.txt"
        try:
            prompt_path.write_text(prompt, encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save prompt for task {task.task_id}: {e}")
        return prompt_path
