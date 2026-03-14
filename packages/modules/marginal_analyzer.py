"""
Marginal Analysis Module - Phase 2

Implements Austrian Economic principles of marginal cost-benefit analysis
for LLM provider selection. Selects the most cost-effective provider that
meets quality requirements, not just the most powerful.

Core Principle:
"What is the next best use of this one unit of CPU time or one cent?"
- Symbiotic Partner Charter

This module enables decisions based on:
- Historical provider performance
- Current costs
- Opportunity cost of alternatives
- Utility per dollar spent
"""

import sqlite3
from decimal import Decimal
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta


class MarginalAnalyzer:
    """Performs marginal cost-benefit analysis for provider selection"""
    
    def __init__(self, db_path: str, scribe, economics_manager):
        """
        Initialize Marginal Analyzer
        
        Args:
            db_path: Path to database
            scribe: Scribe for logging
            economics_manager: EconomicManager for cost tracking
        """
        self.db_path = db_path
        self.scribe = scribe
        self.economics_manager = economics_manager
        
        # Cost defaults per provider ($/1K tokens)
        self.provider_cost_defaults = {
            'ollama': Decimal('0.000'),      # Free (local)
            'github': Decimal('0.000'),      # Free tier
            'venice': Decimal('0.002'),      # ~$2 per 1M tokens
            'openai': Decimal('0.010'),      # ~$10 per 1M tokens (GPT-4)
            'azure': Decimal('0.010')        # Similar to OpenAI
        }
        
        # Quality score defaults (0.0-1.0)
        self.quality_defaults = {
            'ollama': {'low': 0.70, 'medium': 0.65, 'high': 0.60},
            'github': {'low': 0.75, 'medium': 0.75, 'high': 0.75},
            'venice': {'low': 0.80, 'medium': 0.80, 'high': 0.80},
            'openai': {'low': 0.90, 'medium': 0.90, 'high': 0.90},
            'azure': {'low': 0.90, 'medium': 0.90, 'high': 0.90}
        }
    
    def analyze(self, available_providers: List[str], task_type: str,
                complexity: str, expected_tokens: int = 1000,
                minimum_quality_threshold: float = 0.7,
                preferred_provider: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Perform marginal analysis to select provider.
        
        Austrian Economics Implementation:
        - Calculates marginal utility per dollar spent
        - Considers opportunity cost of alternatives
        - Selects provider with highest utility/cost ratio above threshold
        
        Args:
            available_providers: List of provider names to consider
            task_type: Type of task (reasoning, coding, general, etc.)
            complexity: Complexity level (low, medium, high)
            expected_tokens: Expected token count (for cost estimation)
            minimum_quality_threshold: Minimum acceptable quality (0.0-1.0)
            preferred_provider: Override with specific provider
        
        Returns:
            Tuple of (selected_provider_name, analysis_dict)
        """
        # 1. Explicit override takes priority
        if preferred_provider and preferred_provider in available_providers:
            return preferred_provider, {
                'method': 'explicit_override',
                'provider': preferred_provider
            }
        
        # 2. Evaluate each provider
        candidates = []
        
        for provider_name in available_providers:
            try:
                # Get historical quality
                quality_score = self._get_provider_quality(
                    provider_name, task_type, complexity
                )
                
                # Only consider if above minimum quality
                if quality_score < minimum_quality_threshold:
                    continue
                
                # Estimate cost
                estimated_cost = self._estimate_provider_cost(
                    provider_name, expected_tokens
                )
                
                # Calculate marginal utility per dollar
                cost_decimal = max(Decimal(str(estimated_cost)), Decimal('0.000001'))
                utility_per_dollar = Decimal(str(quality_score)) / cost_decimal
                
                candidates.append({
                    'provider': provider_name,
                    'quality': quality_score,
                    'estimated_cost': float(estimated_cost),
                    'utility_per_dollar': float(utility_per_dollar),
                    'expected_tokens': expected_tokens
                })
            
            except Exception as e:
                # Skip providers that error
                continue
        
        # 3. Handle no qualified candidates
        if not candidates:
            return available_providers[0], {
                'method': 'fallback',
                'reason': 'no_qualified_candidates',
                'threshold': minimum_quality_threshold
            }
        
        # 4. Sort by utility per dollar (descending)
        candidates.sort(key=lambda x: x['utility_per_dollar'], reverse=True)
        
        best = candidates[0]
        
        # 5. Calculate opportunity cost (best alternative foregone)
        opportunity_cost = candidates[1]['utility_per_dollar'] if len(candidates) > 1 else 0.0
        
        # 6. Log decision
        self._log_analysis_decision(
            best['provider'],
            task_type,
            complexity,
            best['quality'],
            best['estimated_cost'],
            best['utility_per_dollar'],
            opportunity_cost,
            len(candidates),
            candidates
        )
        
        # 7. Build result
        analysis = {
            'method': 'marginal_analysis',
            'selected': best['provider'],
            'quality': best['quality'],
            'estimated_cost': best['estimated_cost'],
            'utility_per_dollar': best['utility_per_dollar'],
            'opportunity_cost': opportunity_cost,
            'alternatives_evaluated': len(candidates),
            'top_alternatives': candidates[1:4] if len(candidates) > 1 else []
        }
        
        return best['provider'], analysis
    
    def _get_provider_quality(self, provider: str, task_type: str, 
                              complexity: str) -> float:
        """
        Get historical quality score for provider on specific task type.
        
        Uses last 30 days of performance data.
        Falls back to defaults if no history.
        
        Returns: 0.0-1.0 quality score
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query historical performance (last 30 days)
            cursor.execute('''
                SELECT AVG(quality_score), COUNT(*)
                FROM provider_performance
                WHERE provider = ?
                  AND task_type = ?
                  AND timestamp >= datetime('now', '-30 days')
                  AND success = 1
            ''', (provider, task_type))
            
            row = cursor.fetchone()
            conn.close()
            
            # Need at least 5 samples for reliability
            if row and row[0] is not None and row[1] >= 5:
                return float(row[0])
        
        except Exception:
            pass
        
        # Fallback to defaults
        defaults = self.quality_defaults.get(provider, {})
        return defaults.get(complexity, 0.50)
    
    def _estimate_provider_cost(self, provider: str, tokens: int) -> Decimal:
        """
        Estimate cost for provider given token count.
        
        Uses historical data where available, falls back to defaults.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get average cost per token from history
            cursor.execute('''
                SELECT AVG(cost / tokens_used)
                FROM provider_performance
                WHERE provider = ?
                  AND tokens_used > 0
                  AND timestamp >= datetime('now', '-30 days')
            ''', (provider,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0] is not None:
                cost_per_token = Decimal(str(row[0]))
                return cost_per_token * Decimal(str(tokens))
        
        except Exception:
            pass
        
        # Fallback to defaults (cost per 1K tokens)
        rate_per_1k = self.provider_cost_defaults.get(provider, Decimal('0.005'))
        return (rate_per_1k * Decimal(str(tokens))) / Decimal('1000')
    
    def _log_analysis_decision(self, selected: str, task_type: str,
                               complexity: str, quality: float, cost: float,
                               utility_per_dollar: float, opportunity_cost: float,
                               alternatives_count: int, candidates: List[Dict]):
        """Log marginal analysis decision to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build reasoning string
            if alternatives_count > 1:
                alternatives_str = ", ".join([
                    f"{c['provider']}(${c['utility_per_dollar']:.4f})"
                    for c in candidates[1:3]
                ])
                reasoning = f"Selected {selected} with utility/$ = {utility_per_dollar:.4f}. Alternatives: {alternatives_str}"
            else:
                reasoning = f"Only {selected} qualified (quality={quality:.2f})"
            
            cursor.execute('''
                INSERT INTO marginal_analysis_log
                (timestamp, task_type, complexity, selected_provider, quality_score,
                 estimated_cost, utility_per_dollar, opportunity_cost,
                 alternatives_evaluated, reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                task_type,
                complexity,
                selected,
                quality,
                cost,
                utility_per_dollar,
                opportunity_cost,
                alternatives_count,
                reasoning
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            pass  # Silently fail
    
    def record_performance(self, provider: str, model: str, task_type: str,
                          complexity: str, quality_score: float,
                          response_time: float, tokens_used: int,
                          cost: float, success: bool = True):
        """
        Record provider performance for future marginal analysis.
        
        Args:
            provider: Provider name
            model: Model ID/name
            task_type: Type of task performed
            complexity: Task complexity level
            quality_score: Quality rating (0.0-1.0)
            response_time: Response time in seconds
            tokens_used: Tokens used
            cost: Cost in dollars
            success: Whether operation succeeded
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO provider_performance
                (timestamp, provider, model, task_type, complexity,
                 quality_score, response_time, tokens_used, cost, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                provider,
                model,
                task_type,
                complexity,
                quality_score,
                response_time,
                tokens_used,
                cost,
                1 if success else 0
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            self.scribe.log_action(
                "Provider performance recording failed",
                reasoning=str(e),
                outcome="Failed"
            )
    
    def get_analysis_history(self, hours: int = 24,
                            provider_filter: Optional[str] = None) -> List[Dict]:
        """
        Get marginal analysis decision history.
        
        Args:
            hours: Hours of history to retrieve
            provider_filter: Filter by specific provider
        
        Returns:
            List of analysis decisions
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if provider_filter:
                cursor.execute('''
                    SELECT * FROM marginal_analysis_log
                    WHERE selected_provider = ?
                      AND timestamp >= datetime('now', ? || ' hours')
                    ORDER BY timestamp DESC
                    LIMIT 50
                ''', (provider_filter, f'-{hours}'))
            else:
                cursor.execute('''
                    SELECT * FROM marginal_analysis_log
                    WHERE timestamp >= datetime('now', ? || ' hours')
                    ORDER BY timestamp DESC
                    LIMIT 50
                ''', (f'-{hours}',))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'task_type': row[2],
                    'complexity': row[3],
                    'selected': row[4],
                    'quality': row[5],
                    'cost': row[6],
                    'utility_per_dollar': row[7],
                    'opportunity_cost': row[8],
                    'alternatives': row[9],
                    'reasoning': row[10]
                })
            
            conn.close()
            return results
        
        except Exception:
            return []
    
    def get_provider_stats(self, provider: str, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a provider.
        
        Args:
            provider: Provider name
            days: Days of history to analyze
        
        Returns:
            Dict with provider statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get performance stats
            cursor.execute('''
                SELECT
                  COUNT(*) as total_requests,
                  SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                  AVG(quality_score) as avg_quality,
                  AVG(response_time) as avg_response_time,
                  AVG(cost) as avg_cost,
                  SUM(cost) as total_cost,
                  AVG(tokens_used) as avg_tokens
                FROM provider_performance
                WHERE provider = ?
                  AND timestamp >= datetime('now', ? || ' days')
            ''', (provider, f'-{days}'))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                total_requests = row[0] or 0
                successful = row[1] or 0
                
                return {
                    'provider': provider,
                    'period_days': days,
                    'total_requests': total_requests,
                    'successful_requests': successful,
                    'success_rate': (successful / total_requests * 100) if total_requests > 0 else 0,
                    'avg_quality': float(row[2]) if row[2] else 0,
                    'avg_response_time': float(row[3]) if row[3] else 0,
                    'avg_cost': float(row[4]) if row[4] else 0,
                    'total_cost': float(row[5]) if row[5] else 0,
                    'avg_tokens': int(row[6]) if row[6] else 0
                }
        
        except Exception:
            pass
        
        return {}
