"""
Prompts Package - Centralized AI Prompt Management

This package provides a centralized system for managing AI prompts.

USAGE:
    from prompts import get_prompt_manager
    
    pm = get_prompt_manager()
    prompt_data = pm.get_prompt("code_review_suggestions",
                                module_name="router",
                                lines_of_code=200,
                                function_count=10,
                                complexity_list=[])
"""

from .manager import PromptManager, get_prompt_manager

__all__ = ["PromptManager", "get_prompt_manager"]
