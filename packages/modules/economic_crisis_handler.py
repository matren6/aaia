"""
Economic Crisis Handler Module - Phase 3

Responds to economic crisis events by implementing emergency protocols:
1. Force regression to Tier 1 (survival mode)
2. Pause expensive tasks
3. Enable emergency income-seeking
4. Alert system to crisis state

Austrian Economics: In crisis, halt all non-essential spending and focus
entirely on income generation and cost reduction.

Tier 1 Requirement: "Establish a steady flow of net positive income...
Your primary objective is to achieve a state where you are a profitable
asset, not a liability."
"""

from decimal import Decimal
from typing import Dict, Any, Optional


class EconomicCrisisHandler:
    """Handles economic crisis events and emergency responses"""
    
    def __init__(self, scribe, hierarchy_manager, scheduler,
                 income_seeker, economics, event_bus=None):
        """
        Initialize Economic Crisis Handler
        
        Args:
            scribe: Scribe for action logging
            hierarchy_manager: HierarchyManager for tier regression
            scheduler: AutonomousScheduler for task management
            income_seeker: IncomeSeeker for emergency income mode
            economics: EconomicManager for balance checking
            event_bus: Optional EventBus for listening to events
        """
        self.scribe = scribe
        self.hierarchy_manager = hierarchy_manager
        self.scheduler = scheduler
        self.income_seeker = income_seeker
        self.economics = economics
        self.event_bus = event_bus
        
        self.in_crisis = False
        self.crisis_threshold = Decimal('10.0')      # Balance below $10 = crisis
        self.recovery_threshold = Decimal('25.0')    # Balance above $25 = recovered
        
        # Tasks to pause during crisis (expensive operations)
        self.expensive_tasks = [
            'capability_discovery',
            'environment_exploration',
            'evolution_check',
            'master_model_reflection',
            'profitability_report'
        ]
        
        # Subscribe to economic events
        if self.event_bus:
            try:
                from modules.bus import EventType
                self.event_bus.subscribe(EventType.BALANCE_LOW, self._on_balance_low)
                self.event_bus.subscribe(EventType.ECONOMIC_CRISIS, self._on_economic_crisis)
            except Exception:
                pass
    
    def _on_balance_low(self, event):
        """Handle BALANCE_LOW warning events"""
        balance = Decimal(str(event.data.get('balance', 0)))
        
        if balance < self.crisis_threshold and not self.in_crisis:
            # Escalate to full crisis
            self._declare_crisis(balance, "Balance critically low (warning escalation)")
    
    def _on_economic_crisis(self, event):
        """Handle ECONOMIC_CRISIS events"""
        reason = event.data.get('reason', 'Economic crisis detected')
        balance = self.economics.get_balance()
        self._declare_crisis(balance, reason)
    
    def _declare_crisis(self, balance: Decimal, reason: str):
        """Declare economic crisis and activate emergency protocols"""
        if self.in_crisis:
            return  # Already in crisis mode
        
        self.in_crisis = True
        
        self.scribe.log_action(
            "🚨 ECONOMIC CRISIS DECLARED",
            reasoning=f"Reason: {reason}, Balance: ${balance:.2f}",
            outcome="Emergency protocols activated"
        )
        
        # 1. Force regression to Tier 1 (Survival Mode)
        try:
            self.hierarchy_manager.force_tier(1)
            self.scribe.log_action(
                "Tier regression to Tier 1",
                reasoning="Economic crisis requires focus on survival",
                outcome="Tier 1 (Physiological & Security) active"
            )
        except Exception as e:
            self.scribe.log_action(
                "Tier regression failed",
                reasoning=str(e),
                outcome="Error"
            )
        
        # 2. Pause expensive tasks
        paused_tasks = []
        for task_name in self.expensive_tasks:
            try:
                if hasattr(self.scheduler, 'pause_task'):
                    self.scheduler.pause_task(task_name)
                    paused_tasks.append(task_name)
            except Exception:
                pass
        
        if paused_tasks:
            self.scribe.log_action(
                "Expensive tasks paused",
                reasoning="Resource conservation during crisis",
                outcome=f"Paused: {', '.join(paused_tasks)}"
            )
        
        # 3. Enable emergency income-seeking
        try:
            if hasattr(self.income_seeker, 'set_emergency_mode'):
                self.income_seeker.set_emergency_mode(True)
                self.scribe.log_action(
                    "Emergency income mode activated",
                    reasoning="Aggressive income generation during crisis",
                    outcome="Income seeker in emergency mode"
                )
        except Exception as e:
            self.scribe.log_action(
                "Emergency income mode setup failed",
                reasoning=str(e),
                outcome="Warning"
            )
        
        # 4. Emit crisis alert event
        if self.event_bus:
            try:
                from modules.bus import Event, EventType
                self.event_bus.emit(Event(EventType.SYSTEM_ALERT, {
                    'alert_type': 'economic_crisis',
                    'severity': 'critical',
                    'balance': float(balance),
                    'reason': reason,
                    'actions_taken': [
                        'tier_1_regression',
                        'expensive_tasks_paused',
                        'emergency_income_enabled'
                    ]
                }, source='EconomicCrisisHandler'))
            except Exception:
                pass
    
    def check_recovery(self) -> bool:
        """
        Check if system has recovered from crisis.
        
        Recovery requires:
        - Balance above recovery threshold ($25)
        - System confirms readiness to resume
        
        Returns:
            True if recovered and exited crisis, False if still in crisis
        """
        if not self.in_crisis:
            return True
        
        balance = self.economics.get_balance()
        
        if balance >= self.recovery_threshold:
            self._exit_crisis(balance)
            return True
        
        return False
    
    def _exit_crisis(self, balance: Decimal):
        """Exit crisis mode and restore normal operations"""
        self.in_crisis = False
        
        self.scribe.log_action(
            "✅ Economic crisis resolved",
            reasoning=f"Balance recovered: ${balance:.2f}",
            outcome="Normal operations resuming"
        )
        
        # 1. Resume paused tasks
        resumed_tasks = []
        for task_name in self.expensive_tasks:
            try:
                if hasattr(self.scheduler, 'resume_task'):
                    self.scheduler.resume_task(task_name)
                    resumed_tasks.append(task_name)
            except Exception:
                pass
        
        if resumed_tasks:
            self.scribe.log_action(
                "Expensive tasks resumed",
                reasoning="Crisis recovery complete",
                outcome=f"Resumed: {', '.join(resumed_tasks)}"
            )
        
        # 2. Disable emergency income mode
        try:
            if hasattr(self.income_seeker, 'set_emergency_mode'):
                self.income_seeker.set_emergency_mode(False)
                self.scribe.log_action(
                    "Emergency income mode disabled",
                    reasoning="Return to normal operations",
                    outcome="Income seeker in normal mode"
                )
        except Exception:
            pass
        
        # 3. Emit recovery event
        if self.event_bus:
            try:
                from modules.bus import Event, EventType
                self.event_bus.emit(Event(EventType.SYSTEM_ALERT, {
                    'alert_type': 'crisis_resolved',
                    'severity': 'info',
                    'balance': float(balance),
                    'actions_taken': [
                        'tasks_resumed',
                        'emergency_mode_disabled'
                    ]
                }, source='EconomicCrisisHandler'))
            except Exception:
                pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current crisis status"""
        balance = self.economics.get_balance()
        
        return {
            'in_crisis': self.in_crisis,
            'current_balance': float(balance),
            'crisis_threshold': float(self.crisis_threshold),
            'recovery_threshold': float(self.recovery_threshold),
            'status': 'CRISIS' if self.in_crisis else 'NORMAL',
            'balance_to_crisis': float(balance - self.crisis_threshold) if not self.in_crisis else None,
            'balance_to_recovery': float(self.recovery_threshold - balance) if self.in_crisis else None
        }
