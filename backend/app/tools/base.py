from abc import ABC, abstractmethod
from typing import Any, Optional
import json


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    parameters: dict = {}

    @abstractmethod
    def execute(self, **kwargs) -> str:
        raise NotImplementedError

    def to_prompt(self) -> str:
        params_desc = json.dumps(self.parameters, indent=2, ensure_ascii=False)
        return f"- {self.name}: {self.description}\n  Parameters: {params_desc}"
