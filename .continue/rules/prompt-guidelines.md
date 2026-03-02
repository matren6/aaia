# Prompt Management Guidelines

## Golden Rule
**ALL AI prompts MUST use the PromptManager system. Never hardcode prompts in Python code.**

## Prompt Structure

### Required Fields
Every prompt JSON file MUST contain:
- `name`: Unique identifier
- `description`: What the prompt does
- `template`: The prompt template with {placeholders}
- `system_prompt`: System-level instructions for the model
- `parameters`: Array of parameter definitions

### Example Structure
```json
{
  "name": "code_analysis",
  "description": "Analyze Python code for improvements",
  "template": "Analyze this code:\n\n{code}\n\nProvide improvements in:\n1. Structure\n2. Performance\n3. Documentation",
  "parameters": [
    {"name": "code", "type": "string", "required": true}
  ],
  "system_prompt": "You are a code review expert providing actionable feedback.",
  "model_preferences": {
    "task_type": "analysis",
    "complexity": "high"
  },
  "metadata": {
    "created_by": "system",
    "created_at": "2024-01-01T00:00:00Z",
    "version": "1.0"
  }
}
```

## Prompt Categories

Organize prompts by category in subdirectories:

### `packages/prompts/analysis/`
- Code analysis prompts
- System diagnosis prompts
- Performance analysis prompts

### `packages/prompts/dialogue/`
- Command understanding prompts
- Risk analysis prompts
- Structured argument prompts

### `packages/prompts/generation/`
- Code generation prompts
- Tool creation prompts
- Goal planning prompts

### `packages/prompts/system/`
- Reflection prompts
- Health check prompts
- Strategy prompts

## Using Prompts in Code

### Basic Usage
```python
from prompts import get_prompt_manager

pm = get_prompt_manager()
prompt_data = pm.get_prompt(
    "prompt_name",
    param1=value1,
    param2=value2
)
```

### Accessing Components
```python
# prompt_data contains:
prompt_data['prompt']           # Formatted prompt string
prompt_data['system_prompt']    # System instructions
prompt_data['model_preferences'] # Model selection hints
prompt_data['raw']              # Original prompt data
```

### Error Handling
```python
try:
    prompt_data = pm.get_prompt("nonexistent_prompt", param=value)
except ValueError as e:
    # Handle missing prompt
    # Fallback to inline prompt only in emergencies
    pass
```

## Prompt Creation Checklist

When creating a new prompt:

1. ✅ **Unique Name**: Check that name doesn't already exist
2. ✅ **Clear Description**: Explain what the prompt does
3. ✅ **Template**: Use {placeholders} for dynamic content
4. ✅ **Parameters**: Define all placeholders with types
5. ✅ **System Prompt**: Set role and behavior instructions
6. ✅ **Model Preferences**: Specify task type and complexity
7. ✅ **Category**: Place in appropriate subdirectory
8. ✅ **Version**: Start at 1.0, increment on updates

## Prompt Optimization

### Performance Issues
If a prompt isn't working well:

1. Analyze the prompt structure
2. Use PromptOptimizer to create test version
3. A/B test against original
4. Update if test version performs better

### Updating Existing Prompts
```python
pm.update_prompt("prompt_name", {
    "template": "new improved template",
    "description": "updated description"
})
```

## Common Prompt Patterns

### Analysis Prompts
- Structure: Input data → Analysis criteria → Output format
- Use clear section headers
- Specify output format precisely

### Generation Prompts
- Include constraints and boundaries
- Provide examples if helpful
- Specify quality requirements

### Planning Prompts
- Focus on actionable steps
- Consider dependencies
- Estimate effort and benefits

## Anti-Patterns

### ❌ Hardcoded Multi-line Prompts
```python
prompt = f"""
Analyze this code:
{code}

Provide improvements:
1. Structure
2. Performance
"""
```

### ❌ Prompt Strings in Variables
```python
SYSTEM_PROMPT = "You are an AI assistant..."
```

### ❌ Conditional Prompt Construction
```python
if condition:
    prompt = "Prompt A"
else:
    prompt = "Prompt B"
```

## Prompt Discovery

To find existing prompts:
```python
pm = get_prompt_manager()
prompts = pm.list_prompts()
categories = pm.list_categories()

for prompt in prompts:
    print(f"{prompt['name']}: {prompt['description']}")
```

## Migration Path

When refactoring code to use PromptManager:

1. Identify hardcoded prompts in code
2. Extract to JSON file in appropriate category
3. Define parameters for dynamic content
4. Replace hardcoded prompt with pm.get_prompt()
5. Test that behavior is preserved
6. Delete hardcoded prompt string


