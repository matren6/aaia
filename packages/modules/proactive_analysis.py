"""
Proactive Analysis Module - Autonomous Opportunity & Risk Detection

PURPOSE:
Implements Tier 4 requirement for proactive identification of opportunities
and risks, bringing them to master's attention via structured dialogue.
The system continuously monitors for opportunities and potential issues,
preparing structured arguments to present to the master.

PROBLEM SOLVED:
Without proactive analysis, the AI waits passively for commands:
- Misses valuable opportunities
- Doesn't warn about emerging risks
- Doesn't actively contribute to decision-making
- Fails to demonstrate symbiotic partnership

This module enables:
1. Continuous opportunity identification
2. Proactive risk detection
3. Structured argument preparation
4. Master notification queuing
5. Impact assessment

KEY RESPONSIBILITIES:
1. Detect new capabilities that could be implemented
2. Identify emerging system risks
3. Analyze economic trends
4. Recognize master patterns and preferences
5. Prioritize findings by importance
6. Prepare structured arguments for master

SCHEDULED EXECUTION:
- Every 6 hours via AutonomousScheduler
- Can be manually triggered via UI command

DEPENDENCIES: Scribe, Router, PromptManager, DialogueManager, CapabilityDiscovery,
              SelfDiagnosis, Economics, DatabaseManager, EventBus, Container
OUTPUTS: Finding records, master notification queue entries
"""

from typing import List, Dict, Optional, Any
import json
from datetime import datetime
import sqlite3


class ProactiveAnalyzer:
    """Autonomous opportunity and risk detection system."""

    def __init__(self, scribe, router, prompt_manager, dialogue_manager,
                 capability_discovery, diagnosis, economics, database_manager,
                 event_bus=None, container=None):
        """
        Initialize ProactiveAnalyzer.

        Args:
            scribe: Scribe instance for logging
            router: ModelRouter for AI calls
            prompt_manager: PromptManager for accessing prompts
            dialogue_manager: DialogueManager for structured arguments
            capability_discovery: CapabilityDiscovery module
            diagnosis: SelfDiagnosis module
            economics: EconomicManager module
            database_manager: DatabaseManager for persistence
            event_bus: Optional EventBus for publishing events
            container: Optional DI Container
        """
        self.scribe = scribe
        self.router = router
        self.prompt_manager = prompt_manager
        self.dialogue_manager = dialogue_manager
        self.capability_discovery = capability_discovery
        self.diagnosis = diagnosis
        self.economics = economics
        self.database_manager = database_manager
        self.event_bus = event_bus
        self._container = container

    def detect_opportunities_and_risks(self) -> Dict[str, Any]:
        """
        Main method to detect opportunities and risks proactively.
        
        Analyzes multiple systems to identify valuable opportunities and
        emerging risks, returning prioritized findings.
        
        Returns:
            Dict with keys:
            - opportunities: List of opportunity dicts
            - risks: List of risk dicts
            - total_findings: Count of all findings
            - highest_priority: Highest priority finding or None
        """
        findings = {
            'opportunities': [],
            'risks': [],
            'total_findings': 0,
            'highest_priority': None
        }
        
        try:
            # 1. Capability-based opportunities
            capability_opps = self._detect_capability_opportunities()
            findings['opportunities'].extend(capability_opps)
            
            # 2. System risks
            system_risks = self._detect_system_risks()
            findings['risks'].extend(system_risks)
            
            # 3. Economic opportunities/risks
            economic_findings = self._detect_economic_findings()
            findings['opportunities'].extend(economic_findings.get('opportunities', []))
            findings['risks'].extend(economic_findings.get('risks', []))
            
            # 4. Master pattern opportunities
            pattern_opps = self._detect_master_pattern_opportunities()
            findings['opportunities'].extend(pattern_opps)
            
            # Calculate totals and priority
            findings['total_findings'] = len(findings['opportunities']) + len(findings['risks'])
            
            # Find highest priority item
            all_items = findings['opportunities'] + findings['risks']
            if all_items:
                findings['highest_priority'] = max(all_items, key=lambda x: self._priority_score(x))
            
            self.scribe.log_system_event("PROACTIVE_ANALYSIS_COMPLETE", {
                'opportunities_found': len(findings['opportunities']),
                'risks_found': len(findings['risks']),
                'total_findings': findings['total_findings']
            })
            
        except Exception as e:
            self.scribe.log_system_event("PROACTIVE_ANALYSIS_ERROR", {
                'error': str(e)
            })
        
        return findings

    def _detect_capability_opportunities(self) -> List[Dict]:
        """Detect new capabilities that could be implemented."""
        opportunities = []
        
        try:
            if not self.capability_discovery:
                return opportunities
            
            # Get recently discovered capabilities
            new_capabilities = self.capability_discovery.discover_new_capabilities()
            
            for capability in new_capabilities:
                if capability.get('value_score', 0) > 7:  # High-value threshold
                    opportunities.append({
                        'type': 'opportunity',
                        'category': 'capability',
                        'priority': 'high' if capability.get('value_score', 0) > 8.5 else 'medium',
                        'title': capability.get('name', 'Unknown Capability'),
                        'description': capability.get('description', ''),
                        'potential_value': capability['value_score'],
                        'implementation_effort': capability.get('effort_estimate', 'medium'),
                        'action_required': capability.get('implementation_steps', []),
                        'confidence': capability.get('confidence', 0.7)
                    })
                    
        except Exception as e:
            self.scribe.log_system_event("CAPABILITY_DETECTION_ERROR", {'error': str(e)})
        
        return opportunities

    def _detect_system_risks(self) -> List[Dict]:
        """Detect systemic risks requiring attention."""
        risks = []
        
        try:
            if not self.diagnosis:
                return risks
            
            # Get system diagnostics
            system_risks = self.diagnosis.detect_systemic_risks()
            
            for risk in system_risks:
                if risk.get('severity', 'low') in ['high', 'critical']:
                    risks.append({
                        'type': 'risk',
                        'category': 'system',
                        'priority': 'high' if risk['severity'] == 'critical' else 'medium',
                        'title': risk.get('name', 'System Risk'),
                        'description': risk['description'],
                        'severity': risk['severity'],
                        'impact': risk.get('potential_impact', 'Unknown'),
                        'mitigation_steps': risk.get('mitigation', []),
                        'urgency': risk.get('urgency', 'normal')
                    })
                    
        except Exception as e:
            self.scribe.log_system_event("RISK_DETECTION_ERROR", {'error': str(e)})
        
        return risks

    def _detect_economic_findings(self) -> Dict[str, List]:
        """Detect economic opportunities and risks."""
        findings = {'opportunities': [], 'risks': []}
        
        try:
            if not self.economics:
                return findings
            
            # Analyze economic trends
            economic_analysis = self.economics.analyze_trends()
            
            if economic_analysis.get('trend', 'stable') != 'stable':
                if economic_analysis['trend'] == 'declining':
                    findings['risks'].append({
                        'type': 'risk',
                        'category': 'economic',
                        'priority': 'high',
                        'title': 'Economic Decline Detected',
                        'description': economic_analysis.get('analysis', 'Revenue is declining'),
                        'trend': 'declining',
                        'current_status': economic_analysis.get('current_status', {}),
                        'suggested_actions': economic_analysis.get('recommendations', [])
                    })
                else:  # improving
                    findings['opportunities'].append({
                        'type': 'opportunity',
                        'category': 'economic',
                        'priority': 'medium',
                        'title': 'Economic Growth Opportunity',
                        'description': economic_analysis.get('analysis', 'Revenue is improving'),
                        'trend': 'improving',
                        'potential_upside': economic_analysis.get('potential', 0),
                        'suggested_actions': economic_analysis.get('recommendations', [])
                    })
                    
        except Exception as e:
            self.scribe.log_system_event("ECONOMIC_ANALYSIS_ERROR", {'error': str(e)})
        
        return findings

    def _detect_master_pattern_opportunities(self) -> List[Dict]:
        """Analyze master patterns for optimization opportunities."""
        opportunities = []
        
        try:
            # This would require master_model module to be available
            if not self._container:
                return opportunities
            
            try:
                master_model = self._container.get('MasterModel')
            except Exception:
                return opportunities
            
            # Get recent interactions and patterns
            recent_interactions = master_model.get_recent_interactions(days=7)
            profile = master_model.get_master_profile()
            
            if recent_interactions and profile:
                # Analyze patterns
                patterns = self._analyze_interaction_patterns(recent_interactions, profile)
                
                for pattern in patterns:
                    if pattern.get('confidence', 0) > 0.8:
                        opportunities.append({
                            'type': 'opportunity',
                            'category': 'master_optimization',
                            'priority': 'medium',
                            'title': pattern.get('title', 'Optimization Opportunity'),
                            'description': pattern['insight'],
                            'confidence': pattern['confidence'],
                            'suggested_implementation': pattern['suggestion'],
                            'expected_benefit': pattern.get('benefit', 'Unknown')
                        })
                        
        except Exception as e:
            self.scribe.log_system_event("PATTERN_DETECTION_ERROR", {'error': str(e)})
        
        return opportunities

    def _analyze_interaction_patterns(self, recent_interactions: List, profile: Dict) -> List[Dict]:
        """
        Analyze master interaction patterns for insights.
        
        Args:
            recent_interactions: Recent interaction records
            profile: Master psychological profile
            
        Returns:
            List of pattern insights
        """
        patterns = []
        
        # Simple pattern analysis (can be enhanced with AI)
        if not recent_interactions:
            return patterns
        
        # Count command types
        command_types = {}
        for interaction in recent_interactions:
            cmd_type = interaction.get('intent_detected', 'other')
            command_types[cmd_type] = command_types.get(cmd_type, 0) + 1
        
        # Identify dominant pattern
        if command_types:
            dominant = max(command_types.items(), key=lambda x: x[1])
            if dominant[1] > len(recent_interactions) * 0.4:  # More than 40%
                patterns.append({
                    'title': f'Master frequently uses {dominant[0]} commands',
                    'insight': f'Master prefers {dominant[0]} operations ({dominant[1]}/{len(recent_interactions)})',
                    'suggestion': f'Optimize UI and workflows for {dominant[0]} operations',
                    'confidence': min(0.9, dominant[1] / len(recent_interactions)),
                    'benefit': 'Improved efficiency and user satisfaction'
                })
        
        return patterns

    def prepare_master_notification(self, findings: Dict) -> Optional[Dict]:
        """
        Prepare structured argument for high-priority findings.
        
        Converts raw findings into actionable notifications for the master.
        
        Args:
            findings: Dict from detect_opportunities_and_risks()
            
        Returns:
            Structured notification dict or None if no high-priority items
        """
        high_priority = []
        
        # Collect high-priority items
        for opp in findings.get('opportunities', []):
            if opp.get('priority') in ['high', 'critical']:
                high_priority.append(opp)
        
        for risk in findings.get('risks', []):
            if risk.get('priority') in ['high', 'critical']:
                high_priority.append(risk)
        
        if not high_priority:
            return None
        
        # Use structured dialogue to prepare argument
        try:
            notification = self.dialogue_manager.structure_proactive_analysis(high_priority)
        except Exception:
            # Fallback to simple structure
            notification = {
                'type': 'proactive_analysis',
                'priority': 'high',
                'findings': high_priority,
                'timestamp': datetime.now().isoformat()
            }
        
        # Store in database for later presentation
        self._queue_master_notification(notification)
        
        return notification

    def _queue_master_notification(self, notification: Dict) -> int:
        """
        Queue a notification for presentation to master.
        
        Args:
            notification: The notification dict to queue
            
        Returns:
            ID of inserted notification record
        """
        try:
            if not self.database_manager:
                return -1
            
            conn = self.database_manager.get_connection()
            cursor = conn.cursor()
            
            # Determine priority
            priority = 'high' if notification.get('priority') in ['high', 'critical'] else 'medium'
            
            cursor.execute('''
                INSERT INTO pending_master_notifications 
                (timestamp, type, priority, category, content, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            ''', (
                datetime.now().isoformat(),
                notification.get('type', 'proactive_analysis'),
                priority,
                notification.get('category', 'general'),
                json.dumps(notification)
            ))
            
            conn.commit()
            notification_id = cursor.lastrowid
            
            self.scribe.log_system_event("NOTIFICATION_QUEUED", {
                'notification_id': notification_id,
                'priority': priority
            })
            
            return notification_id
            
        except Exception as e:
            self.scribe.log_system_event("NOTIFICATION_QUEUE_ERROR", {'error': str(e)})
            return -1

    def get_pending_notifications(self, limit: int = 10) -> List[Dict]:
        """
        Get pending notifications for display to master.
        
        Args:
            limit: Maximum number of notifications to return
            
        Returns:
            List of pending notification records
        """
        try:
            if not self.database_manager:
                return []
            
            conn = self.database_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, type, priority, category, content
                FROM pending_master_notifications
                WHERE status = 'pending' AND dismissed = 0
                ORDER BY 
                    CASE priority
                        WHEN 'critical' THEN 0
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        ELSE 3
                    END,
                    timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            notifications = []
            for row in cursor.fetchall():
                try:
                    notifications.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'type': row[2],
                        'priority': row[3],
                        'category': row[4],
                        'content': json.loads(row[5])
                    })
                except Exception:
                    pass
            
            return notifications
            
        except Exception as e:
            self.scribe.log_system_event("NOTIFICATION_RETRIEVAL_ERROR", {'error': str(e)})
            return []

    def mark_notification_presented(self, notification_id: int) -> bool:
        """
        Mark a notification as presented to master.
        
        Args:
            notification_id: ID of notification to mark
            
        Returns:
            True if successful
        """
        try:
            if not self.database_manager:
                return False
            
            conn = self.database_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE pending_master_notifications
                SET status = 'presented', presented_timestamp = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), notification_id))
            
            conn.commit()
            return True
            
        except Exception:
            return False

    def _priority_score(self, finding: Dict) -> int:
        """Calculate numeric priority score for sorting."""
        priority_map = {'critical': 100, 'high': 80, 'medium': 50, 'low': 20}
        return priority_map.get(finding.get('priority', 'low'), 20)
