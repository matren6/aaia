# /opt/autonomous-agent/router/rate_limiter.py
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import logging

class RateLimiter:
    """Handles rate limiting and token budgeting across providers."""
    
    def __init__(self, db_path: str = "/opt/agent-data/rate_limit.db"):
        self.logger = logging.getLogger("rate_limiter")
        self.db_path = db_path
        self._init_database()
        
        # In-memory sliding windows
        self.rpm_windows = {}  # provider -> [timestamps]
        self.tpm_windows = {}  # provider -> [(timestamp, tokens)]
        
        # Default limits (can be overridden per-provider)
        self.default_limits = {
            "groq": {"rpm": 30, "tpm": 12000, "rpd": 14400},
            "venice": {"rpm": 60, "tpm": 30000, "daily_budget": 0.49},
            "ollama": {"rpm": 1000, "tpm": 1000000}  # Effectively unlimited
        }
        
        self.logger.info("RateLimiter initialized")
    
    def _init_database(self):
        """Initialize SQLite database for persistent tracking."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Daily usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_usage (
                date DATE NOT NULL,
                provider TEXT NOT NULL,
                request_count INTEGER DEFAULT 0,
                token_count INTEGER DEFAULT 0,
                cost DECIMAL(10, 6) DEFAULT 0.0,
                PRIMARY KEY (date, provider)
            )
        ''')
        
        # Budget tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_usage (
                date DATE PRIMARY KEY,
                provider TEXT NOT NULL,
                spent DECIMAL(10, 6) DEFAULT 0.0,
                budget DECIMAL(10, 6) DEFAULT 0.0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def check_rpm_limit(self, provider: str, buffer: int = 3) -> bool:
        """Check if provider is within RPM limits."""
        if provider not in self.rpm_windows:
            self.rpm_windows[provider] = []
        
        now = time.time()
        window_start = now - 60  # Last 60 seconds
        
        # Clean old entries
        self.rpm_windows[provider] = [
            ts for ts in self.rpm_windows[provider] if ts > window_start
        ]
        
        rpm_limit = self.default_limits.get(provider, {}).get("rpm", 30)
        current_rpm = len(self.rpm_windows[provider])
        
        if current_rpm >= (rpm_limit - buffer):
            self.logger.warning(
                f"{provider.upper()} RPM limit approached: "
                f"{current_rpm}/{rpm_limit} requests in last minute"
            )
            return False
        
        return True
    
    def check_tpm_limit(self, provider: str, estimated_tokens: int, buffer: int = 1000) -> bool:
        """Check if provider is within TPM limits."""
        if provider not in self.tpm_windows:
            self.tpm_windows[provider] = []
        
        now = time.time()
        window_start = now - 60  # Last 60 seconds
        
        # Clean old entries
        self.tpm_windows[provider] = [
            (ts, tokens) for ts, tokens in self.tpm_windows[provider] 
            if ts > window_start
        ]
        
        tpm_limit = self.default_limits.get(provider, {}).get("tpm", 12000)
        current_tpm = sum(tokens for ts, tokens in self.tpm_windows[provider])
        
        if current_tpm + estimated_tokens > (tpm_limit - buffer):
            self.logger.warning(
                f"{provider.upper()} TPM limit would be exceeded: "
                f"{current_tpm}/{tpm_limit} tokens, "
                f"requesting {estimated_tokens} more"
            )
            return False
        
        return True
    
    def check_daily_limits(self, provider: str, estimated_cost: float = 0) -> bool:
        """Check daily request limits and budget."""
        today = datetime.now().date()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check daily request count
            cursor.execute('''
                SELECT request_count FROM daily_usage 
                WHERE date = ? AND provider = ?
            ''', (today.isoformat(), provider))
            
            result = cursor.fetchone()
            daily_requests = result[0] if result else 0
            
            rpd_limit = self.default_limits.get(provider, {}).get("rpd", 14400)
            if daily_requests >= rpd_limit:
                self.logger.warning(
                    f"{provider.upper()} daily request limit reached: "
                    f"{daily_requests}/{rpd_limit}"
                )
                conn.close()
                return False
            
            # Check budget if applicable
            if estimated_cost > 0:
                budget = self.default_limits.get(provider, {}).get("daily_budget", float('inf'))
                if budget < float('inf'):  # Provider has a budget
                    cursor.execute('''
                        SELECT SUM(spent) FROM budget_usage 
                        WHERE date = ? AND provider = ?
                    ''', (today.isoformat(), provider))
                    
                    result = cursor.fetchone()
                    spent_today = result[0] if result and result[0] else 0
                    
                    if spent_today + estimated_cost > budget:
                        self.logger.warning(
                            f"{provider.upper()} daily budget exceeded: "
                            f"${spent_today:.6f}/${budget:.6f} spent"
                        )
                        conn.close()
                        return False
            
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking daily limits for {provider}: {e}")
            return False
    
    def record_request(self, provider: str, tokens: int = 0, cost: float = 0.0):
        """Record a successful request."""
        now = time.time()
        
        # Update sliding windows
        if provider not in self.rpm_windows:
            self.rpm_windows[provider] = []
        self.rpm_windows[provider].append(now)
        
        if tokens > 0:
            if provider not in self.tpm_windows:
                self.tpm_windows[provider] = []
            self.tpm_windows[provider].append((now, tokens))
        
        # Update database
        try:
            today = datetime.now().date()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update daily usage
            cursor.execute('''
                INSERT INTO daily_usage (date, provider, request_count, token_count, cost)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(date, provider) DO UPDATE SET
                    request_count = request_count + 1,
                    token_count = token_count + ?,
                    cost = cost + ?
            ''', (today.isoformat(), provider, tokens, cost, tokens, cost))
            
            # Update budget if applicable
            if cost > 0:
                cursor.execute('''
                    INSERT INTO budget_usage (date, provider, spent)
                    VALUES (?, ?, ?)
                    ON CONFLICT(date, provider) DO UPDATE SET
                        spent = spent + ?
                ''', (today.isoformat(), provider, cost, cost))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error recording request for {provider}: {e}")