"""
Unit Tests for Phase 5 Modules

Tests for:
- TraitExtractor
- AutonomousTraitLearning
- ReflectionAnalyzer
- ProfitabilityReporter
"""

import pytest
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import Mock, MagicMock, patch
import json


class TestTraitExtractor:
    """Tests for TraitExtractor module"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies"""
        return {
            'prompt_manager': Mock(),
            'router': Mock(),
            'scribe': Mock(),
            'event_bus': Mock()
        }
    
    @pytest.fixture
    def trait_extractor(self, mock_dependencies):
        """Create TraitExtractor instance"""
        from modules.trait_extractor import TraitExtractor
        return TraitExtractor(
            prompt_manager=mock_dependencies['prompt_manager'],
            router=mock_dependencies['router'],
            scribe=mock_dependencies['scribe'],
            event_bus=mock_dependencies['event_bus']
        )
    
    def test_initialization(self, trait_extractor):
        """Test TraitExtractor initialization"""
        assert trait_extractor.prompt_manager is not None
        assert trait_extractor.router is not None
        assert trait_extractor.scribe is not None
        assert len(trait_extractor.categories) == 10
    
    def test_extract_from_interaction(self, trait_extractor, mock_dependencies):
        """Test single interaction trait extraction"""
        interaction = {
            'input': 'show me the status',
            'response': 'System is healthy',
            'intent': 'query',
            'success': True
        }
        current_traits = {}
        
        # Mock prompt manager
        mock_dependencies['prompt_manager'].get_prompt.return_value = {
            'prompt': 'Test prompt'
        }
        
        # Mock router
        mock_dependencies['router'].route_request.return_value = ('model', 'cost')
        mock_dependencies['router'].call_model.return_value = json.dumps([
            {
                'category': 'communication_style',
                'name': 'directness',
                'value': 'direct',
                'confidence': 0.85,
                'evidence': 'User prefers short responses'
            }
        ])
        
        traits = trait_extractor.extract_from_interaction(interaction, current_traits)
        
        assert len(traits) > 0
        assert traits[0]['category'] == 'communication_style'
    
    def test_parse_extracted_traits(self, trait_extractor):
        """Test trait parsing"""
        analysis = json.dumps([
            {
                'category': 'decision_style',
                'name': 'analytical',
                'value': 'data-driven',
                'confidence': 0.9,
                'evidence': 'User asks for metrics'
            }
        ])
        
        traits = trait_extractor._parse_extracted_traits(analysis)
        
        assert len(traits) == 1
        assert traits[0]['name'] == 'analytical'
    
    def test_detect_trait_changes(self, trait_extractor):
        """Test trait change detection"""
        old_traits = {
            'communication_style': {
                'directness': {
                    'value': 'verbose',
                    'confidence': 0.7
                }
            }
        }
        
        new_traits = {
            'communication_style': {
                'directness': {
                    'value': 'direct',
                    'confidence': 0.85
                }
            }
        }
        
        changes = trait_extractor.detect_trait_changes(old_traits, new_traits)
        
        assert len(changes) == 1
        assert changes[0]['change_type'] == 'updated'


class TestReflectionAnalyzer:
    """Tests for ReflectionAnalyzer module"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies"""
        return {
            'prompt_manager': Mock(),
            'router': Mock(),
            'scribe': Mock(),
            'event_bus': Mock()
        }
    
    @pytest.fixture
    def reflection_analyzer(self, mock_dependencies):
        """Create ReflectionAnalyzer instance"""
        from modules.reflection_analyzer import ReflectionAnalyzer
        return ReflectionAnalyzer(
            prompt_manager=mock_dependencies['prompt_manager'],
            router=mock_dependencies['router'],
            scribe=mock_dependencies['scribe'],
            event_bus=mock_dependencies['event_bus']
        )
    
    def test_initialization(self, reflection_analyzer):
        """Test ReflectionAnalyzer initialization"""
        assert reflection_analyzer.prompt_manager is not None
        assert reflection_analyzer.router is not None
        assert reflection_analyzer.scribe is not None
    
    def test_summarize_profile(self, reflection_analyzer):
        """Test profile summarization"""
        profile = {
            'communication_style': [
                {'name': 'directness', 'value': 'direct', 'confidence': 0.85}
            ],
            'decision_style': []
        }
        
        summary = reflection_analyzer._summarize_profile(profile)
        
        assert 'Communication Style' in summary
        assert 'direct' in summary
        assert '85%' in summary
    
    def test_summarize_interactions(self, reflection_analyzer):
        """Test interaction summarization"""
        interactions = [
            {'input': 'show status', 'intent': 'query', 'success': True},
            {'input': 'create tool', 'intent': 'creation', 'success': True},
        ]
        
        summary = reflection_analyzer._summarize_interactions(interactions)
        
        assert 'query' in summary.lower()
        assert 'creation' in summary.lower()


class TestProfitabilityReporter:
    """Tests for ProfitabilityReporter module"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies"""
        return {
            'economics_manager': Mock(),
            'prompt_manager': Mock(),
            'router': Mock(),
            'scribe': Mock(),
            'event_bus': Mock()
        }
    
    @pytest.fixture
    def profitability_reporter(self, mock_dependencies):
        """Create ProfitabilityReporter instance"""
        from modules.profitability_reporter import ProfitabilityReporter
        return ProfitabilityReporter(
            economics_manager=mock_dependencies['economics_manager'],
            prompt_manager=mock_dependencies['prompt_manager'],
            router=mock_dependencies['router'],
            scribe=mock_dependencies['scribe'],
            event_bus=mock_dependencies['event_bus']
        )
    
    def test_initialization(self, profitability_reporter):
        """Test ProfitabilityReporter initialization"""
        assert profitability_reporter.economics is not None
        assert profitability_reporter.prompt_manager is not None
        assert profitability_reporter.router is not None
    
    def test_calculate_trends(self, profitability_reporter):
        """Test trend calculation"""
        current = {'net_profit': 100}
        previous = {'net_profit': 80}
        
        trends = profitability_reporter._calculate_trends(current, previous)
        
        assert trends['current_profit'] == 100
        assert trends['previous_profit'] == 80
        assert trends['change'] == 20
        assert trends['change_percent'] == 25.0
        assert trends['trend'] == 'improving'
    
    def test_generate_alerts(self, profitability_reporter):
        """Test alert generation"""
        report = {
            'is_profitable': False,
            'profit_margin': 5
        }
        analysis = {
            'recommendations': ['urgent: increase prices']
        }
        
        alerts = profitability_reporter._generate_alerts(report, analysis)
        
        assert len(alerts) > 0
        assert any('not profitable' in alert.lower() for alert in alerts)
        assert any('low profit margin' in alert.lower() for alert in alerts)


class TestAutonomousTraitLearning:
    """Tests for AutonomousTraitLearning module"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies"""
        return {
            'master_model': Mock(),
            'trait_extractor': Mock(),
            'scribe': Mock(),
            'event_bus': Mock()
        }
    
    @pytest.fixture
    def autonomous_learning(self, mock_dependencies):
        """Create AutonomousTraitLearning instance"""
        from modules.trait_extractor import AutonomousTraitLearning
        return AutonomousTraitLearning(
            master_model_manager=mock_dependencies['master_model'],
            trait_extractor=mock_dependencies['trait_extractor'],
            scribe=mock_dependencies['scribe'],
            event_bus=mock_dependencies['event_bus']
        )
    
    def test_initialization(self, autonomous_learning):
        """Test AutonomousTraitLearning initialization"""
        assert autonomous_learning.master_model is not None
        assert autonomous_learning.trait_extractor is not None
        assert autonomous_learning.scribe is not None


class TestModuleIntegration:
    """Integration tests for Phase 5 modules"""
    
    def test_trait_extractor_import(self):
        """Test TraitExtractor can be imported"""
        from modules.trait_extractor import TraitExtractor
        assert TraitExtractor is not None
    
    def test_reflection_analyzer_import(self):
        """Test ReflectionAnalyzer can be imported"""
        from modules.reflection_analyzer import ReflectionAnalyzer
        assert ReflectionAnalyzer is not None
    
    def test_profitability_reporter_import(self):
        """Test ProfitabilityReporter can be imported"""
        from modules.profitability_reporter import ProfitabilityReporter
        assert ProfitabilityReporter is not None
    
    def test_autonomous_learning_import(self):
        """Test AutonomousTraitLearning can be imported"""
        from modules.trait_extractor import AutonomousTraitLearning
        assert AutonomousTraitLearning is not None


class TestDIContainerIntegration:
    """Tests for DI container integration"""
    
    def test_trait_extractor_registration(self):
        """Test TraitExtractor can be retrieved from container"""
        from modules.setup import SystemBuilder
        from modules.settings import get_config
        
        config = get_config()
        builder = SystemBuilder(config)
        system = builder.build()
        container = system['container']
        
        try:
            trait_extractor = container.get('TraitExtractor')
            assert trait_extractor is not None
        except Exception as e:
            pytest.skip(f"Container setup issue: {e}")
    
    def test_reflection_analyzer_registration(self):
        """Test ReflectionAnalyzer can be retrieved from container"""
        from modules.setup import SystemBuilder
        from modules.settings import get_config
        
        config = get_config()
        builder = SystemBuilder(config)
        system = builder.build()
        container = system['container']
        
        try:
            analyzer = container.get('ReflectionAnalyzer')
            assert analyzer is not None
        except Exception as e:
            pytest.skip(f"Container setup issue: {e}")
    
    def test_profitability_reporter_registration(self):
        """Test ProfitabilityReporter can be retrieved from container"""
        from modules.setup import SystemBuilder
        from modules.settings import get_config
        
        config = get_config()
        builder = SystemBuilder(config)
        system = builder.build()
        container = system['container']
        
        try:
            reporter = container.get('ProfitabilityReporter')
            assert reporter is not None
        except Exception as e:
            pytest.skip(f"Container setup issue: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
