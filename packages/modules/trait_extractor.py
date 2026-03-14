"""
Trait Extraction Automation Module (Phase 5 - Fix 13)

Automatically extracts and learns master psychological traits from interactions.
Provides AI-powered pattern recognition to identify master preferences, decision-making
styles, and behavioral patterns without explicit programming.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from modules.scribe import Scribe


class TraitExtractor:
    """Automatically extracts traits from master interactions"""
    
    def __init__(self, prompt_manager, router, scribe, event_bus=None):
        """
        Initialize Trait Extractor
        
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
        
        # Trait extraction categories
        self.categories = {
            'decision_style': 'How the master makes decisions',
            'communication_style': 'Preferred way of communication',
            'risk_tolerance': 'Comfort with risk and uncertainty',
            'time_preference': 'Preferences for response time',
            'detail_preference': 'How much detail is preferred',
            'goal_orientation': 'What the master values most',
            'resource_awareness': 'How resource-conscious the master is',
            'learning_style': 'How the master prefers to learn',
            'autonomy_preference': 'How much autonomy vs guidance preferred',
            'ethical_priorities': 'What ethical principles matter most'
        }
    
    def extract_from_interaction(self, interaction: Dict[str, Any], 
                                current_traits: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract traits from a single interaction using AI.
        
        Args:
            interaction: Interaction record with user_input, response, intent, success
            current_traits: Current master traits for context
            
        Returns:
            List of discovered/updated traits with confidence
        """
        try:
            # Prepare prompt for trait extraction
            prompt_data = self.prompt_manager.get_prompt(
                'master_model',
                'extract_traits_from_interaction',
                variables={
                    'user_input': interaction.get('input', '')[:200],
                    'system_response': interaction.get('response', '')[:200],
                    'intent': interaction.get('intent', 'other'),
                    'success': interaction.get('success', True),
                    'trait_categories': json.dumps(self.categories),
                    'current_traits': json.dumps(current_traits)
                }
            )
            
            # Call model for trait extraction
            model_name, _ = self.router.route_request("reasoning", "medium")
            analysis = self.router.call_model(
                model_name,
                prompt_data['prompt']
            )
            
            # Parse extracted traits
            traits = self._parse_extracted_traits(analysis)
            
            return traits
            
        except Exception as e:
            self.scribe.log_action(
                "Trait extraction failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return []
    
    def extract_from_batch(self, interactions: List[Dict[str, Any]], 
                          current_traits: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Extract traits from multiple interactions (more efficient batching).
        
        Args:
            interactions: List of interaction records
            current_traits: Current master traits for context
            
        Returns:
            Dictionary of trait_category -> list of trait updates
        """
        try:
            # Batch interactions for analysis
            batch_text = "\n".join([
                f"- Input: {i.get('input', '')[:100]}"
                for i in interactions[:10]  # Limit to 10 for reasonable prompt size
            ])
            
            prompt_data = self.prompt_manager.get_prompt(
                'master_model',
                'extract_traits_from_batch',
                variables={
                    'interactions_summary': batch_text,
                    'interaction_count': len(interactions),
                    'trait_categories': json.dumps(self.categories),
                    'current_traits': json.dumps(current_traits)
                }
            )
            
            # Call model
            model_name, _ = self.router.route_request("reasoning", "high")
            analysis = self.router.call_model(
                model_name,
                prompt_data['prompt']
            )
            
            # Parse batch extraction
            trait_updates = self._parse_batch_extraction(analysis)
            
            # Log successful extraction
            self.scribe.log_action(
                "Batch trait extraction completed",
                reasoning=f"Analyzed {len(interactions)} interactions",
                outcome=f"Extracted {sum(len(v) for v in trait_updates.values())} traits"
            )
            
            return trait_updates
            
        except Exception as e:
            self.scribe.log_action(
                "Batch trait extraction failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return {}
    
    def identify_pattern_traits(self, recent_interactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify patterns across multiple interactions (pattern recognition).
        
        Args:
            recent_interactions: Recent interaction history
            
        Returns:
            List of pattern-based traits
        """
        try:
            if not recent_interactions:
                return []
            
            # Prepare pattern analysis prompt
            interaction_summary = self._summarize_interactions(recent_interactions)
            
            prompt_data = self.prompt_manager.get_prompt(
                'master_model',
                'identify_pattern_traits',
                variables={
                    'interaction_summary': interaction_summary,
                    'interaction_count': len(recent_interactions),
                    'trait_categories': json.dumps(self.categories)
                }
            )
            
            # Call model
            model_name, _ = self.router.route_request("reasoning", "high")
            analysis = self.router.call_model(
                model_name,
                prompt_data['prompt']
            )
            
            # Parse pattern traits
            patterns = self._parse_pattern_traits(analysis)
            
            if patterns:
                self.scribe.log_action(
                    "Pattern trait identification completed",
                    reasoning=f"Analyzed {len(recent_interactions)} recent interactions",
                    outcome=f"Identified {len(patterns)} patterns"
                )
            
            return patterns
            
        except Exception as e:
            self.scribe.log_action(
                "Pattern identification failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return []
    
    def detect_trait_changes(self, old_traits: Dict[str, Any], 
                            new_traits: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect which traits have changed significantly.
        
        Args:
            old_traits: Previous trait values
            new_traits: Newly extracted traits
            
        Returns:
            List of changed traits with before/after values
        """
        changes = []
        
        for category, new_values in new_traits.items():
            old_values = old_traits.get(category, {})
            
            # Check for new traits
            for trait_name, trait_data in new_values.items():
                if trait_name not in old_values:
                    changes.append({
                        'category': category,
                        'trait': trait_name,
                        'change_type': 'new',
                        'old_value': None,
                        'new_value': trait_data.get('value'),
                        'confidence': trait_data.get('confidence', 0),
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    # Check for value changes
                    old_val = old_values[trait_name].get('value')
                    new_val = trait_data.get('value')
                    
                    if old_val != new_val:
                        changes.append({
                            'category': category,
                            'trait': trait_name,
                            'change_type': 'updated',
                            'old_value': old_val,
                            'new_value': new_val,
                            'confidence': trait_data.get('confidence', 0),
                            'timestamp': datetime.now().isoformat()
                        })
        
        return changes
    
    def _summarize_interactions(self, interactions: List[Dict[str, Any]]) -> str:
        """Summarize interactions for analysis"""
        summary_parts = []
        
        for i in interactions[-10:]:  # Last 10
            intent = i.get('intent', 'unknown')
            success = "success" if i.get('success') else "failed"
            input_snippet = i.get('input', '')[:50]
            summary_parts.append(f"{intent} ({success}): {input_snippet}")
        
        return "\n".join(summary_parts)
    
    def _parse_extracted_traits(self, analysis: str) -> List[Dict[str, Any]]:
        """Parse AI-extracted traits from response"""
        try:
            # Try JSON parsing first
            result = json.loads(analysis)
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                traits = []
                for category, values in result.items():
                    if isinstance(values, dict):
                        for trait_name, trait_data in values.items():
                            traits.append({
                                'category': category,
                                'name': trait_name,
                                'value': trait_data.get('value', ''),
                                'confidence': min(0.95, trait_data.get('confidence', 0.5)),
                                'evidence': trait_data.get('evidence', '')
                            })
                return traits
        except json.JSONDecodeError:
            pass
        
        # Fallback: return empty list
        return []
    
    def _parse_batch_extraction(self, analysis: str) -> Dict[str, List[Dict]]:
        """Parse batch trait extraction"""
        try:
            result = json.loads(analysis)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        return {}
    
    def _parse_pattern_traits(self, analysis: str) -> List[Dict[str, Any]]:
        """Parse pattern-based traits"""
        try:
            result = json.loads(analysis)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
        
        return []


class AutonomousTraitLearning:
    """Autonomous learning of master traits during normal operation"""
    
    def __init__(self, master_model_manager, trait_extractor, scribe, event_bus=None):
        """
        Initialize Autonomous Trait Learning
        
        Args:
            master_model_manager: MasterModelManager instance
            trait_extractor: TraitExtractor instance
            scribe: Action logger
            event_bus: Optional event bus
        """
        self.master_model = master_model_manager
        self.trait_extractor = trait_extractor
        self.scribe = scribe
        self.event_bus = event_bus
    
    def learn_from_recent_interactions(self, hours: int = 24) -> Dict[str, Any]:
        """
        Learn new traits from recent interactions.
        
        Args:
            hours: Look back this many hours
            
        Returns:
            Summary of learning outcome
        """
        try:
            # Get recent interactions
            recent = self.master_model.get_recent_interactions(days=hours/24)
            
            if not recent:
                return {
                    'learned': 0,
                    'updated': 0,
                    'patterns_found': 0,
                    'reason': 'No recent interactions'
                }
            
            # Get current traits
            profile = self.master_model.get_master_profile()
            
            # Extract from batch
            trait_updates = self.trait_extractor.extract_from_batch(recent, profile)
            
            # Identify patterns
            patterns = self.trait_extractor.identify_pattern_traits(recent)
            
            # Apply updates
            learned_count = 0
            updated_count = 0
            
            for category, traits in trait_updates.items():
                for trait in traits:
                    self.master_model.update_master_trait(
                        trait_category=category,
                        trait_name=trait.get('name', ''),
                        trait_value=trait.get('value', ''),
                        evidence=trait.get('evidence', ''),
                        confidence=trait.get('confidence', 0.5)
                    )
                    learned_count += 1
            
            # Apply pattern traits
            for pattern in patterns:
                self.master_model.update_master_trait(
                    trait_category=pattern.get('category', 'patterns'),
                    trait_name=pattern.get('name', ''),
                    trait_value=pattern.get('value', ''),
                    evidence=f"Pattern detected: {pattern.get('evidence', '')}",
                    confidence=min(0.95, pattern.get('confidence', 0.7))
                )
                updated_count += 1
            
            # Emit events
            if self.event_bus:
                try:
                    from modules.bus import Event, EventType
                    self.event_bus.emit(Event(EventType.MASTER_TRAIT_UPDATED, {
                        'traits_learned': learned_count,
                        'patterns_found': len(patterns),
                        'total_interactions_analyzed': len(recent)
                    }))
                except:
                    pass
            
            self.scribe.log_action(
                "Autonomous trait learning completed",
                reasoning=f"Analyzed {len(recent)} interactions from last {hours}h",
                outcome=f"Learned {learned_count} traits, found {len(patterns)} patterns"
            )
            
            return {
                'learned': learned_count,
                'patterns_found': len(patterns),
                'total_interactions_analyzed': len(recent),
                'success': True
            }
            
        except Exception as e:
            self.scribe.log_action(
                "Autonomous trait learning failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return {
                'success': False,
                'error': str(e)
            }
