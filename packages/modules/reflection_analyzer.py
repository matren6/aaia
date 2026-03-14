"""
Enhanced Reflection Analysis Module (Phase 5 - Fix 9)

Provides deeper AI-powered reflection on master model insights and trends.
Generates weekly insights, predicts future preferences, and provides strategic recommendations.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from modules.scribe import Scribe


class ReflectionAnalyzer:
    """Enhanced reflection analysis using AI"""
    
    def __init__(self, prompt_manager, router, scribe, event_bus=None):
        """
        Initialize Reflection Analyzer
        
        Args:
            prompt_manager: Prompt manager for templates
            router: LLM router for analysis
            scribe: Action logger
            event_bus: Optional event bus
        """
        self.prompt_manager = prompt_manager
        self.router = router
        self.scribe = scribe
        self.event_bus = event_bus
    
    def generate_weekly_insights(self, master_profile: Dict[str, Any],
                               recent_interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate weekly insights from master model and interactions.
        
        Args:
            master_profile: Current master psychological profile
            recent_interactions: Recent interaction history
            
        Returns:
            Dictionary of insights and recommendations
        """
        try:
            # Prepare data for analysis
            profile_summary = self._summarize_profile(master_profile)
            interaction_summary = self._summarize_interactions(recent_interactions)
            
            # Get AI insights
            prompt_data = self.prompt_manager.get_prompt(
                'master_model',
                'generate_weekly_insights',
                variables={
                    'master_profile': profile_summary,
                    'interactions': interaction_summary,
                    'interaction_count': len(recent_interactions)
                }
            )
            
            model_name, _ = self.router.route_request("reasoning", "high")
            analysis = self.router.call_model(
                model_name,
                prompt_data['prompt']
            )
            
            # Parse insights
            insights = self._parse_insights(analysis)
            
            self.scribe.log_action(
                "Weekly insights generated",
                reasoning=f"Analyzed {len(recent_interactions)} interactions",
                outcome=f"Generated {len(insights.get('key_insights', []))} insights"
            )
            
            return insights
            
        except Exception as e:
            self.scribe.log_action(
                "Weekly insights generation failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict_next_preferences(self, master_profile: Dict[str, Any],
                                interaction_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict master's next preferences and likely needs.
        
        Args:
            master_profile: Current master profile
            interaction_history: Full interaction history
            
        Returns:
            Predictions about future preferences
        """
        try:
            profile_summary = self._summarize_profile(master_profile)
            
            prompt_data = self.prompt_manager.get_prompt(
                'master_model',
                'predict_next_preferences',
                variables={
                    'master_profile': profile_summary,
                    'recent_patterns': self._get_recent_patterns(interaction_history),
                    'interaction_count': len(interaction_history)
                }
            )
            
            model_name, _ = self.router.route_request("reasoning", "high")
            analysis = self.router.call_model(
                model_name,
                prompt_data['prompt']
            )
            
            # Parse predictions
            predictions = self._parse_predictions(analysis)
            
            return predictions
            
        except Exception as e:
            self.scribe.log_action(
                "Preference prediction failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return {}
    
    def analyze_trait_evolution(self, trait_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze how master traits have evolved over time.
        
        Args:
            trait_history: Historical trait records
            
        Returns:
            Analysis of trait evolution
        """
        try:
            if not trait_history:
                return {'evolution_score': 0, 'changes': []}
            
            prompt_data = self.prompt_manager.get_prompt(
                'master_model',
                'analyze_trait_evolution',
                variables={
                    'trait_history': json.dumps(trait_history[-100:]),  # Last 100
                    'time_period': 'weekly',
                    'history_length': len(trait_history)
                }
            )
            
            model_name, _ = self.router.route_request("reasoning", "medium")
            analysis = self.router.call_model(
                model_name,
                prompt_data['prompt']
            )
            
            # Parse evolution analysis
            evolution = self._parse_evolution(analysis)
            
            return evolution
            
        except Exception as e:
            self.scribe.log_action(
                "Trait evolution analysis failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return {}
    
    def generate_strategic_recommendations(self, master_profile: Dict[str, Any],
                                          insights: Dict[str, Any]) -> List[str]:
        """
        Generate strategic recommendations based on master profile and insights.
        
        Args:
            master_profile: Master psychological profile
            insights: Generated insights
            
        Returns:
            List of strategic recommendations
        """
        try:
            profile_summary = self._summarize_profile(master_profile)
            insights_summary = json.dumps(insights.get('key_insights', []))
            
            prompt_data = self.prompt_manager.get_prompt(
                'master_model',
                'generate_strategic_recommendations',
                variables={
                    'master_profile': profile_summary,
                    'insights': insights_summary,
                    'focus_areas': json.dumps(insights.get('focus_areas', []))
                }
            )
            
            model_name, _ = self.router.route_request("reasoning", "high")
            analysis = self.router.call_model(
                model_name,
                prompt_data['prompt']
            )
            
            # Parse recommendations
            recommendations = self._parse_recommendations(analysis)
            
            return recommendations
            
        except Exception as e:
            self.scribe.log_action(
                "Strategic recommendations generation failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return []
    
    def identify_growth_areas(self, master_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify areas where the master could grow or improve.
        
        Args:
            master_profile: Master psychological profile
            
        Returns:
            List of growth opportunities
        """
        try:
            profile_summary = self._summarize_profile(master_profile)
            
            prompt_data = self.prompt_manager.get_prompt(
                'master_model',
                'identify_growth_areas',
                variables={
                    'master_profile': profile_summary,
                    'focus_on': 'decision_making, capability_development, goal_achievement'
                }
            )
            
            model_name, _ = self.router.route_request("reasoning", "high")
            analysis = self.router.call_model(
                model_name,
                prompt_data['prompt']
            )
            
            # Parse growth areas
            growth_areas = self._parse_growth_areas(analysis)
            
            return growth_areas
            
        except Exception as e:
            self.scribe.log_action(
                "Growth area identification failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return []
    
    # Helper methods
    
    def _summarize_profile(self, profile: Dict[str, Any]) -> str:
        """Summarize master profile into readable text"""
        summary_parts = []
        
        for category, traits in profile.items():
            if traits:
                category_name = category.replace('_', ' ').title()
                summary_parts.append(f"\n{category_name}:")
                
                for trait in traits:
                    name = trait.get('name', 'Unknown')
                    value = trait.get('value', '')
                    confidence = trait.get('confidence', 0)
                    conf_pct = f"{confidence*100:.0f}%"
                    summary_parts.append(f"  - {name}: {value} ({conf_pct} confident)")
        
        return "\n".join(summary_parts)
    
    def _summarize_interactions(self, interactions: List[Dict[str, Any]]) -> str:
        """Summarize recent interactions"""
        summary_parts = []
        
        for i in interactions[-20:]:  # Last 20
            intent = i.get('intent', 'unknown')
            success = "✓" if i.get('success') else "✗"
            input_snippet = i.get('input', '')[:40]
            summary_parts.append(f"{success} {intent}: {input_snippet}")
        
        return "\n".join(summary_parts)
    
    def _get_recent_patterns(self, interactions: List[Dict[str, Any]]) -> str:
        """Extract recent patterns from interactions"""
        patterns = []
        
        if not interactions:
            return ""
        
        # Count intent types
        intent_counts = {}
        for i in interactions[-20:]:
            intent = i.get('intent', 'other')
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
            patterns.append(f"{intent}: {count} times")
        
        return ", ".join(patterns)
    
    def _parse_insights(self, analysis: str) -> Dict[str, Any]:
        """Parse weekly insights from AI"""
        try:
            result = json.loads(analysis)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        return {
            'key_insights': [],
            'focus_areas': [],
            'observations': analysis[:200]
        }
    
    def _parse_predictions(self, analysis: str) -> Dict[str, Any]:
        """Parse preference predictions"""
        try:
            result = json.loads(analysis)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        return {
            'predictions': [],
            'confidence_level': 'low'
        }
    
    def _parse_evolution(self, analysis: str) -> Dict[str, Any]:
        """Parse trait evolution analysis"""
        try:
            result = json.loads(analysis)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        return {
            'evolution_score': 0,
            'changes': []
        }
    
    def _parse_recommendations(self, analysis: str) -> List[str]:
        """Parse strategic recommendations"""
        try:
            result = json.loads(analysis)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
        
        # Fallback: split by lines
        lines = analysis.split('\n')
        return [line.strip() for line in lines if line.strip() and line.startswith('-')]
    
    def _parse_growth_areas(self, analysis: str) -> List[Dict[str, Any]]:
        """Parse growth areas"""
        try:
            result = json.loads(analysis)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
        
        return []
