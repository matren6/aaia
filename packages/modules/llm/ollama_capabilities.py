"""
Ollama Model Capability Classification

Uses Ollama's native /api/show endpoint to get:
- Direct capabilities (completion, vision, embedding)
- Exact context window from model_info
- Model family and parameters

Falls back to heuristics only for:
- Code optimization (not exposed by Ollama API)
- Function calling support (not exposed by Ollama API)
"""

from typing import Dict, List, Optional
import re


def extract_capabilities_from_show(show_response: Dict) -> Dict[str, bool]:
    """Extract AAIA capabilities from /api/show response
    
    Uses Ollama's native capabilities array for vision and reasoning,
    falls back to heuristics for code and function calling.
    
    Args:
        show_response: Full response from /api/show endpoint
        
    Returns:
        Dict with AAIA capability flags:
        {
            'code': bool,
            'reasoning': bool,
            'vision': bool,
            'function_calling': bool
        }
    """
    # Get Ollama's native capabilities
    ollama_caps = show_response.get('capabilities', [])
    
    # Get model metadata for heuristics
    details = show_response.get('details', {})
    model_name = show_response.get('name', '')
    family = details.get('family', '')
    
    # Initialize capabilities
    capabilities = {
        'code': False,
        'reasoning': False,
        'vision': False,
        'function_calling': False
    }
    
    # 1. VISION - Direct from Ollama (100% accurate)
    if 'vision' in ollama_caps:
        capabilities['vision'] = True
    
    # 2. REASONING - Inferred from completion capability
    if 'completion' in ollama_caps or 'chat' in ollama_caps:
        capabilities['reasoning'] = True
    
    # 3. CODE - Heuristic (Ollama doesn't expose this)
    capabilities['code'] = _is_code_optimized(model_name, family)
    
    # 4. FUNCTION CALLING - Heuristic (Ollama doesn't expose this)
    capabilities['function_calling'] = _supports_function_calling(model_name, family)
    
    return capabilities


def _is_code_optimized(model_name: str, family: str) -> bool:
    """Check if model is code-optimized using name/family heuristics
    
    Args:
        model_name: Full model name (e.g., "codellama:13b")
        family: Model family (e.g., "llama")
    
    Returns:
        True if model is likely code-optimized
    """
    name_lower = model_name.lower()
    family_lower = family.lower()
    
    # Explicit code model families
    CODE_FAMILIES = {
        'codellama', 'deepseek-coder', 'starcoder', 
        'codegemma', 'qwen-coder', 'qwen2.5-coder',
        'codeqwen', 'stablecodellama'
    }
    
    if any(cf in family_lower for cf in CODE_FAMILIES):
        return True
    
    # Name explicitly mentions code
    if 'code' in name_lower or 'coder' in name_lower:
        return True
    
    # General-purpose models can do code (broad capability)
    GENERAL_CAPABLE = {'llama', 'mistral', 'gemma', 'phi', 'qwen', 'yi'}
    if any(gf in family_lower for gf in GENERAL_CAPABLE):
        return True
    
    return False


def _supports_function_calling(model_name: str, family: str) -> bool:
    """Check if model supports function/tool calling using version heuristics
    
    Args:
        model_name: Full model name
        family: Model family
    
    Returns:
        True if model likely supports function calling
    """
    name_lower = model_name.lower()
    
    # Known function-calling capable models by version
    FUNCTION_MODELS = {
        'llama3.1', 'llama3.2', 'llama3.3',
        'mixtral', 'mistral-large',
        'qwen2.5', 'qwen-plus',
        'hermes', 'nous-hermes',
        'functionary',
    }
    
    return any(fm in name_lower for fm in FUNCTION_MODELS)


def extract_context_window(show_response: Dict) -> int:
    """Extract context window from /api/show response
    
    Priority chain:
    1. model_info["*.context_length"] - Most reliable (from GGUF metadata)
    2. parameters "num_ctx" - User runtime override
    3. Estimate from parameter size - Conservative fallback
    
    Args:
        show_response: Full response from /api/show
        
    Returns:
        Context window size in tokens
    """
    # Priority 1: Direct from model_info (most reliable)
    model_info = show_response.get('model_info', {})
    for key, value in model_info.items():
        if 'context_length' in key.lower():
            try:
                return int(value)
            except (ValueError, TypeError):
                pass
    
    # Priority 2: Runtime parameter override
    parameters = show_response.get('parameters', '')
    num_ctx_match = re.search(r'num_ctx\s+(\d+)', parameters)
    if num_ctx_match:
        return int(num_ctx_match.group(1))
    
    # Priority 3: Estimate from parameter size
    details = show_response.get('details', {})
    param_size = _parse_param_size(details.get('parameter_size', '0B'))
    
    # Conservative estimates (lower is safer)
    if param_size <= 3:
        return 4096
    elif param_size <= 7:
        return 8192
    elif param_size <= 13:
        return 8192
    elif param_size <= 34:
        return 32768
    elif param_size <= 70:
        return 65536
    else:
        return 131072


def _parse_param_size(size_str: str) -> float:
    """Parse parameter size string to float (in billions)
    
    Examples:
        "3.2B" → 3.2
        "13B" → 13.0
        "70B" → 70.0
        "7.2B" → 7.2
    
    Args:
        size_str: Parameter size string from Ollama
    
    Returns:
        Size in billions as float
    """
    match = re.search(r'([\d.]+)\s*B', size_str.upper())
    if match:
        return float(match.group(1))
    return 0.0


def calculate_speed_score(details: Dict) -> int:
    """Calculate speed score for model ranking (lower = faster)
    
    Factors:
    - Parameter size: Smaller models are faster
    - Quantization level: Lower precision is faster
    
    Since Ollama is free (local), "cost" = speed/latency.
    We want to pick the FASTEST suitable model.
    
    Args:
        details: Model details from /api/show
    
    Returns:
        Speed score (lower is better, use for sorting)
    """
    # Base score from parameter count
    param_size = _parse_param_size(details.get('parameter_size', '0B'))
    score = int(param_size * 10)  # 3B → 30, 70B → 700
    
    # Adjust for quantization (lower quant = faster)
    quant_level = details.get('quantization_level', 'Q4_0')
    
    quant_multipliers = {
        'Q2': 0.8,
        'Q3': 0.9,
        'Q4': 1.0,
        'Q5': 1.1,
        'Q6': 1.2,
        'Q8': 1.3,
        'F16': 1.5,
        'F32': 2.0,
    }
    
    for quant_prefix, multiplier in quant_multipliers.items():
        if quant_level.startswith(quant_prefix):
            score = int(score * multiplier)
            break
    
    return score


def get_model_description(details: Dict) -> str:
    """Generate human-readable model description
    
    Args:
        details: Model details from /api/show
    
    Returns:
        Description string like "7B parameters, Q4_0 quantization"
    """
    param_size = details.get('parameter_size', 'Unknown')
    quant = details.get('quantization_level', 'Unknown')
    
    return f"{param_size} parameters, {quant} quantization"
