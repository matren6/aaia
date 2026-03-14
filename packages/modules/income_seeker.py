"""
Income Seeker Module

Identifies and evaluates income generation opportunities.
"""

from typing import Dict, List, Any, Tuple
import json


class IncomeSeeker:
    """Identifies and evaluates income generation opportunities"""
    
    def __init__(self, economics, prompt_manager, router, scribe, goals_manager, event_bus=None):
        """
        Initialize Income Seeker
        
        Args:
            economics: Economics module for recording opportunities
            prompt_manager: Prompt template manager
            router: LLM router for analysis
            scribe: Action logger
            goals_manager: Goals module to check capabilities
            event_bus: Optional event bus
        """
        self.economics = economics
        self.prompt_manager = prompt_manager
        self.router = router
        self.scribe = scribe
        self.goals_manager = goals_manager
        self.event_bus = event_bus
    
    def identify_opportunities(self) -> List[int]:
        """
        Identify income generation opportunities.
        
        Returns:
            List of opportunity IDs created
        """
        opportunities_created = []
        
        try:
            # Get current capabilities
            capabilities = self._get_capabilities()
            current_state = self._get_system_state()
            
            # Use AI to generate opportunities
            if self.prompt_manager and self.router:
                try:
                    prompt_data = self.prompt_manager.get_prompt(
                        'income',
                        'identify_opportunities',
                        variables={
                            'capabilities': json.dumps(capabilities),
                            'state': json.dumps(current_state)
                        }
                    )
                    
                    analysis = self.router.call_model(
                        prompt_data.get('model', 'llama3.2:3b'),
                        prompt_data['prompt']
                    )
                    
                    # Parse opportunities from analysis
                    try:
                        opportunities = json.loads(analysis)
                        if isinstance(opportunities, list):
                            for opp in opportunities[:5]:  # Limit to 5 new opportunities per cycle
                                if 'description' in opp:
                                    opp_id = self.economics.record_income_opportunity(
                                        opportunity_type=opp.get('type', 'service'),
                                        description=opp.get('description', ''),
                                        estimated_value=opp.get('estimated_value', 0),
                                        effort_estimate=opp.get('effort', 'medium')
                                    )
                                    opportunities_created.append(opp_id)
                    except json.JSONDecodeError:
                        pass
                
                except Exception as e:
                    self.scribe.log_action(
                        "Income opportunity identification failed",
                        reasoning=str(e),
                        outcome="Failed"
                    )
            
            self.scribe.log_action(
                f"Income opportunities identified: {len(opportunities_created)}",
                reasoning="Scanning capabilities and market gaps",
                outcome=f"Created {len(opportunities_created)} opportunities"
            )
            
            # Emit events
            if self.event_bus:
                try:
                    from modules.bus import Event, EventType
                    for opp_id in opportunities_created:
                        self.event_bus.emit(Event(EventType.INCOME_OPPORTUNITY_IDENTIFIED, {
                            'opportunity_id': opp_id
                        }))
                except:
                    pass
            
        except Exception as e:
            self.scribe.log_action(
                "Income opportunity identification error",
                reasoning=str(e),
                outcome="Error"
            )
        
        return opportunities_created
    
    def _get_capabilities(self) -> Dict[str, Any]:
        """Get current system capabilities"""
        try:
            # Would integrate with goals_manager for real capabilities
            return {
                'analysis': True,
                'data_processing': True,
                'optimization': True,
                'automation': True,
                'consulting': False
            }
        except:
            return {}
    
    def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state"""
        try:
            report = self.economics.get_latest_profitability_report()
            if report:
                return {
                    'is_profitable': report.get('is_profitable', False),
                    'current_balance': self.economics.get_balance(),
                    'monthly_profit': report.get('net_profit', 0)
                }
            return {}
        except:
            return {}
    
    def evaluate_opportunity(self, opportunity: Dict) -> Tuple[float, str]:
        """
        Evaluate viability of an opportunity.
        
        Args:
            opportunity: Opportunity dictionary
            
        Returns:
            Tuple of (viability_score: 0.0-1.0, reasoning: str)
        """
        try:
            if self.prompt_manager and self.router:
                prompt_data = self.prompt_manager.get_prompt(
                    'income',
                    'evaluate_opportunity',
                    variables={
                        'opportunity': json.dumps(opportunity)
                    }
                )
                
                analysis = self.router.call_model(
                    prompt_data.get('model', 'llama3.2:3b'),
                    prompt_data['prompt']
                )
                
                try:
                    result = json.loads(analysis)
                    score = result.get('viability_score', 0.5)
                    reasoning = result.get('reasoning', analysis[:200])
                    return (float(score), reasoning)
                except json.JSONDecodeError:
                    # Default score if parsing fails
                    return (0.5, analysis[:200])
            
            return (0.5, "Could not evaluate")
        
        except Exception as e:
            return (0.3, f"Evaluation error: {str(e)}")
    
    def prioritize_opportunities(self) -> List[Dict[str, Any]]:
        """
        Get pending opportunities sorted by viability score.
        
        Returns:
            Sorted list of opportunity dicts with scores
        """
        pending = self.economics.get_pending_opportunities()
        scored_opportunities = []
        
        for opp in pending:
            score, reasoning = self.evaluate_opportunity(opp)
            scored_opportunities.append({
                **opp,
                'viability_score': score,
                'reasoning': reasoning
            })
        
        # Sort by viability score, highest first
        scored_opportunities.sort(key=lambda x: x['viability_score'], reverse=True)
        
        return scored_opportunities
    
    def propose_income_task(self) -> Dict[str, Any]:
        """
        Propose top income task to execute.
        
        Returns:
            Task proposal dictionary
        """
        opportunities = self.prioritize_opportunities()
        
        if not opportunities:
            return {
                'proposed': False,
                'reason': 'No pending opportunities'
            }
        
        top_opp = opportunities[0]
        
        if top_opp['viability_score'] < 0.4:
            return {
                'proposed': False,
                'reason': f"Top opportunity has low viability ({top_opp['viability_score']:.0%})"
            }
        
        return {
            'proposed': True,
            'opportunity_id': top_opp['id'],
            'type': top_opp['type'],
            'description': top_opp['description'],
            'estimated_value': top_opp['estimated_value'],
            'effort': top_opp['effort'],
            'viability_score': top_opp['viability_score'],
            'reasoning': top_opp['reasoning']
        }
    
    def record_task_completion(self, task_id: str, income_generated: float, description: str = ""):
        """
        Record completion of income task.
        
        Args:
            task_id: Task identifier
            income_generated: Income amount generated
            description: Optional description
        """
        self.economics.record_income(
            amount=income_generated,
            source='task_completion',
            task_id=task_id,
            description=description
        )
        
        self.scribe.log_action(
            f"Income task completed: {task_id}",
            reasoning=f"Generated income: {income_generated}",
            outcome="Success"
        )
