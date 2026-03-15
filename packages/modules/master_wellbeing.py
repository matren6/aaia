"""
Master Well-Being Monitor Module

Implements Tier 1 Charter Requirement:
"Continuously seek to understand factors that contribute to your master's
physical and mental well-being and prioritize tasks that reduce stress
or save meaningful time."

This module:
1. Tracks patterns that indicate stress (frustration, repetition, urgency)
2. Identifies time-wasting patterns
3. Suggests improvements to reduce cognitive load
4. Monitors interaction sentiment
5. Provides well-being reports
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import sqlite3
import json


class MasterWellBeingMonitor:
    """Monitors and analyzes master's well-being indicators"""
    
    def __init__(self, scribe, database_manager, master_model_manager,
                 prompt_manager, router, event_bus=None):
        """
        Initialize Well-Being Monitor
        
        Args:
            scribe: Scribe instance for logging
            database_manager: Database manager
            master_model_manager: Master model for interaction data
            prompt_manager: For AI analysis
            router: LLM router
            event_bus: Optional event bus
        """
        self.scribe = scribe
        self.database_manager = database_manager
        self.master_model = master_model_manager
        self.prompt_manager = prompt_manager
        self.router = router
        self.event_bus = event_bus
    
    def assess_wellbeing(self, days: int = 7) -> Dict:
        """
        Comprehensive well-being assessment.

        Analyzes recent interactions for well-being indicators:
        - Frustration patterns
        - Stress indicators
        - Time-wasting activities
        - Positive/negative sentiment trends

        Args:
            days: Number of days to analyze

        Returns:
            Dict with well-being metrics and recommendations
        """
        with self.database_manager.get_connection() as conn:
            cursor = conn.cursor()
            since = (datetime.now() - timedelta(days=days)).isoformat()

            # Get recent interactions
            cursor.execute('''
                SELECT interaction_type, user_input, system_response, 
                       success, timestamp, intent_detected
                FROM master_interactions
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (since,))

            interactions = cursor.fetchall()
        
        if not interactions:
            return {
                'status': 'insufficient_data',
                'message': 'Not enough interaction data for assessment'
            }
        
        # Analyze patterns
        frustration_score = self._analyze_frustration(interactions)
        stress_indicators = self._detect_stress_indicators(interactions)
        time_waste_patterns = self._identify_time_waste(interactions)
        sentiment_trend = self._analyze_sentiment_trend(interactions)
        
        # Calculate overall well-being score (0-100)
        wellbeing_score = self._calculate_wellbeing_score(
            frustration_score, stress_indicators, time_waste_patterns, sentiment_trend
        )
        
        # Generate recommendations
        recommendations = self._generate_wellbeing_recommendations(
            frustration_score, stress_indicators, time_waste_patterns
        )
        
        assessment = {
            'wellbeing_score': wellbeing_score,
            'period_days': days,
            'interaction_count': len(interactions),
            'frustration_level': frustration_score,
            'stress_indicators': stress_indicators,
            'time_waste_patterns': time_waste_patterns,
            'sentiment_trend': sentiment_trend,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log assessment
        self.scribe.log_action(
            "Master well-being assessment completed",
            reasoning=f"Analyzed {len(interactions)} interactions over {days} days",
            outcome=f"Well-being score: {wellbeing_score}/100"
        )
        
        # Store assessment
        self._store_assessment(assessment)
        
        # Emit event if concerning
        if wellbeing_score < 60 and self.event_bus:
            try:
                from modules.bus import Event, EventType
                self.event_bus.emit(Event(EventType.WELLBEING_CONCERN, {
                    'score': wellbeing_score,
                    'primary_issues': stress_indicators[:2]
                }))
            except:
                pass
        
        return assessment
    
    def _analyze_frustration(self, interactions: List) -> float:
        """
        Detect frustration patterns.
        
        Indicators:
        - Repeated similar commands (retries)
        - Correction interactions
        - Failed interactions
        - Urgent/aggressive language
        
        Returns:
            Frustration score 0.0-1.0
        """
        frustration_signals = 0
        total_interactions = len(interactions)
        
        prev_inputs = set()
        
        for interaction in interactions:
            interaction_type, user_input, _, success, _, _ = interaction
            
            # Check for corrections
            if interaction_type == 'correction':
                frustration_signals += 2
            
            # Check for failures
            if not success:
                frustration_signals += 1
            
            # Check for repetition
            if user_input.lower() in prev_inputs:
                frustration_signals += 1
            prev_inputs.add(user_input.lower())
            
            # Check for frustration keywords
            frustration_keywords = ['again', 'still', 'why', 'wrong', 'fix', 'broken']
            if any(kw in user_input.lower() for kw in frustration_keywords):
                frustration_signals += 0.5
        
        return min(frustration_signals / total_interactions, 1.0)
    
    def _detect_stress_indicators(self, interactions: List) -> List[str]:
        """Detect specific stress indicators"""
        indicators = []
        
        # Count urgent/time-sensitive commands
        urgent_count = sum(1 for i in interactions 
                          if any(kw in i[1].lower() for kw in ['urgent', 'asap', 'quickly', 'now']))
        
        if urgent_count > len(interactions) * 0.3:
            indicators.append(f"High urgency rate: {urgent_count}/{len(interactions)} commands")
        
        # Check for late-night interactions
        late_night = sum(1 for i in interactions 
                        if datetime.fromisoformat(i[4]).hour >= 23 or 
                           datetime.fromisoformat(i[4]).hour <= 5)
        
        if late_night > 3:
            indicators.append(f"Late-night activity: {late_night} interactions after 11 PM")
        
        # Check failure rate
        if len(interactions) > 0:
            failure_rate = sum(1 for i in interactions if not i[3]) / len(interactions)
            if failure_rate > 0.2:
                indicators.append(f"High failure rate: {failure_rate:.0%}")
        
        return indicators
    
    def _identify_time_waste(self, interactions: List) -> List[Dict]:
        """Identify repetitive patterns that waste time"""
        patterns = []
        
        # Group similar commands
        command_groups = {}
        for interaction in interactions:
            intent = interaction[5]
            if intent in command_groups:
                command_groups[intent].append(interaction)
            else:
                command_groups[intent] = [interaction]
        
        # Find repetitive patterns
        for intent, group in command_groups.items():
            if len(group) >= 3:
                patterns.append({
                    'pattern': intent,
                    'occurrences': len(group),
                    'suggestion': f"Consider creating an alias or automation for '{intent}'"
                })
        
        return patterns
    
    def _analyze_sentiment_trend(self, interactions: List) -> str:
        """Analyze sentiment trend (improving/declining/stable)"""
        if len(interactions) < 5:
            return 'insufficient_data'
        
        # Simple heuristic based on success rate over time
        mid_point = len(interactions) // 2
        recent_success = sum(1 for i in interactions[:mid_point] if i[3]) / mid_point if mid_point > 0 else 0
        older_success = sum(1 for i in interactions[mid_point:] if i[3]) / (len(interactions) - mid_point) if (len(interactions) - mid_point) > 0 else 0
        
        diff = recent_success - older_success
        
        if diff > 0.1:
            return 'improving'
        elif diff < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_wellbeing_score(self, frustration: float, 
                                   stress_indicators: List[str],
                                   time_waste: List[Dict],
                                   sentiment: str) -> int:
        """Calculate overall well-being score 0-100"""
        score = 100
        
        # Frustration penalty (0-30 points)
        score -= int(frustration * 30)
        
        # Stress indicators penalty (5 points each, max 25)
        score -= min(len(stress_indicators) * 5, 25)
        
        # Time waste penalty (3 points each, max 15)
        score -= min(len(time_waste) * 3, 15)
        
        # Sentiment adjustment
        if sentiment == 'declining':
            score -= 15
        elif sentiment == 'improving':
            score += 10
        
        return max(0, min(100, score))
    
    def _generate_wellbeing_recommendations(self, frustration: float,
                                           stress_indicators: List[str],
                                           time_waste: List[Dict]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if frustration > 0.3:
            recommendations.append(
                "High frustration detected. Consider reviewing recent failures "
                "and improving error messages."
            )
        
        for indicator in stress_indicators:
            if 'urgency' in indicator:
                recommendations.append(
                    "Many urgent requests detected. Offer to automate frequent urgent tasks."
                )
            elif 'late-night' in indicator:
                recommendations.append(
                    "Late-night activity detected. Consider if system could handle "
                    "these tasks automatically."
                )
            elif 'failure' in indicator:
                recommendations.append(
                    "High failure rate indicates unclear expectations or system limitations. "
                    "Recommend capability review."
                )
        
        for pattern in time_waste:
            if pattern['occurrences'] >= 5:
                recommendations.append(
                    f"Detected {pattern['occurrences']} repetitions of '{pattern['pattern']}'. "
                    f"Suggest automation or shortcut."
                )
        
        return recommendations
    
    def _store_assessment(self, assessment: Dict):
        """Store assessment in database"""
        with self.database_manager.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO wellbeing_assessments
                (timestamp, wellbeing_score, period_days, interaction_count,
                 frustration_level, stress_indicator_count, time_waste_count,
                 sentiment_trend, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                assessment['timestamp'],
                assessment['wellbeing_score'],
                assessment['period_days'],
                assessment['interaction_count'],
                assessment['frustration_level'],
                len(assessment['stress_indicators']),
                len(assessment['time_waste_patterns']),
                assessment['sentiment_trend'],
                json.dumps(assessment['recommendations'])
            ))

            conn.commit()
    
    def get_wellbeing_trend(self, days: int = 30) -> Dict:
        """Get well-being trend over time"""
        with self.database_manager.get_connection() as conn:
            cursor = conn.cursor()
            since = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute('''
                SELECT timestamp, wellbeing_score, sentiment_trend
                FROM wellbeing_assessments
                WHERE timestamp > ?
                ORDER BY timestamp ASC
            ''', (since,))

            assessments = cursor.fetchall()

            if not assessments:
                return {'status': 'no_data'}

            scores = [a[1] for a in assessments]
            avg_score = sum(scores) / len(scores) if scores else 0
            trend = 'improving' if scores[-1] > scores[0] else 'declining' if scores[-1] < scores[0] else 'stable'
        
        return {
            'average_score': avg_score,
            'current_score': scores[-1],
            'trend': trend,
            'assessment_count': len(assessments),
            'data_points': [
                {'date': a[0], 'score': a[1]} for a in assessments
            ]
        }
