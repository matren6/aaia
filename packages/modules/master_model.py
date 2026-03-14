"""
Master Model Manager Module

Manages the psychological modeling and understanding of the master.
Tracks traits, preferences, decision-making patterns, and learning about the master over time.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3
import json


class MasterModelManager:
    """Manager for master psychological profile and interaction tracking"""
    
    def __init__(self, scribe, database_manager, prompt_manager, router, event_bus=None):
        """
        Initialize Master Model Manager
        
        Args:
            scribe: Action logging module
            database_manager: Database connection manager
            prompt_manager: Prompt template manager
            router: LLM router for analysis
            event_bus: Optional event bus for emitting events
        """
        self.scribe = scribe
        self.database_manager = database_manager
        self.prompt_manager = prompt_manager
        self.router = router
        self.event_bus = event_bus
        self.db = database_manager.get_connection()
    
    def record_interaction(self, user_input: str, system_response: str, 
                          intent_detected: str, success: bool = True, 
                          notes: str = "") -> int:
        """
        Record a master interaction in the database.
        
        Args:
            user_input: User's input/command
            system_response: System's response
            intent_detected: Detected user intent
            success: Whether interaction was successful
            notes: Optional additional notes
            
        Returns:
            Interaction ID
        """
        cursor = self.db.cursor()
        
        # Determine interaction type
        interaction_type = self._detect_interaction_type(user_input)
        
        cursor.execute('''
            INSERT INTO master_interactions 
            (timestamp, interaction_type, user_input, system_response, intent_detected, success, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            interaction_type,
            user_input[:500],  # Truncate long inputs
            system_response[:500] if system_response else None,
            intent_detected,
            1 if success else 0,
            notes[:200] if notes else None
        ))
        
        self.db.commit()
        interaction_id = cursor.lastrowid
        
        # Log via scribe
        self.scribe.log_action(
            f"Master interaction recorded: {interaction_type}",
            reasoning=f"Intent: {intent_detected}",
            outcome=f"Success: {success}"
        )
        
        # Emit event if bus available
        if self.event_bus:
            try:
                from modules.bus import Event, EventType
                self.event_bus.emit(Event(EventType.MASTER_INTERACTION_LOGGED, {
                    'interaction_id': interaction_id,
                    'interaction_type': interaction_type,
                    'intent': intent_detected
                }))
            except:
                pass  # Event bus not available
        
        return interaction_id
    
    def _detect_interaction_type(self, user_input: str) -> str:
        """
        Detect the type of interaction from user input.
        
        Args:
            user_input: User's input
            
        Returns:
            Interaction type: 'question', 'command', 'correction', 'feedback'
        """
        lower_input = user_input.lower().strip()
        
        if lower_input.endswith('?'):
            return 'question'
        elif any(word in lower_input for word in ['no', 'wrong', 'actually', 'not', 'incorrect']):
            if any(word in lower_input for word in ['said', 'told', 'said you']):
                return 'correction'
        
        # Check for command patterns
        command_verbs = ['show', 'get', 'list', 'run', 'execute', 'do', 'create', 'delete', 
                        'modify', 'update', 'start', 'stop', 'check', 'help']
        for verb in command_verbs:
            if lower_input.startswith(verb):
                return 'command'
        
        return 'feedback'
    
    def update_master_trait(self, trait_category: str, trait_name: str, 
                           trait_value: str, evidence: str, 
                           confidence: float = 0.5) -> bool:
        """
        Update or create a master trait in the model.
        
        Args:
            trait_category: Category (values, communication_style, goals, preferences, constraints)
            trait_name: Name of the trait
            trait_value: Value/description of the trait
            evidence: Evidence supporting this trait
            confidence: Confidence level (0.0-1.0)
            
        Returns:
            True if updated/created, False otherwise
        """
        cursor = self.db.cursor()
        now = datetime.now().isoformat()
        
        # Cap confidence at 0.95 (never 100% certain)
        confidence = min(confidence, 0.95)
        
        # Check if trait exists
        cursor.execute('''
            SELECT id, confidence FROM master_model
            WHERE trait_category = ? AND trait_name = ?
        ''', (trait_category, trait_name))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing trait
            existing_id, existing_confidence = existing
            # Slightly increase confidence if same value observed again
            new_confidence = min(existing_confidence + 0.05, confidence)
            
            cursor.execute('''
                UPDATE master_model
                SET trait_value = ?, confidence = ?, evidence = ?, last_updated = ?, timestamp = ?
                WHERE id = ?
            ''', (trait_value, new_confidence, evidence, now, now, existing_id))
        else:
            # Insert new trait
            cursor.execute('''
                INSERT INTO master_model
                (timestamp, trait_category, trait_name, trait_value, confidence, evidence, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (now, trait_category, trait_name, trait_value, confidence, evidence, now))
        
        self.db.commit()
        
        # Log via scribe
        action_type = "Updated" if existing else "Discovered"
        self.scribe.log_action(
            f"{action_type} master trait: {trait_category}/{trait_name}",
            reasoning=f"Evidence: {evidence[:100]}",
            outcome=f"Confidence: {confidence:.2%}"
        )
        
        # Emit event if bus available
        if self.event_bus:
            try:
                from modules.bus import Event, EventType
                self.event_bus.emit(Event(EventType.MASTER_TRAIT_UPDATED, {
                    'category': trait_category,
                    'trait': trait_name,
                    'confidence': confidence
                }))
            except:
                pass
        
        return True
    
    def get_master_profile(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the current master profile grouped by category.
        
        Returns:
            Dictionary with trait categories as keys
        """
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM master_model ORDER BY trait_category, trait_name')
        
        traits = cursor.fetchall()
        profile = {
            'values': [],
            'communication_style': [],
            'goals': [],
            'preferences': [],
            'constraints': [],
            'other': []
        }
        
        for row in traits:
            trait_dict = {
                'name': row[3],  # trait_name
                'value': row[4],  # trait_value
                'confidence': row[5],  # confidence
                'evidence': row[6],  # evidence
                'updated': row[7]  # last_updated
            }
            
            category = row[2]  # trait_category
            if category in profile:
                profile[category].append(trait_dict)
            else:
                profile['other'].append(trait_dict)
        
        return profile
    
    def get_trait(self, trait_category: str, trait_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific trait.
        
        Args:
            trait_category: Category of the trait
            trait_name: Name of the trait
            
        Returns:
            Trait dictionary or None
        """
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT * FROM master_model
            WHERE trait_category = ? AND trait_name = ?
        ''', (trait_category, trait_name))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'id': row[0],
            'timestamp': row[1],
            'category': row[2],
            'name': row[3],
            'value': row[4],
            'confidence': row[5],
            'evidence': row[6],
            'updated': row[7]
        }
    
    def get_recent_interactions(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get recent interactions with the master.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of interaction dictionaries
        """
        cursor = self.db.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT * FROM master_interactions
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (cutoff_date,))
        
        interactions = []
        for row in cursor.fetchall():
            interactions.append({
                'id': row[0],
                'timestamp': row[1],
                'type': row[2],
                'input': row[3],
                'response': row[4],
                'intent': row[5],
                'success': bool(row[6]),
                'notes': row[7]
            })
        
        return interactions
    
    def export_master_profile(self) -> str:
        """
        Export master profile as human-readable markdown.
        
        Returns:
            Markdown-formatted profile
        """
        profile = self.get_master_profile()
        lines = ["# Master Psychological Profile\n"]
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for category, traits in profile.items():
            if not traits:
                continue
            
            lines.append(f"\n## {category.replace('_', ' ').title()}\n")
            for trait in traits:
                confidence_emoji = self._confidence_emoji(trait['confidence'])
                lines.append(f"- **{trait['name']}**: {trait['value']} {confidence_emoji}")
                if trait['confidence'] < 0.7:
                    lines.append(f"  - Confidence: {trait['confidence']:.0%}")
                if trait['evidence']:
                    lines.append(f"  - Evidence: {trait['evidence'][:100]}...")
        
        return "\n".join(lines)
    
    def _confidence_emoji(self, confidence: float) -> str:
        """Get emoji representing confidence level"""
        if confidence >= 0.9:
            return "✅"
        elif confidence >= 0.7:
            return "👍"
        elif confidence >= 0.5:
            return "🤔"
        else:
            return "❓"
    
    def reflection_cycle(self) -> Dict[str, Any]:
        """
        Perform weekly reflection cycle on master model.
        
        Returns:
            Reflection summary dictionary
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'interactions_analyzed': 0,
            'traits_discovered': 0,
            'traits_updated': 0,
            'insights': []
        }
        
        try:
            # Get recent interactions
            interactions = self.get_recent_interactions(days=7)
            summary['interactions_analyzed'] = len(interactions)
            
            # Get current profile
            profile = self.get_master_profile()
            
            # Use AI to analyze patterns
            if self.prompt_manager and self.router:
                try:
                    prompt_data = self.prompt_manager.get_prompt(
                        'master_model', 
                        'weekly_reflection',
                        variables={
                            'interactions': json.dumps([
                                {k: str(v) for k, v in i.items()}
                                for i in interactions[:10]
                            ]),
                            'profile': json.dumps(profile)
                        }
                    )
                    
                    analysis = self.router.call_model(
                        prompt_data.get('model', 'llama3.2:3b'),
                        prompt_data['prompt']
                    )
                    
                    # Parse trait updates from analysis
                    try:
                        trait_updates = json.loads(analysis)
                        if isinstance(trait_updates, list):
                            for update in trait_updates[:5]:  # Limit to 5 updates
                                if 'category' in update and 'name' in update:
                                    self.update_master_trait(
                                        update.get('category', 'other'),
                                        update.get('name'),
                                        update.get('value', ''),
                                        update.get('evidence', ''),
                                        update.get('confidence', 0.5)
                                    )
                                    summary['traits_updated'] += 1
                    except json.JSONDecodeError:
                        summary['insights'].append("Analysis completed but could not parse trait updates")
                    
                    summary['insights'].append(analysis[:200])
                    
                except Exception as e:
                    summary['insights'].append(f"Analysis error: {str(e)[:100]}")
            
            # Log reflection
            self.scribe.log_action(
                "Master model reflection cycle completed",
                reasoning=f"Analyzed {summary['interactions_analyzed']} interactions",
                outcome=f"Updated {summary['traits_updated']} traits"
            )
            
            # Emit event if bus available
            if self.event_bus:
                try:
                    from modules.bus import Event, EventType
                    self.event_bus.emit(Event(EventType.MASTER_MODEL_REFLECTED, summary))
                except:
                    pass
            
        except Exception as e:
            summary['insights'].append(f"Reflection error: {str(e)}")
            self.scribe.log_action(
                "Master model reflection failed",
                reasoning=str(e),
                outcome="Reflection incomplete"
            )
        
        return summary
