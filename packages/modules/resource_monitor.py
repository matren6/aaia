"""
Resource Monitor Module - Track Physical Resource Costs

Monitors and records the cost of:
- CPU time (user + system)
- Memory usage (resident set size)
- Electricity consumption (based on estimated system power)

Publishes RESOURCE_COST events and logs transactions via EconomicManager.

Electricity Cost Model:
- Assumes estimated_system_power_watts (default 150W) for the entire system
- Calculates cost: power_kw * hours * electricity_cost_per_kwh
- Electricity cost configured per kWh (default $0.50 for EU rates)
"""

import threading
import time
import psutil
import sqlite3
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Optional


class ResourceMonitor:
    """Monitors physical resource usage and calculates costs"""
    
    def __init__(self, economic_manager, scribe, event_bus=None, config=None):
        """
        Initialize Resource Monitor
        
        Args:
            economic_manager: EconomicManager for transaction logging
            scribe: Scribe for action logging
            event_bus: Optional EventBus for publishing events
            config: SystemConfig with economics settings
        """
        self.economic_manager = economic_manager
        self.scribe = scribe
        self.event_bus = event_bus
        
        # Load configuration
        if config:
            self.cpu_cost_per_second = Decimal(str(config.economics.cpu_cost_per_second))
            self.memory_cost_per_gb_hour = Decimal(str(config.economics.memory_cost_per_gb_hour))
            self.storage_cost_per_gb_month = Decimal(str(config.economics.storage_cost_per_gb_month))
            self.electricity_cost_per_kwh = Decimal(str(config.economics.electricity_cost_per_kwh))
            self.interval = config.economics.resource_monitoring_interval
            self.threshold = Decimal(str(config.economics.resource_cost_threshold))
            self.system_power_watts = config.economics.estimated_system_power_watts
            self.enabled = config.economics.resource_monitoring_enabled
        else:
            self.cpu_cost_per_second = Decimal('0.0001')
            self.memory_cost_per_gb_hour = Decimal('0.01')
            self.storage_cost_per_gb_month = Decimal('0.10')
            self.electricity_cost_per_kwh = Decimal('0.50')
            self.interval = 300
            self.threshold = Decimal('0.01')
            self.system_power_watts = 150.0
            self.enabled = True
        
        self.running = False
        self.monitor_thread = None
        self.process = psutil.Process()
        
        # Tracking variables
        self.last_cpu_times = None
        self.last_check_time = None
        
        # Initialize database table
        self._init_database(scribe)
    
    def _init_database(self, scribe):
        """Initialize resource_costs table if needed"""
        try:
            conn = sqlite3.connect(scribe.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resource_costs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    cost REAL NOT NULL,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_resource_costs_timestamp 
                ON resource_costs(timestamp DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_resource_costs_type 
                ON resource_costs(resource_type)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.scribe.log_action(
                "Resource cost database initialization failed",
                reasoning=str(e),
                outcome="Error"
            )
    
    def start(self):
        """Start resource monitoring"""
        if not self.enabled:
            self.scribe.log_action(
                "Resource monitoring disabled",
                reasoning="Configuration disabled",
                outcome="Not started"
            )
            return
        
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.scribe.log_action(
            "Resource monitoring started",
            reasoning=f"Interval: {self.interval}s, Electricity: ${self.electricity_cost_per_kwh}/kWh, System: {self.system_power_watts}W",
            outcome="Running"
        )
    
    def stop(self):
        """Stop resource monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.scribe.log_action(
            "Resource monitoring stopped",
            reasoning="Shutdown",
            outcome="Stopped"
        )
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                costs = self._calculate_interval_costs()
                total_cost = sum(costs.values(), Decimal('0'))
                
                # Log if above threshold
                if total_cost >= self.threshold:
                    self._log_resource_costs(costs, total_cost)
                
            except Exception as e:
                self.scribe.log_action(
                    "Resource monitoring error",
                    reasoning=str(e),
                    outcome="Error"
                )
            
            time.sleep(self.interval)
    
    def _calculate_interval_costs(self) -> Dict[str, Decimal]:
        """Calculate costs for the current interval"""
        costs = {}
        current_time = datetime.now()
        
        # Initialize timing on first run
        if self.last_check_time is None:
            self.last_check_time = current_time
        
        time_delta = (current_time - self.last_check_time).total_seconds()
        self.last_check_time = current_time
        
        # CPU cost
        cpu_times = self.process.cpu_times()
        if self.last_cpu_times:
            cpu_delta = (cpu_times.user + cpu_times.system) - \
                       (self.last_cpu_times.user + self.last_cpu_times.system)
            costs['cpu'] = self.cpu_cost_per_second * Decimal(str(cpu_delta))
        else:
            costs['cpu'] = Decimal('0')
        
        self.last_cpu_times = cpu_times
        
        # Memory cost (RSS - Resident Set Size)
        memory_info = self.process.memory_info()
        memory_gb = Decimal(str(memory_info.rss / (1024 ** 3)))  # Convert to GB
        memory_hours = Decimal(str(time_delta / 3600))  # Convert seconds to hours
        costs['memory'] = self.memory_cost_per_gb_hour * memory_gb * memory_hours
        
        # Electricity cost
        # Formula: (power_watts / 1000) * (time_seconds / 3600) * cost_per_kwh
        # Simplified: power_watts * time_seconds / 3600000 * cost_per_kwh
        power_kw = Decimal(str(self.system_power_watts / 1000))  # Convert watts to kW
        kwh_used = power_kw * Decimal(str(time_delta)) / Decimal('3600')  # Convert seconds to hours
        costs['electricity'] = kwh_used * self.electricity_cost_per_kwh
        
        # Storage cost (approximate as monthly cost / 2880 intervals per month)
        # Only accrue if storage size is significant
        costs['storage'] = Decimal('0')  # Not tracked per interval
        
        return costs
    
    def _log_resource_costs(self, costs: Dict[str, Decimal], total: Decimal):
        """Log resource costs as economic transactions"""
        # Log individual cost components
        for resource, cost in costs.items():
            if cost > Decimal('0'):
                self.economic_manager.log_transaction(
                    description=f"Resource cost: {resource}",
                    amount=-cost,  # Negative = expense
                    category='compute',
                    metadata={
                        'resource_type': resource,
                        'interval_seconds': self.interval
                    }
                )
        
        # Also log to resource_costs table for detailed tracking
        self._log_to_resource_table(costs)
        
        # Emit event
        if self.event_bus:
            try:
                from modules.bus import Event, EventType
                self.event_bus.emit(Event(EventType.RESOURCE_COST, {
                    'total_cost': float(total),
                    'breakdown': {k: float(v) for k, v in costs.items()},
                    'interval': self.interval,
                    'electricity_kwh': float(costs.get('electricity', Decimal('0'))) / float(self.electricity_cost_per_kwh) if self.electricity_cost_per_kwh > 0 else 0,
                    'memory_gb': float(self.process.memory_info().rss / (1024 ** 3))
                }))
            except:
                pass
    
    def _log_to_resource_table(self, costs: Dict[str, Decimal]):
        """Log cost details to resource_costs table"""
        try:
            conn = sqlite3.connect(self.scribe.db_path)
            cursor = conn.cursor()
            
            for resource_type, cost in costs.items():
                if cost > Decimal('0'):
                    # Determine quantity and unit based on resource type
                    if resource_type == 'cpu':
                        quantity = float(self.process.cpu_times().user + self.process.cpu_times().system)
                        unit = 'seconds'
                    elif resource_type == 'memory':
                        quantity = float(self.process.memory_info().rss / (1024 ** 3))
                        unit = 'GB'
                    elif resource_type == 'electricity':
                        # Calculate kWh
                        kwh = float(cost) / float(self.electricity_cost_per_kwh) if self.electricity_cost_per_kwh > 0 else 0
                        quantity = kwh
                        unit = 'kWh'
                    else:
                        quantity = 0
                        unit = 'unknown'
                    
                    cursor.execute('''
                        INSERT INTO resource_costs (timestamp, resource_type, quantity, unit, cost, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        datetime.now().isoformat(),
                        resource_type,
                        quantity,
                        unit,
                        float(cost),
                        None
                    ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            pass  # Silently fail, already logged via transaction
    
    def get_current_usage(self) -> Dict[str, Any]:
        """Get current resource usage snapshot"""
        cpu_percent = self.process.cpu_percent(interval=1)
        memory_info = self.process.memory_info()
        
        return {
            'cpu_percent': cpu_percent,
            'memory_mb': memory_info.rss / (1024 ** 2),
            'memory_percent': self.process.memory_percent(),
            'num_threads': self.process.num_threads(),
            'power_draw_watts': self.system_power_watts
        }
    
    def get_resource_costs(self, days: int = 30) -> Dict[str, float]:
        """Get resource costs for the specified period"""
        try:
            conn = sqlite3.connect(self.scribe.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT resource_type, SUM(cost)
                FROM resource_costs
                WHERE timestamp >= datetime('now', ? || ' days')
                GROUP BY resource_type
            ''', (f'-{days}',))
            
            result = {}
            for row in cursor.fetchall():
                result[row[0]] = float(row[1]) if row[1] else 0.0
            
            conn.close()
            return result
        except Exception:
            return {}
