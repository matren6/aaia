# modules/prompt_optimizer.py
"""
Prompt Optimizer Module - AI Self-Modification for Prompts

PURPOSE:
This module enables the AI to optimize its own prompts based on performance metrics.
It provides A/B testing capabilities and automatic prompt improvement suggestions.

KEY FEATURES:
1. Optimize prompts based on performance metrics
2. A/B test new prompt versions against originals
3. Generate optimization suggestions using AI
4. Track prompt performance over time

DEPENDENCIES: PromptManager, ModelRouter, Scribe
"""

from datetime import datetime
from typing import Dict, List, Any, Optional


class PromptOptimizer:
    """AI-powered prompt optimization and A/B testing"""
    
    def __init__(self, prompt_manager, router, scribe):
        """Initialize PromptOptimizer.
        
        Args:
            prompt_manager: PromptManager instance
            router: ModelRouter for AI calls
            scribe: Scribe instance for logging
        """
        self.prompt_manager = prompt_manager
        self.router = router
        self.scribe = scribe
        self._performance_history: Dict[str, List[Dict]] = {}
    
    def optimize_prompt(self, prompt_name: str, performance_metrics: Dict) -> str:
        """Optimize a prompt based on performance metrics.
        
        Args:
            prompt_name: Name of the prompt to optimize
            performance_metrics: Dict with 'issues' and 'success_criteria'
            
        Returns:
            Name of the test prompt created
        """
        # Get current prompt
        try:
            prompt_data = self.prompt_manager.get_prompt_raw(prompt_name)
        except ValueError as e:
            self.scribe.log_action(
                f"Prompt optimization failed",
                f"Prompt not found: {prompt_name}",
                "error"
            )
            raise
        
        current_template = prompt_data.get("template", "")
        
        # Generate optimization suggestions using PromptManager if available
        suggestions = None
        try:
            if self.prompt_manager:
                opt_prompt = self.prompt_manager.get_prompt(
                    "prompt_optimization",
                    current_prompt=current_template,
                    performance_issues=performance_metrics.get("issues", []),
                    success_criteria=performance_metrics.get("success_criteria", "")
                )
                
                suggestions = self.router.generate(opt_prompt["prompt"],
                    opt_prompt["system_prompt"]
                )
        except Exception as e:
            self.scribe.log_action(
                "Prompt optimization attempt",
                f"Using PromptManager attempt failed: {str(e)}",
                "warning"
            )
        
        # Do not use inline hardcoded prompts. If suggestions were not produced
        # above, attempt to fetch the centralized `prompt_optimization` template
        # from PromptManager and use it. If that fails, log and raise.
        if not suggestions:
            try:
                if self.prompt_manager:
                    opt_prompt = self.prompt_manager.get_prompt(
                        "prompt_optimization",
                        current_prompt=current_template,
                        performance_issues=performance_metrics.get("issues", []),
                        success_criteria=performance_metrics.get("success_criteria", "Improve clarity and effectiveness")
                    )
                    
                    suggestions = self.router.generate(opt_prompt["prompt"],
                        opt_prompt.get("system_prompt", "You are a prompt engineering expert.")
                    )
            except Exception as e:
                self.scribe.log_action(
                    "Prompt optimization failed",
                    f"Error: {str(e)}",
                    "error"
                )
                raise ValueError(f"Failed to optimize prompt: {e}")
        
        # Parse optimization suggestions
        new_template = self._parse_optimization_suggestions(suggestions)
        
        # Create a test version of the prompt
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        test_name = f"{prompt_name}_test_{timestamp}"
        
        try:
            self.prompt_manager.create_prompt(
                name=test_name,
                template=new_template,
                description=f"Test version of {prompt_name} - optimized",
                category="tests"
            )
        except Exception as e:
            # If create fails, try to save to a custom location
            self.prompt_manager.create_prompt(
                name=test_name,
                template=new_template,
                description=f"Test version of {prompt_name}",
                category="custom"
            )
        
        self.scribe.log_action(
            f"Created test prompt: {test_name}",
            f"Based on {prompt_name}",
            "prompt_created"
        )
        
        return test_name
    
    def a_b_test_prompt(self, original_name: str, test_name: str, 
                        test_cases: List[Dict]) -> Dict:
        """A/B test a new prompt against the original.
        
        Args:
            original_name: Name of the original prompt
            test_name: Name of the test prompt
            test_cases: List of test cases with 'input' and expected 'output'
            
        Returns:
            Dict with test results and recommendation
        """
        results = {
            "original": {"success": 0, "total": 0, "quality_scores": []},
            "test": {"success": 0, "total": 0, "quality_scores": []}
        }
        
        for test_case in test_cases:
            # Test original prompt
            try:
                original_response = self._test_prompt_with_case(
                    original_name, test_case
                )
                results["original"]["total"] += 1
                if original_response.get("success", False):
                    results["original"]["success"] += 1
                quality = original_response.get("quality", 0)
                if quality > 0:
                    results["original"]["quality_scores"].append(quality)
            except Exception as e:
                self.scribe.log_action(
                    f"Prompt test failed for {original_name}",
                    f"Error: {str(e)}",
                    "error"
                )
            
            # Test new prompt
            try:
                test_response = self._test_prompt_with_case(test_name, test_case)
                results["test"]["total"] += 1
                if test_response.get("success", False):
                    results["test"]["success"] += 1
                quality = test_response.get("quality", 0)
                if quality > 0:
                    results["test"]["quality_scores"].append(quality)
            except Exception as e:
                self.scribe.log_action(
                    f"Prompt test failed for {test_name}",
                    f"Error: {str(e)}",
                    "error"
                )
        
        # Calculate results
        orig_total = results["original"]["total"]
        test_total = results["test"]["total"]
        
        if orig_total == 0 or test_total == 0:
            return {
                "winner": "insufficient_data",
                "error": "No valid test results"
            }
        
        original_success_rate = results["original"]["success"] / orig_total
        test_success_rate = results["test"]["success"] / test_total
        
        orig_quality = results["original"]["quality_scores"]
        test_quality = results["test"]["quality_scores"]
        
        original_avg_quality = sum(orig_quality) / len(orig_quality) if orig_quality else 0
        test_avg_quality = sum(test_quality) / len(test_quality) if test_quality else 0
        
        # Determine winner
        winner = "test" if (test_success_rate >= original_success_rate and 
                           test_avg_quality >= original_avg_quality - 0.1) else "original"
        
        result = {
            "winner": winner,
            "original_success_rate": round(original_success_rate, 3),
            "test_success_rate": round(test_success_rate, 3),
            "original_avg_quality": round(original_avg_quality, 2),
            "test_avg_quality": round(test_avg_quality, 2),
            "recommendation": "Replace" if winner == "test" else "Keep original",
            "total_tests": orig_total
        }
        
        self.scribe.log_action(
            f"A/B test completed: {winner} wins",
            f"Original: {original_success_rate:.2f}, Test: {test_success_rate:.2f}",
            "ab_test_completed"
        )
        
        return result
    
    def _test_prompt_with_case(self, prompt_name: str, test_case: Dict) -> Dict:
        """Test a single prompt with a test case.
        
        Args:
            prompt_name: Name of the prompt to test
            test_case: Dict with 'input' and optionally 'expected'
            
        Returns:
            Dict with 'success', 'quality', and 'response'
        """
        try:
            # Get prompt with test input
            prompt_data = self.prompt_manager.get_prompt(
                prompt_name,
                **test_case.get("params", {})
            )

            # Call the model
            response = self.router.generate(
                prompt_data["prompt"],
                system_prompt=prompt_data["system_prompt"],
                task_type="optimization",
                complexity="high"
            )
            
            # Evaluate response quality
            quality = self._evaluate_response(
                response, 
                test_case.get("expected", "")
            )
            
            return {
                "success": quality >= 0.5,
                "quality": quality,
                "response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "quality": 0,
                "error": str(e)
            }
    
    def _evaluate_response(self, response: str, expected: str) -> float:
        """Evaluate response quality (0-1 score).
        
        Args:
            response: Model response
            expected: Expected response pattern
            
        Returns:
            Quality score between 0 and 1
        """
        if not response or len(response.strip()) < 5:
            return 0.0
        
        # Simple quality checks
        score = 0.5  # Base score for having a response
        
        # Check response length (reasonable length gets bonus)
        if 50 < len(response) < 2000:
            score += 0.2
        
        # Check for expected keywords if provided
        if expected:
            expected_lower = expected.lower()
            response_lower = response.lower()
            matches = sum(1 for word in expected_lower.split() 
                         if len(word) > 3 and word in response_lower)
            if matches > 0:
                score += min(0.3, matches * 0.1)
        
        return min(1.0, score)
    
    def _parse_optimization_suggestions(self, suggestions: str) -> str:
        """Parse AI optimization suggestions into a prompt template.
        
        Args:
            suggestions: Raw AI suggestions
            
        Returns:
            Optimized prompt template string
        """
        # Try to extract a clean prompt from the suggestions
        lines = suggestions.strip().split('\n')
        
        # Look for the optimized prompt (after "OPTIMIZED:" or similar marker)
        in_optimized_section = False
        optimized_lines = []
        
        markers = ["optimized prompt:", "improved prompt:", "new prompt:", 
                   "===optimized===", "---optimized---"]
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check for section markers
            if any(marker in line_lower for marker in markers):
                in_optimized_section = True
                continue
            
            # Collect lines in optimized section
            if in_optimized_section:
                if line.strip() and not line.strip().startswith('#'):
                    # Check for end markers
                    if line.strip().startswith('---') or '---' in line:
                        break
                    optimized_lines.append(line)
        
        # If we found optimized content, use it
        if optimized_lines:
            # Clean up the lines
            cleaned = []
            for line in optimized_lines:
                # Remove numbering/bullets
                cleaned_line = line.strip()
                if cleaned_line and len(cleaned_line) > 2:
                    # Remove leading markers
                    for prefix in ['-', '*', '1.', '2.', '3.']:
                        if cleaned_line.startswith(prefix):
                            cleaned_line = cleaned_line[len(prefix):].strip()
                    if cleaned_line:
                        cleaned.append(cleaned_line)
            
            if cleaned:
                return '\n'.join(cleaned)
        
        # Fallback: return the raw suggestions but cleaned
        return suggestions.strip()
    
    def track_performance(self, prompt_name: str, metrics: Dict):
        """Track performance metrics for a prompt over time.
        
        Args:
            prompt_name: Name of the prompt
            metrics: Dict with performance metrics
        """
        if prompt_name not in self._performance_history:
            self._performance_history[prompt_name] = []
        
        self._performance_history[prompt_name].append({
            "timestamp": datetime.now().isoformat(),
            **metrics
        })
    
    def get_prompt_performance(self, prompt_name: str) -> Dict:
        """Get aggregated performance metrics for a prompt.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            Dict with aggregated metrics
        """
        history = self._performance_history.get(prompt_name, [])
        
        if not history:
            return {
                "total_uses": 0,
                "avg_success_rate": 0,
                "avg_quality": 0
            }
        
        total = len(history)
        success_count = sum(1 for h in history if h.get("success", False))
        quality_sum = sum(h.get("quality", 0) for h in history)
        
        return {
            "total_uses": total,
            "success_rate": round(success_count / total, 3) if total > 0 else 0,
            "avg_quality": round(quality_sum / total, 2) if total > 0 else 0,
            "history": history
        }
    
    def get_prompts_needing_optimization(self, min_uses: int = 5) -> List[Dict]:
        """Get prompts that may need optimization based on performance.
        
        Args:
            min_uses: Minimum number of uses to consider
            
        Returns:
            List of prompts with poor performance
        """
        needs_optimization = []
        
        for prompt_name, history in self._performance_history.items():
            if len(history) < min_uses:
                continue
            
            perf = self.get_prompt_performance(prompt_name)
            
            if perf["success_rate"] < 0.7 or perf["avg_quality"] < 3.0:
                needs_optimization.append({
                    "name": prompt_name,
                    "success_rate": perf["success_rate"],
                    "avg_quality": perf["avg_quality"],
                    "total_uses": perf["total_uses"]
                })
        
        return needs_optimization
