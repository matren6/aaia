"""
Database migrations

Each migration is a Python file in this directory with a Migration class.
Migrations are numbered sequentially starting from 1.
"""
from typing import Dict
import sqlite3
from abc import ABC, abstractmethod


class Migration(ABC):
    """Base class for database migrations"""
    
    def __init__(self):
        self.description = "No description"
    
    @abstractmethod
    def up(self, conn: sqlite3.Connection):
        """Apply the migration"""
        pass
    
    @abstractmethod
    def down(self, conn: sqlite3.Connection):
        """Revert the migration"""
        pass


def get_migrations() -> Dict[int, Migration]:
    """Get all available migrations"""
    from .migration_001_initial_schema import Migration001
    from .migration_002_add_goals import Migration002
    from .migration_003_add_capabilities import Migration003
    from .migration_004_add_master_model import Migration004
    from .migration_005_add_income_tracking import Migration005
    from .migration_006_add_mandate_overrides import Migration006
    from .migration_007_provider_performance import Migration007
    from .migration_008_resource_costs import Migration008
    from .migration_009_add_safety_lockouts import Migration009
    from .migration_010_add_proactive_notifications import Migration010
    from .migration_011_add_dialogue_outcomes import Migration011
    from .migration_012_add_final_mandate_tracking import Migration012
    from .migration_013_add_wellbeing_tracking import Migration013
    from .migration_014_add_subjective_value import Migration014
    from .migration_015_add_pending_dialogues import Migration015
    from .migration_016_add_llm_tracking import Migration016

    return {
        1: Migration001(),
        2: Migration002(),
        3: Migration003(),
        4: Migration004(),
        5: Migration005(),
        6: Migration006(),
        7: Migration007(),
        8: Migration008(),
        9: Migration009(),
        10: Migration010(),
        11: Migration011(),
        12: Migration012(),
        13: Migration013(),
        14: Migration014(),
        15: Migration015(),
        16: Migration016(),
    }
