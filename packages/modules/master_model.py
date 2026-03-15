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

    def enhanced_reflection_cycle(self) -> Dict[str, Any]:
        """
        Phase 3: Enhanced weekly reflection with advice effectiveness analysis.

        Analyzes the effectiveness of our advice to the master, tracks outcomes,
        and uses this data to improve the master psychological model.

        Returns:
            Dict with keys:
            - period_start, period_end: Date range analyzed
            - dialogues_analyzed: Count of dialogues with advice
            - advice_effectiveness: Dict with metrics
            - model_updates: Number of traits updated
            - insights: List of key insights
            - confidence_score: Overall model confidence (0-1)
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

        reflection_data = {
            'period_start': start_time.isoformat(),
            'period_end': end_time.isoformat(),
            'dialogues_analyzed': 0,
            'advice_effectiveness': {},
            'model_updates': 0,
            'insights': [],
            'confidence_score': 0.0
        }

        try:
            # Get dialogues with outcomes in the period
            dialogues_with_outcomes = self._get_dialogues_with_outcomes(start_time, end_time)
            reflection_data['dialogues_analyzed'] = len(dialogues_with_outcomes)

            # Analyze advice effectiveness
            effectiveness = self._analyze_advice_effectiveness(dialogues_with_outcomes)
            reflection_data['advice_effectiveness'] = effectiveness

            # Update psychological model based on effectiveness
            model_updates = self._update_psychological_model(effectiveness)
            reflection_data['model_updates'] = model_updates

            # Generate insights from effectiveness analysis
            insights = self._generate_model_insights(effectiveness)
            reflection_data['insights'] = insights

            # Calculate overall model confidence
            confidence = self._calculate_model_confidence()
            reflection_data['confidence_score'] = confidence

            # Store reflection results
            self._store_reflection_cycle(reflection_data)

            # Log completion
            self.scribe.log_system_event("ENHANCED_REFLECTION_COMPLETED", {
                'dialogues': len(dialogues_with_outcomes),
                'advice_effectiveness': effectiveness.get('effectiveness_rate', 0),
                'model_confidence': confidence
            })

        except Exception as e:
            reflection_data['insights'].append(f"Reflection error: {str(e)}")
            self.scribe.log_system_event("ENHANCED_REFLECTION_ERROR", {'error': str(e)})

        return reflection_data

    def _get_dialogues_with_outcomes(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """
        Get interactions where advice was given and outcomes are available.

        Args:
            start_time: Beginning of period
            end_time: End of period

        Returns:
            List of dialogue records with outcomes
        """
        try:
            cursor = self.db.cursor()

            cursor.execute('''
                SELECT id, timestamp, interaction_type, user_input, system_response, 
                       intent_detected, success, notes
                FROM master_interactions
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp DESC
            ''', (start_time.isoformat(), end_time.isoformat()))

            dialogues = []
            for row in cursor.fetchall():
                dialogue = {
                    'id': row[0],
                    'timestamp': row[1],
                    'type': row[2],
                    'input': row[3],
                    'response': row[4],
                    'intent': row[5],
                    'success': bool(row[6]),
                    'notes': row[7]
                }

                # Check if this was advice-giving interaction
                if self._is_advice_interaction(dialogue):
                    dialogue['advice'] = self._extract_advice(dialogue['response'])

                    # Get follow-up interactions
                    follow_ups = self._get_follow_up_interactions(row[0], end_time)
                    dialogue['follow_ups'] = follow_ups

                    dialogues.append(dialogue)

            return dialogues

        except Exception as e:
            self.scribe.log_system_event("DIALOGUE_RETRIEVAL_ERROR", {'error': str(e)})
            return []

    def _is_advice_interaction(self, dialogue: Dict) -> bool:
        """
        Determine if interaction included advice-giving.

        Args:
            dialogue: Interaction record

        Returns:
            True if advice was given
        """
        response = (dialogue.get('response') or '').lower()
        advice_keywords = [
            'suggest', 'recommend', 'should', 'could', 'consider',
            'try', 'attempt', 'might', 'may help', 'would be',
            'i think', 'in my view', 'my recommendation'
        ]

        return any(keyword in response for keyword in advice_keywords)

    def _extract_advice(self, response: str) -> str:
        """Extract the advice portion from a response."""
        if not response:
            return ""

        # Simple extraction: take first 200 chars or up to first period
        period_pos = response.find('.')
        if period_pos > 0 and period_pos < 200:
            return response[:period_pos + 1]
        return response[:200]

    def _get_follow_up_interactions(self, dialogue_id: int, end_time: datetime) -> List[Dict]:
        """
        Get interactions after a given dialogue (follow-ups).

        Args:
            dialogue_id: ID of original dialogue
            end_time: End of analysis period

        Returns:
            List of follow-up interactions
        """
        try:
            cursor = self.db.cursor()

            # Get timestamp of original dialogue
            cursor.execute('SELECT timestamp FROM master_interactions WHERE id = ?', (dialogue_id,))
            original = cursor.fetchone()
            if not original:
                return []

            original_time = original[0]

            # Get interactions within next 24 hours
            follow_up_limit = (datetime.fromisoformat(original_time) + timedelta(hours=24)).isoformat()

            cursor.execute('''
                SELECT id, timestamp, interaction_type, user_input, system_response, 
                       intent_detected, success, notes
                FROM master_interactions
                WHERE timestamp > ? AND timestamp <= ? AND timestamp <= ?
                ORDER BY timestamp ASC
                LIMIT 3
            ''', (original_time, follow_up_limit, end_time.isoformat()))

            follow_ups = []
            for row in cursor.fetchall():
                follow_ups.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'type': row[2],
                    'input': row[3],
                    'response': row[4],
                    'success': bool(row[6])
                })

            return follow_ups

        except Exception:
            return []

    def _analyze_advice_effectiveness(self, dialogues: List[Dict]) -> Dict:
        """
        Analyze how effective our advice was.

        Args:
            dialogues: List of dialogues with advice

        Returns:
            Dict with effectiveness metrics
        """
        effectiveness_data = {
            'total_advice_given': 0,
            'advice_followed': 0,
            'positive_outcomes': 0,
            'negative_outcomes': 0,
            'neutral_outcomes': 0,
            'effectiveness_rate': 0.0,
            'success_rate': 0.0,
            'improvement_areas': []
        }

        for dialogue in dialogues:
            if not dialogue.get('advice'):
                continue

            effectiveness_data['total_advice_given'] += 1

            # Check if follow-ups exist
            follow_ups = dialogue.get('follow_ups', [])
            if not follow_ups:
                continue

            # Was advice followed (indicated by follow-up success)?
            was_followed = any(fu['success'] for fu in follow_ups)
            if was_followed:
                effectiveness_data['advice_followed'] += 1

                # Analyze outcome
                outcome = self._analyze_outcome(dialogue, follow_ups)

                if outcome == 'positive':
                    effectiveness_data['positive_outcomes'] += 1
                elif outcome == 'negative':
                    effectiveness_data['negative_outcomes'] += 1
                    effectiveness_data['improvement_areas'].append({
                        'advice': dialogue['advice'][:100],
                        'issue': 'Advice did not lead to positive outcome',
                        'follow_ups': len(follow_ups)
                    })
                else:
                    effectiveness_data['neutral_outcomes'] += 1

        # Calculate rates
        if effectiveness_data['total_advice_given'] > 0:
            effectiveness_data['effectiveness_rate'] = (
                effectiveness_data['advice_followed'] / 
                effectiveness_data['total_advice_given']
            )

        if effectiveness_data['advice_followed'] > 0:
            positive = effectiveness_data['positive_outcomes']
            success_count = positive + (effectiveness_data['neutral_outcomes'] / 2)
            effectiveness_data['success_rate'] = success_count / effectiveness_data['advice_followed']

        return effectiveness_data

    def _analyze_outcome(self, dialogue: Dict, follow_ups: List[Dict]) -> str:
        """
        Analyze if advice led to positive, negative, or neutral outcome.

        Args:
            dialogue: Original advice dialogue
            follow_ups: Follow-up interactions

        Returns:
            'positive', 'negative', or 'neutral'
        """
        if not follow_ups:
            return 'neutral'

        # Success rate among follow-ups
        successful = sum(1 for fu in follow_ups if fu['success'])
        success_rate = successful / len(follow_ups)

        # If master took action and it succeeded, positive
        if success_rate > 0.6:
            return 'positive'
        # If master took action but it failed, negative
        elif success_rate < 0.3:
            return 'negative'
        # Otherwise neutral
        else:
            return 'neutral'

    def _update_psychological_model(self, effectiveness: Dict) -> int:
        """
        Update master psychological model based on advice effectiveness.

        Args:
            effectiveness: Dict with effectiveness metrics

        Returns:
            Number of traits updated
        """
        updates = 0

        try:
            # Update decision-making patterns
            if effectiveness['effectiveness_rate'] > 0.7:
                self.update_master_trait(
                    'traits',
                    'decision_confidence',
                    'high',
                    f"Master follows AI advice at {effectiveness['effectiveness_rate']:.0%} rate",
                    effectiveness['effectiveness_rate']
                )
                updates += 1

            # Track advice receptiveness
            receptiveness = effectiveness['advice_followed'] / max(effectiveness['total_advice_given'], 1)
            if receptiveness > 0:
                self.update_master_trait(
                    'traits',
                    'advice_receptiveness',
                    'good' if receptiveness > 0.5 else 'moderate',
                    f"Master follows {receptiveness:.0%} of given advice",
                    receptiveness
                )
                updates += 1

            # Success pattern
            if effectiveness['success_rate'] > 0.6:
                self.update_master_trait(
                    'communication_style',
                    'advice_effectiveness',
                    'high',
                    f"Advice leads to positive outcomes {effectiveness['success_rate']:.0%} of the time",
                    effectiveness['success_rate']
                )
                updates += 1

        except Exception as e:
            self.scribe.log_system_event("MODEL_UPDATE_ERROR", {'error': str(e)})

        return updates

    def _generate_model_insights(self, effectiveness: Dict) -> List[str]:
        """
        Generate insights from advice effectiveness analysis.

        Args:
            effectiveness: Dict with effectiveness metrics

        Returns:
            List of insight strings
        """
        insights = []

        try:
            # Effectiveness insights
            if effectiveness['total_advice_given'] == 0:
                insights.append("No advice given in this period.")
            else:
                insights.append(
                    f"Gave {effectiveness['total_advice_given']} pieces of advice, "
                    f"{effectiveness['advice_followed']} followed "
                    f"({effectiveness['effectiveness_rate']:.0%} rate)"
                )

            # Success rate insights
            if effectiveness['advice_followed'] > 0:
                insights.append(
                    f"Advice success rate: {effectiveness['success_rate']:.0%} "
                    f"({effectiveness['positive_outcomes']} positive, "
                    f"{effectiveness['negative_outcomes']} negative outcomes)"
                )

            # Improvement areas
            if effectiveness['improvement_areas']:
                insights.append(
                    f"Found {len(effectiveness['improvement_areas'])} areas for improvement"
                )
                for area in effectiveness['improvement_areas'][:2]:
                    insights.append(f"  - {area['issue']}")

        except Exception:
            insights.append("Could not generate detailed insights")

        return insights

    def _calculate_model_confidence(self) -> float:
        """
        Calculate overall confidence in master psychological model.

        Returns:
            Confidence score 0.0-1.0
        """
        try:
            profile = self.get_master_profile()

            # Flatten all traits
            all_traits = []
            for category_traits in profile.values():
                all_traits.extend(category_traits)

            if not all_traits:
                return 0.0

            # Average confidence of all traits
            avg_confidence = sum(t['confidence'] for t in all_traits) / len(all_traits)

            # Boost for recent interactions
            recent = self.get_recent_interactions(days=7)
            recency_boost = min(0.1, len(recent) / 100)

            final_confidence = min(1.0, avg_confidence + recency_boost)

            return final_confidence

        except Exception:
            return 0.0

    def _store_reflection_cycle(self, reflection_data: Dict) -> None:
        """
        Store reflection cycle results for historical tracking.

        Args:
            reflection_data: Reflection results dict
        """
        try:
            cursor = self.db.cursor()

            # Check if reflection_cycles table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reflection_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    dialogues_analyzed INTEGER,
                    advice_effectiveness REAL,
                    model_updates INTEGER,
                    confidence_score REAL,
                    insights TEXT
                )
            ''')

            # Insert reflection record
            cursor.execute('''
                INSERT INTO reflection_cycles
                (timestamp, period_start, period_end, dialogues_analyzed, 
                 advice_effectiveness, model_updates, confidence_score, insights)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                reflection_data['period_start'],
                reflection_data['period_end'],
                reflection_data['dialogues_analyzed'],
                reflection_data['advice_effectiveness'].get('effectiveness_rate', 0),
                reflection_data['model_updates'],
                reflection_data['confidence_score'],
                json.dumps(reflection_data['insights'][:5])  # Store top 5 insights
            ))

            self.db.commit()

        except Exception as e:
            self.scribe.log_system_event("REFLECTION_STORAGE_ERROR", {'error': str(e)})
