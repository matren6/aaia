"""
Prompt Manager moved to modules package.

This file contains the PromptManager class originally located in
`packages/prompts/manager.py`. It was moved here to colocate with other
modules. Default prompts directory is set to the sibling `prompts` package.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class PromptManager:
    """Centralized prompt management system"""

    def __init__(self, prompts_dir: str = None):
        """
        Initialize PromptManager.

        Args:
            prompts_dir: Directory containing prompt JSON files.
                        Defaults to the `prompts` directory sibling to this module.
        """
        if prompts_dir is None:
            # Default to the prompts directory which is a sibling of the `modules` package
            base_dir = Path(__file__).resolve().parent.parent
            prompts_dir = base_dir / "prompts"

        self.prompts_dir = Path(prompts_dir)
        self._prompts: Dict[str, Dict] = {}

        # Create directory if it doesn't exist
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

        # Load all prompts
        self._load_all_prompts()

    def _load_all_prompts(self):
        """Load all prompt files from the prompts directory"""
        if not self.prompts_dir.exists():
            return

        for prompt_file in self.prompts_dir.rglob("*.json"):
            try:
                self._load_prompt_file(prompt_file)
            except Exception as e:
                print(f"Warning: Failed to load prompt file {prompt_file}: {e}")

    def _load_prompt_file(self, file_path: Path):
        """Load a single prompt file"""
        try:
            with open(file_path, 'r') as f:
                prompts_data = json.load(f)

            # Handle both single prompt and list of prompts
            if isinstance(prompts_data, list):
                for prompt in prompts_data:
                    self._register_prompt(prompt, file_path)
            else:
                self._register_prompt(prompts_data, file_path)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")

    def _register_prompt(self, prompt_data: Dict, file_path: Path):
        """Register a prompt in the internal dictionary"""
        if "name" not in prompt_data:
            raise ValueError(f"Prompt missing 'name' field in {file_path}")

        name = prompt_data["name"]

        # Add file path and category to prompt data
        prompt_data["file_path"] = str(file_path)
        prompt_data["category"] = file_path.parent.name if file_path.parent != self.prompts_dir else "root"

        # Initialize metadata if not present
        if "metadata" not in prompt_data:
            prompt_data["metadata"] = {
                "created_by": "system",
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "last_updated": datetime.now().isoformat()
            }

        self._prompts[name] = prompt_data

    def get_prompt(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Get a formatted prompt by name.

        Args:
            name: Name of the prompt to retrieve
            **kwargs: Parameters to format the prompt template

        Returns:
            Dict containing:
                - prompt: Formatted prompt text
                - system_prompt: System prompt for the model
                - model_preferences: Model preference settings
                - raw: Raw prompt data

        Raises:
            ValueError: If prompt not found or required parameters missing
        """
        if name not in self._prompts:
            available = ", ".join(self._prompts.keys())
            raise ValueError(f"Prompt not found: {name}. Available prompts: {available}")

        prompt_data = self._prompts[name]
        template = prompt_data.get("template", "")

        # Validate required parameters
        parameters = prompt_data.get("parameters", [])
        for param in parameters:
            if param.get("required", False) and param["name"] not in kwargs:
                raise ValueError(f"Required parameter missing: {param['name']}")

        # Format the prompt with provided parameters
        try:
            formatted_prompt = template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing parameter for prompt formatting: {e}")
        except Exception as e:
            raise ValueError(f"Error formatting prompt: {e}")

        return {
            "prompt": formatted_prompt,
            "system_prompt": prompt_data.get("system_prompt", ""),
            "model_preferences": prompt_data.get("model_preferences", {}),
            "raw": prompt_data
        }

    def get_prompt_raw(self, name: str) -> Dict:
        """
        Get raw prompt data without formatting.

        Args:
            name: Name of the prompt

        Returns:
            Raw prompt data dictionary
        """
        if name not in self._prompts:
            raise ValueError(f"Prompt not found: {name}")
        return self._prompts[name].copy()

    def list_prompts(self, category: Optional[str] = None) -> List[Dict]:
        """
        List all available prompts, optionally filtered by category.

        Args:
            category: Optional category to filter by

        Returns:
            List of prompt info dictionaries
        """
        prompts = []
        for name, data in self._prompts.items():
            prompt_category = data.get("category", "root")
            if category is None or prompt_category == category:
                prompts.append({
                    "name": name,
                    "description": data.get("description", ""),
                    "category": prompt_category,
                    "file_path": data.get("file_path", ""),
                    "version": data.get("metadata", {}).get("version", "1.0")
                })

        # Sort by name
        prompts.sort(key=lambda x: x["name"])
        return prompts

    def list_categories(self) -> List[str]:
        """List all available prompt categories."""
        categories = set()
        for data in self._prompts.values():
            categories.add(data.get("category", "root"))
        return sorted(list(categories))

    def update_prompt(self, name: str, updates: Dict) -> bool:
        """
        Update a prompt with new data.

        Args:
            name: Name of the prompt to update
            updates: Dictionary of fields to update

        Returns:
            True if successful

        Raises:
            ValueError: If prompt not found
        """
        if name not in self._prompts:
            raise ValueError(f"Prompt not found: {name}")

        prompt_data = self._prompts[name]
        file_path = prompt_data["file_path"]

        # Update the prompt data
        allowed_fields = ["template", "description", "system_prompt", 
                         "model_preferences", "parameters"]
        for key, value in updates.items():
            if key in allowed_fields:
                prompt_data[key] = value

        # Update metadata
        if "metadata" not in prompt_data:
            prompt_data["metadata"] = {}
        prompt_data["metadata"]["last_updated"] = datetime.now().isoformat()

        # Increment version
        current_version = prompt_data["metadata"].get("version", "1.0")
        try:
            major, minor = current_version.split(".")
            prompt_data["metadata"]["version"] = f"{major}.{int(minor) + 1}"
        except:
            prompt_data["metadata"]["version"] = "1.1"

        # Save back to file
        try:
            with open(file_path, 'w') as f:
                json.dump(prompt_data, f, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save prompt to file: {e}")

        # Update internal cache
        self._prompts[name] = prompt_data
        return True

    def create_prompt(self, name: str, template: str, description: str = "",
                     parameters: Optional[List[Dict]] = None,
                     system_prompt: str = "", category: str = "custom",
                     **kwargs) -> bool:
        """
        Create a new prompt.

        Args:
            name: Unique name for the prompt
            template: Prompt template string with {placeholders}
            description: Description of what the prompt does
            parameters: List of parameter definitions
            system_prompt: System prompt for the model
            category: Category for organizing prompts
            **kwargs: Additional fields for the prompt

        Returns:
            True if successful
        """
        if name in self._prompts:
            raise ValueError(f"Prompt already exists: {name}")

        prompt_data = {
            "name": name,
            "description": description,
            "template": template,
            "parameters": parameters or [],
            "system_prompt": system_prompt,
            "metadata": {
                "created_by": "ai_agent",
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "last_updated": datetime.now().isoformat()
            },
            **kwargs
        }

        # Determine file path
        category_dir = self.prompts_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        file_path = category_dir / f"{name}.json"

        # Save to file
        try:
            with open(file_path, 'w') as f:
                json.dump(prompt_data, f, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save prompt to file: {e}")

        # Register in internal cache
        self._register_prompt(prompt_data, file_path)
        return True

    def delete_prompt(self, name: str) -> bool:
        """
        Delete a prompt.

        Args:
            name: Name of the prompt to delete

        Returns:
            True if successful
        """
        if name not in self._prompts:
            raise ValueError(f"Prompt not found: {name}")

        prompt_data = self._prompts[name]
        file_path = prompt_data.get("file_path")

        # Remove from internal cache
        del self._prompts[name]

        # Delete file if it exists
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Failed to delete prompt file: {e}")

        return True

    def reload(self):
        """Reload all prompts from disk"""
        self._prompts = {}
        self._load_all_prompts()


# Singleton instance for convenience
_default_manager: Optional[PromptManager] = None


def get_prompt_manager(prompts_dir: str = None) -> PromptManager:
    """
    Get the default PromptManager instance.

    Args:
        prompts_dir: Optional custom prompts directory

    Returns:
        PromptManager instance
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = PromptManager(prompts_dir)
    return _default_manager


if __name__ == "__main__":
    # Test the prompt manager
    pm = PromptManager()
    print(f"Loaded {len(pm._prompts)} prompts")
    print(f"Categories: {pm.list_categories()}")
    print("\nAvailable prompts:")
    for p in pm.list_prompts():
        print(f"  - {p['name']} [{p['category']}]: {p['description'][:50]}...")
