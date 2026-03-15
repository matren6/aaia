"""
Profitability Reporting Module (Phase 5 - Fix 14)

Generates comprehensive profitability reports with AI-powered analysis,
alerts, and recommendations for improving economic sustainability.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from modules.scribe import Scribe


class ProfitabilityReporter:
    """Generates and analyzes profitability reports"""
    
    def __init__(self, economics_manager, prompt_manager, router, scribe, event_bus=None):
        """
        Initialize Profitability Reporter
        
        Args:
            economics_manager: EconomicManager instance
            prompt_manager: Prompt manager for templates
            router: LLM router for analysis
            scribe: Action logger
            event_bus: Optional event bus
        """
        self.economics = economics_manager
        self.prompt_manager = prompt_manager
        self.router = router
        self.scribe = scribe
        self.event_bus = event_bus
    
    def generate_comprehensive_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive profitability report with AI analysis.
        
        Args:
            days: Report period in days
            
        Returns:
            Comprehensive profitability report
        """
        try:
            # Get base report
            base_report = self.economics.get_profitability_report(days=days)
            
            # Get comparison data
            previous_report = self.economics.get_profitability_report(days=days*2)
            
            # Perform AI analysis
            prompt_data = self.prompt_manager.get_prompt(
                'economics',
                'analyze_profitability',
                variables={
                    'current_period': json.dumps(base_report),
                    'previous_period': json.dumps(previous_report),
                    'days': days
                }
            )
            
            analysis = self.router.generate(prompt_data['prompt']
            )
            
            parsed_analysis = self._parse_analysis(analysis)
            
            # Compile comprehensive report
            comprehensive = {
                'generated_at': datetime.now().isoformat(),
                'period_days': days,
                'metrics': base_report,
                'analysis': parsed_analysis,
                'trends': self._calculate_trends(base_report, previous_report),
                'recommendations': parsed_analysis.get('recommendations', []),
                'alerts': self._generate_alerts(base_report, parsed_analysis)
            }
            
            self.scribe.log_action(
                "Comprehensive profitability report generated",
                reasoning=f"{days}-day report",
                outcome=f"Profit: ${base_report.get('net_profit', 0):.2f}"
            )
            
            return comprehensive
            
        except Exception as e:
            self.scribe.log_action(
                "Profitability report generation failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return {}
    
    def analyze_income_sources(self) -> Dict[str, Any]:
        """
        Analyze profitability by income source.
        
        Returns:
            Income source breakdown with analysis
        """
        try:
            by_source = self.economics.get_income_by_source()
            
            prompt_data = self.prompt_manager.get_prompt(
                'economics',
                'analyze_income_sources',
                variables={
                    'income_sources': json.dumps(by_source)
                }
            )
            
            analysis = self.router.generate(prompt_data['prompt']
            )
            
            parsed = self._parse_source_analysis(analysis)
            
            return {
                'sources': by_source,
                'analysis': parsed
            }
            
        except Exception as e:
            self.scribe.log_action(
                "Income source analysis failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return {}
    
    def identify_cost_optimization(self) -> List[Dict[str, Any]]:
        """
        Identify opportunities to optimize costs.
        
        Returns:
            List of cost optimization recommendations
        """
        try:
            # Get cost breakdown
            total_costs = self.economics.get_total_costs()
            
            prompt_data = self.prompt_manager.get_prompt(
                'economics',
                'optimize_costs',
                variables={
                    'total_costs': total_costs,
                    'focus_on': 'efficiency, elimination, automation'
                }
            )
            
            analysis = self.router.generate(prompt_data['prompt']
            )
            
            optimizations = self._parse_optimizations(analysis)
            
            return optimizations
            
        except Exception as e:
            self.scribe.log_action(
                "Cost optimization analysis failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return []
    
    def project_future_profitability(self, months: int = 3) -> Dict[str, Any]:
        """
        Project future profitability based on trends.
        
        Args:
            months: Months to project forward
            
        Returns:
            Profitability projections
        """
        try:
            # Get historical data
            history = []
            for i in range(months):
                report = self.economics.get_profitability_report(days=30*(i+1))
                history.append(report)
            
            prompt_data = self.prompt_manager.get_prompt(
                'economics',
                'project_profitability',
                variables={
                    'historical_data': json.dumps(history[-3:]),  # Last 3 periods
                    'projection_months': months,
                    'focus_on': 'trends, assumptions, risks'
                }
            )
            
            analysis = self.router.generate(prompt_data['prompt']
            )
            
            projections = self._parse_projections(analysis)
            
            return projections
            
        except Exception as e:
            self.scribe.log_action(
                "Profitability projection failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return {}
    
    def generate_action_plan(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate action plan for improving profitability.
        
        Args:
            report: Current profitability report
            
        Returns:
            Action plan with priorities
        """
        try:
            prompt_data = self.prompt_manager.get_prompt(
                'economics',
                'generate_action_plan',
                variables={
                    'current_state': json.dumps(report.get('metrics', {})),
                    'analysis': json.dumps(report.get('analysis', {})),
                    'recommendations': json.dumps(report.get('recommendations', []))
                }
            )
            
            analysis = self.router.generate(prompt_data['prompt']
            )
            
            plan = self._parse_action_plan(analysis)
            
            return plan
            
        except Exception as e:
            self.scribe.log_action(
                "Action plan generation failed",
                reasoning=str(e),
                outcome="Failed"
            )
            return {}
    
    # Helper methods
    
    def _calculate_trends(self, current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate profit trends"""
        try:
            current_profit = current.get('net_profit', 0)
            previous_profit = previous.get('net_profit', 0)
            
            if previous_profit == 0:
                change_pct = 0
            else:
                change_pct = ((current_profit - previous_profit) / abs(previous_profit)) * 100
            
            return {
                'previous_profit': previous_profit,
                'current_profit': current_profit,
                'change': current_profit - previous_profit,
                'change_percent': change_pct,
                'trend': 'improving' if change_pct > 0 else 'declining'
            }
        except:
            return {}
    
    def _generate_alerts(self, report: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Generate alerts for profitability issues"""
        alerts = []
        
        # Check profitability
        if not report.get('is_profitable'):
            alerts.append("⚠️  Not profitable - expenses exceed income")
        
        # Check margin
        margin = report.get('profit_margin', 0)
        if margin < 10:
            alerts.append(f"⚠️  Low profit margin ({margin:.1f}%) - less than 10%")
        
        # Check recommendations
        for rec in analysis.get('recommendations', []):
            if 'urgent' in rec.lower() or 'critical' in rec.lower():
                alerts.append(f"🔴 {rec}")
        
        return alerts
    
    def _parse_analysis(self, analysis: str) -> Dict[str, Any]:
        """Parse profitability analysis"""
        try:
            result = json.loads(analysis)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        return {
            'summary': analysis[:200],
            'recommendations': []
        }
    
    def _parse_source_analysis(self, analysis: str) -> Dict[str, Any]:
        """Parse income source analysis"""
        try:
            result = json.loads(analysis)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        return {}
    
    def _parse_optimizations(self, analysis: str) -> List[Dict[str, Any]]:
        """Parse cost optimizations"""
        try:
            result = json.loads(analysis)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
        
        return []
    
    def _parse_projections(self, analysis: str) -> Dict[str, Any]:
        """Parse profitability projections"""
        try:
            result = json.loads(analysis)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        return {}
    
    def _parse_action_plan(self, analysis: str) -> Dict[str, Any]:
        """Parse action plan"""
        try:
            result = json.loads(analysis)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        return {
            'actions': [],
            'priorities': []
        }
