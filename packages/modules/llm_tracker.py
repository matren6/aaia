"""
LLM Interaction Tracker Module

Tracks all AI prompt/response interactions for analysis, debugging, and optimization.
Provides comprehensive logging of LLM usage patterns.

KEY RESPONSIBILITIES:
1. Log all LLM requests and responses
2. Track performance metrics (latency, tokens, cost)
3. Provide query interface for analysis
4. Enable web UI inspection
5. Support optimization and debugging
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sqlite3
import json
import time


class LLMInteractionTracker:
    """Tracks and analyzes all LLM interactions"""
    
    def __init__(self, database_manager, scribe, event_bus=None):
        """
        Initialize LLM Interaction Tracker
        
        Args:
            database_manager: Database manager
            scribe: Scribe for logging
            event_bus: Optional event bus for subscriptions
        """
        self.database_manager = database_manager
        self.scribe = scribe
        self.event_bus = event_bus
        self.db = database_manager.get_connection()
        
        # Subscribe to LLM events if event bus available
        if self.event_bus:
            try:
                from modules.bus import EventType
                self.event_bus.subscribe(EventType.LLM_RESPONSE, self._on_llm_response)
                self.event_bus.subscribe(EventType.LLM_ERROR, self._on_llm_error)
            except:
                pass
    
    def log_interaction(self, provider: str, model: str, prompt: str,
                       response: str, tokens_used: int = 0, cost: float = 0.0,
                       latency_ms: int = 0, system_prompt: str = None,
                       success: bool = True, error: str = None,
                       context: str = None, metadata: Dict = None) -> int:
        """
        Log an LLM interaction.
        
        Args:
            provider: Provider name (ollama, openai, venice, etc.)
            model: Model name (llama3.2:3b, gpt-4, etc.)
            prompt: The prompt sent to the model
            response: The model's response
            tokens_used: Number of tokens consumed
            cost: Cost of the request
            latency_ms: Response time in milliseconds
            system_prompt: Optional system prompt
            success: Whether request succeeded
            error: Error message if failed
            context: What triggered this request
            metadata: Additional metadata
            
        Returns:
            Interaction ID
        """
        cursor = self.db.cursor()
        
        cursor.execute('''
            INSERT INTO llm_interactions
            (timestamp, provider, model, prompt, system_prompt, response,
             tokens_used, cost, latency_ms, success, error, context, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            provider,
            model,
            prompt[:5000],  # Truncate very long prompts
            system_prompt[:2000] if system_prompt else None,
            response[:10000],  # Truncate very long responses
            tokens_used,
            cost,
            latency_ms,
            1 if success else 0,
            error[:500] if error else None,
            context[:500] if context else None,
            json.dumps(metadata) if metadata else None
        ))
        
        self.db.commit()
        interaction_id = cursor.lastrowid
        
        # Log summary
        if not success:
            self.scribe.log_action(
                f"LLM interaction failed: {provider}/{model}",
                reasoning=f"Error: {error}",
                outcome="Error"
            )
        
        return interaction_id
    
    def _on_llm_response(self, event):
        """Handle LLM_RESPONSE event"""
        try:
            data = event.data
            self.log_interaction(
                provider=data.get('provider', 'unknown'),
                model=data.get('model', 'unknown'),
                prompt=data.get('prompt', ''),
                response=data.get('response', ''),
                tokens_used=data.get('tokens_used', 0),
                cost=data.get('cost', 0.0),
                latency_ms=data.get('latency_ms', 0),
                system_prompt=data.get('system_prompt'),
                success=True,
                context=data.get('context')
            )
        except Exception as e:
            self.scribe.log_action(
                "LLM response tracking failed",
                reasoning=str(e),
                outcome="Error"
            )
    
    def _on_llm_error(self, event):
        """Handle LLM_ERROR event"""
        try:
            data = event.data
            self.log_interaction(
                provider=data.get('provider', 'unknown'),
                model=data.get('model', 'unknown'),
                prompt=data.get('prompt', ''),
                response='',
                tokens_used=0,
                cost=0.0,
                success=False,
                error=data.get('error'),
                context=data.get('context')
            )
        except Exception as e:
            self.scribe.log_action(
                "LLM error tracking failed",
                reasoning=str(e),
                outcome="Error"
            )
    
    def get_interactions(self, provider: str = None, model: str = None,
                        success_only: bool = False, limit: int = 100,
                        offset: int = 0, hours: int = None) -> List[Dict]:
        """
        Get LLM interactions with filtering.
        
        Args:
            provider: Filter by provider
            model: Filter by model
            success_only: Only successful interactions
            limit: Max results
            offset: Pagination offset
            hours: Only last N hours
            
        Returns:
            List of interaction records
        """
        cursor = self.db.cursor()
        
        # Build query
        query = 'SELECT * FROM llm_interactions WHERE 1=1'
        params = []
        
        if provider:
            query += ' AND provider = ?'
            params.append(provider)
        
        if model:
            query += ' AND model = ?'
            params.append(model)
        
        if success_only:
            query += ' AND success = 1'
        
        if hours:
            since = (datetime.now() - timedelta(hours=hours)).isoformat()
            query += ' AND timestamp > ?'
            params.append(since)
        
        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        interactions = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            interaction = dict(zip(columns, row))
            # Parse JSON metadata
            if interaction.get('metadata'):
                try:
                    interaction['metadata'] = json.loads(interaction['metadata'])
                except:
                    pass
            interactions.append(interaction)
        
        return interactions
    
    def get_interaction_stats(self, hours: int = 24) -> Dict:
        """
        Get statistics about LLM usage.
        
        Args:
            hours: Time period to analyze
            
        Returns:
            Dict with statistics
        """
        cursor = self.db.cursor()
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        # Total interactions
        cursor.execute('''
            SELECT COUNT(*), SUM(tokens_used), SUM(cost), AVG(latency_ms)
            FROM llm_interactions
            WHERE timestamp > ?
        ''', (since,))
        
        row = cursor.fetchone()
        total_count = row[0] or 0
        total_tokens = row[1] or 0
        total_cost = row[2] or 0.0
        avg_latency = row[3] or 0
        
        # Success rate
        cursor.execute('''
            SELECT COUNT(*) FROM llm_interactions
            WHERE timestamp > ? AND success = 1
        ''', (since,))
        
        success_count = cursor.fetchone()[0] or 0
        success_rate = (success_count / total_count) if total_count > 0 else 0
        
        # By provider
        cursor.execute('''
            SELECT provider, COUNT(*), SUM(tokens_used), SUM(cost)
            FROM llm_interactions
            WHERE timestamp > ?
            GROUP BY provider
        ''', (since,))
        
        by_provider = {}
        for row in cursor.fetchall():
            by_provider[row[0]] = {
                'count': row[1],
                'tokens': row[2] or 0,
                'cost': row[3] or 0.0
            }
        
        # By model
        cursor.execute('''
            SELECT model, COUNT(*), SUM(tokens_used), SUM(cost)
            FROM llm_interactions
            WHERE timestamp > ?
            GROUP BY model
        ''', (since,))
        
        by_model = {}
        for row in cursor.fetchall():
            by_model[row[0]] = {
                'count': row[1],
                'tokens': row[2] or 0,
                'cost': row[3] or 0.0
            }
        
        # Recent errors
        cursor.execute('''
            SELECT timestamp, provider, model, error
            FROM llm_interactions
            WHERE timestamp > ? AND success = 0
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (since,))
        
        recent_errors = []
        for row in cursor.fetchall():
            recent_errors.append({
                'timestamp': row[0],
                'provider': row[1],
                'model': row[2],
                'error': row[3]
            })
        
        return {
            'period_hours': hours,
            'total_interactions': total_count,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'avg_latency_ms': avg_latency,
            'success_rate': success_rate,
            'by_provider': by_provider,
            'by_model': by_model,
            'recent_errors': recent_errors
        }
    
    def get_interaction_by_id(self, interaction_id: int) -> Optional[Dict]:
        """
        Get specific interaction by ID.
        
        Args:
            interaction_id: Interaction ID
            
        Returns:
            Interaction record or None
        """
        cursor = self.db.cursor()
        
        cursor.execute('SELECT * FROM llm_interactions WHERE id = ?', (interaction_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        columns = [desc[0] for desc in cursor.description]
        interaction = dict(zip(columns, row))
        
        # Parse JSON metadata
        if interaction.get('metadata'):
            try:
                interaction['metadata'] = json.loads(interaction['metadata'])
            except:
                pass
        
        return interaction
    
    def search_interactions(self, search_term: str, limit: int = 50) -> List[Dict]:
        """
        Search interactions by prompt or response content.
        
        Args:
            search_term: Text to search for
            limit: Max results
            
        Returns:
            List of matching interactions
        """
        cursor = self.db.cursor()
        
        search_pattern = f"%{search_term}%"
        
        cursor.execute('''
            SELECT * FROM llm_interactions
            WHERE prompt LIKE ? OR response LIKE ? OR context LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (search_pattern, search_pattern, search_pattern, limit))
        
        interactions = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            interaction = dict(zip(columns, row))
            if interaction.get('metadata'):
                try:
                    interaction['metadata'] = json.loads(interaction['metadata'])
                except:
                    pass
            interactions.append(interaction)
        
        return interactions
    
    def get_expensive_interactions(self, hours: int = 24, limit: int = 20) -> List[Dict]:
        """
        Get most expensive LLM interactions.
        
        Useful for cost optimization analysis.
        
        Args:
            hours: Time period
            limit: Max results
            
        Returns:
            List of expensive interactions
        """
        cursor = self.db.cursor()
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute('''
            SELECT * FROM llm_interactions
            WHERE timestamp > ?
            ORDER BY cost DESC
            LIMIT ?
        ''', (since, limit))
        
        interactions = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            interactions.append(dict(zip(columns, row)))
        
        return interactions
    
    def cleanup_old_interactions(self, days: int = 30) -> int:
        """
        Clean up old interactions to save space.
        
        Args:
            days: Keep interactions newer than this
            
        Returns:
            Number of interactions deleted
        """
        cursor = self.db.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            DELETE FROM llm_interactions
            WHERE timestamp < ?
        ''', (cutoff,))
        
        self.db.commit()
        deleted = cursor.rowcount
        
        self.scribe.log_action(
            f"Cleaned up old LLM interactions",
            reasoning=f"Removed interactions older than {days} days",
            outcome=f"Deleted {deleted} records"
        )
        
        return deleted
