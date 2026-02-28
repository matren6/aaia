"""
Environment Explorer Module - Operational Environment Mapping

PURPOSE:
The Environment Explorer explores and maps the AI's operational environment,
discovering available commands, file system access, network capabilities,
security constraints, and resources. This knowledge enables better decision-
making about what's possible.

PROBLEM SOLVED:
The AI needs to understand its environment to operate effectively:
- What commands are available in PATH?
- What directories can we access/write to?
- Can we make network requests?
- Are we running in a container?
- What Python packages are installed?
- What are the resource limits?

KEY RESPONSIBILITIES:
1. explore_environment(): Comprehensive environment mapping (cached)
2. get_system_info(): Platform, OS, container info, hardware
3. is_containerized(): Detect if running in Docker/container
4. discover_available_commands(): What executables are in PATH
5. map_file_system(): What paths are accessible/writable
6. test_network_capabilities(): DNS, HTTP, ports
7. check_resource_availability(): CPU, memory, disk, network I/O
8. test_security_constraints(): What operations are allowed
9. explore_python_environment(): Python packages, sys.path
10. find_development_opportunities(): What opportunities environment enables
11. get_capability_mapping(): Map capabilities to potential uses

SYSTEM INFO COLLECTED:
- Platform and OS details
- Container detection and ID
- CPU count and current usage
- Memory total/available
- Disk space
- Python version and packages

SECURITY CONSTRAINTS TESTED:
- File write access
- Network access
- Process creation
- Module imports
- Subprocess execution
- Sysadmin (sudo) access

DEPENDENCIES: Scribe, Router
OUTPUTS: Comprehensive environment map, development opportunities
"""

import subprocess
import platform
import os
import sys
import socket
import tempfile
from typing import Dict, List, Optional
from datetime import datetime


class EnvironmentExplorer:
    """Explore and map the AI's operational environment"""

    def __init__(self, scribe, router, event_bus = None):
        self.scribe = scribe
        self.router = router
        self.event_bus = event_bus
        self.environment_map = {}
        self.exploration_cache = None
        self.last_exploration = None

    def explore_environment(self, force: bool = False) -> Dict:
        """Explore the container environment"""
        # Use cached if recent
        if not force and self.exploration_cache:
            age = datetime.now() - self.last_exploration
            if age.total_seconds() < 3600:  # 1 hour cache
                return self.exploration_cache

        exploration = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.get_system_info(),
            "available_commands": self.discover_available_commands(),
            "file_system": self.map_file_system(),
            "network_capabilities": self.test_network_capabilities(),
            "resource_availability": self.check_resource_availability(),
            "security_constraints": self.test_security_constraints(),
            "python_environment": self.explore_python_environment()
        }

        # Update environment map
        self.environment_map = exploration
        self.exploration_cache = exploration
        self.last_exploration = datetime.now()

        # Log exploration
        self.scribe.log_action(
            "Environment exploration",
            f"Discovered {len(exploration['available_commands'])} commands, "
            f"{exploration['resource_availability'].get('disk_free_gb', 0):.1f}GB free",
            "exploration_completed"
        )

        return exploration

    def get_system_info(self) -> Dict:
        """Get information about the system"""
        system_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "cpu_count": os.cpu_count() or 1,
            "current_uid": os.getuid() if hasattr(os, 'getuid') else None,
            "containerized": self.is_containerized(),
            "hostname": socket.gethostname()
        }

        if system_info["containerized"]:
            system_info["container_id"] = self.get_container_id()

        # Try to get memory info
        try:
            import psutil
            memory = psutil.virtual_memory()
            system_info.update({
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_percent": memory.percent
            })

            # Swap memory
            swap = psutil.swap_memory()
            system_info.update({
                "swap_total_gb": round(swap.total / (1024**3), 2),
                "swap_percent": swap.percent
            })

        except ImportError:
            system_info["memory_info"] = "psutil not available"

        return system_info

    def is_containerized(self) -> bool:
        """Check if running in a container"""
        # Check common container indicators
        indicators = [
            os.path.exists("/.dockerenv"),
            os.path.exists("/run/.containerenv"),
            os.path.exists("/proc/1/cgroup") and self._check_cgroup_for_container(),
            os.environ.get("DOCKER_CONTAINER", False),
            os.environ.get("KUBERNETES_SERVICE_HOST", False)
        ]

        return any(indicators)

    def _check_cgroup_for_container(self) -> bool:
        """Check cgroup for container indicators"""
        try:
            with open("/proc/1/cgroup", "r") as f:
                content = f.read()
                return "docker" in content or "container" in content.lower()
        except:
            return False

    def get_container_id(self) -> Optional[str]:
        """Get container ID if available"""
        try:
            # Try various container ID locations
            for path in ["/proc/self/cgroup", "/.dockerenv"]:
                if os.path.exists(path):
                    return path.split("/")[-1][:12]
        except:
            pass
        return "unknown"

    def discover_available_commands(self) -> List[str]:
        """Discover what commands are available in PATH"""
        available_commands = set()

        # Check common directories
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)

        for path_dir in path_dirs:
            if os.path.isdir(path_dir):
                try:
                    files = os.listdir(path_dir)
                    for file in files:
                        file_path = os.path.join(path_dir, file)
                        # Check if executable
                        if os.path.isfile(file_path) and os.access(file_path, os.X_OK) and not file.startswith("."):
                            available_commands.add(file)
                except (PermissionError, OSError):
                    continue

        return sorted(available_commands)

    def map_file_system(self) -> Dict:
        """Map accessible file system areas"""
        filesystem = {
            "accessible_paths": [],
            "writable_paths": [],
            "temp_dir": tempfile.gettempdir(),
            "home_dir": os.path.expanduser("~"),
            "cwd": os.getcwd()
        }

        # Check common paths
        paths_to_check = [
            "/tmp",
            "/home",
            "/workspace",
            "/app",
            "/var",
            "/usr/local"
        ]

        for path in paths_to_check:
            if os.path.exists(path):
                info = {"path": path, "readable": os.access(path, os.R_OK)}

                # Check if writable (be careful!)
                if os.access(path, os.W_OK):
                    filesystem["writable_paths"].append(path)
                    info["writable"] = True
                else:
                    info["writable"] = False

                filesystem["accessible_paths"].append(info)

        return filesystem

    def test_network_capabilities(self) -> Dict:
        """Test network capabilities"""
        capabilities = {
            "dns_resolution": self.test_dns_resolution(),
            "external_http": self.test_http_access(),
            "localhost_access": self.test_localhost_access(),
            "ports_available": self.scan_common_ports()
        }

        return capabilities

    def test_dns_resolution(self) -> bool:
        """Test if DNS resolution works"""
        try:
            socket.gethostbyname("google.com")
            return True
        except:
            return False

    def test_http_access(self) -> bool:
        """Test if HTTP access is possible"""
        try:
            # Try a simple HTTP request
            import urllib.request
            urllib.request.urlopen("https://www.google.com", timeout=5)
            return True
        except:
            # Try with requests if available
            try:
                import requests
                r = requests.get("https://www.google.com", timeout=5)
                return r.status_code == 200
            except:
                return False

    def test_localhost_access(self) -> bool:
        """Test localhost connectivity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', 8080))
            sock.close()
            return result == 0 or result == 111  # 111 = connection refused (but reachable)
        except:
            return False

    def scan_common_ports(self) -> List[Dict]:
        """Scan for commonly available services"""
        ports = [
            (80, "http"),
            (443, "https"),
            (22, "ssh"),
            (5432, "postgres"),
            (3306, "mysql"),
            (6379, "redis"),
            (27017, "mongodb"),
            (8080, "http-alt"),
            (3000, "node"),
            (8000, "python-http")
        ]

        available = []
        for port, service in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                if result == 0:
                    available.append({"port": port, "service": service, "status": "open"})
            except:
                pass

        return available

    def check_resource_availability(self) -> Dict:
        """Check available system resources"""
        resources = {}

        try:
            import psutil

            # CPU
            cpu = psutil.cpu_counts()
            resources["cpu_count"] = cpu
            resources["cpu_percent"] = psutil.cpu_percent(interval=0.1)

            # Memory
            memory = psutil.virtual_memory()
            resources["memory_total_gb"] = round(memory.total / (1024**3), 2)
            resources["memory_available_gb"] = round(memory.available / (1024**3), 2)
            resources["memory_percent"] = memory.percent

            # Disk
            disk = psutil.disk_usage('/')
            resources["disk_total_gb"] = round(disk.total / (1024**3), 2)
            resources["disk_free_gb"] = round(disk.free / (1024**3), 2)
            resources["disk_percent"] = disk.percent

            # Network IO
            net_io = psutil.net_io_counters()
            resources["network_bytes_sent"] = net_io.bytes_sent
            resources["network_bytes_recv"] = net_io.bytes_recv

        except ImportError:
            resources["error"] = "psutil not available"

        return resources

    def test_security_constraints(self) -> Dict:
        """Test what security constraints are in place"""
        constraints = {
            "file_write": self.test_file_write(),
            "network_access": self.test_network_access(),
            "process_creation": self.test_process_creation(),
            "module_import": self.test_module_import(),
            "subprocess_allowed": self.test_subprocess(),
            "sys_admin": self.test_sys_admin()
        }

        return constraints

    def test_file_write(self) -> bool:
        """Test if we can write to files"""
        try:
            test_file = "/tmp/test_write_" + str(os.getpid()) + ".txt"
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except:
            return False

    def test_network_access(self) -> bool:
        """Test if network access is allowed"""
        return self.test_dns_resolution() or self.test_http_access()

    def test_process_creation(self) -> bool:
        """Test if we can create processes"""
        try:
            # Try simple fork (Unix) or just check os module
            import multiprocessing
            return True
        except:
            return False

    def test_module_import(self) -> bool:
        """Test if we can import modules"""
        test_modules = ["json", "sqlite3", "requests", "psutil"]
        available = []

        for module in test_modules:
            try:
                __import__(module)
                available.append(module)
            except ImportError:
                pass

        return {"tested": test_modules, "available": available}

    def test_subprocess(self) -> bool:
        """Test if subprocess is allowed"""
        try:
            result = subprocess.run(
                ["echo", "test"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def test_sys_admin(self) -> bool:
        """Test if we have sys admin capabilities"""
        # Check for sudo access (very rough check)
        try:
            if os.getuid() == 0:
                return True  # Running as root
            # Check if we can use sudo without password
            result = subprocess.run(
                ["sudo", "-n", "true"],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False

    def explore_python_environment(self) -> Dict:
        """Explore Python environment"""
        env = {
            "python_path": sys.path,
            "loaded_modules": list(sys.modules.keys())[:20],  # First 20
            "version": sys.version
        }

        # Check for key packages
        packages = ["requests", "psutil", "numpy", "pandas", "flask", "django", "torch", "tensorflow"]
        env["available_packages"] = []

        for pkg in packages:
            try:
                __import__(pkg)
                env["available_packages"].append(pkg)
            except ImportError:
                pass

        return env

    def find_development_opportunities(self) -> List[Dict]:
        """Find opportunities based on environment exploration"""
        if not self.environment_map:
            self.explore_environment()

        opportunities = []

        # Check for development tools
        dev_tools = ["git", "docker", "python3", "pip", "pip3", "node", "npm", "gcc", "make", "curl", "wget"]
        available_commands = self.environment_map.get("available_commands", [])

        missing_tools = [tool for tool in dev_tools if tool not in available_commands]

        if missing_tools:
            opportunities.append({
                "type": "tool_installation",
                "tools": missing_tools[:5],
                "value": "Enable development and integration capabilities",
                "complexity": "low"
            })

        # Check for API access
        if self.environment_map.get("network_capabilities", {}).get("external_http", False):
            opportunities.append({
                "type": "api_integration",
                "description": "External HTTP access available",
                "value": "Expand capabilities through web services",
                "complexity": "medium"
            })

        # Check for container benefits
        if self.environment_map.get("system_info", {}).get("containerized", False):
            opportunities.append({
                "type": "container_optimization",
                "description": "Running in container - optimize for containerized deployment",
                "value": "Better resource management and portability",
                "complexity": "medium"
            })

        # Check for resource availability
        resources = self.environment_map.get("resource_availability", {})
        if resources.get("memory_available_gb", 0) > 4:
            opportunities.append({
                "type": "memory_intensive_operations",
                "description": "Available memory allows for caching and complex operations",
                "value": "Improve performance with intelligent caching",
                "complexity": "low"
            })

        return opportunities

    def get_capability_mapping(self) -> Dict:
        """Map system capabilities to potential uses"""
        if not self.environment_map:
            self.explore_environment()

        available = self.environment_map.get("available_commands", [])
        network = self.environment_map.get("network_capabilities", {})

        mapping = {
            "file_operations": "read write delete".split() if self.environment_map.get("security_constraints", {}).get("file_write") else [],
            "web_requests": ["curl", "wget", "python"] if network.get("external_http") else [],
            "database": ["psql", "mysql", "sqlite3"] if any(c in available for c in ["psql", "mysql", "sqlite3"]) else [],
            "version_control": ["git"] if "git" in available else [],
            "container_ops": ["docker"] if "docker" in available else [],
            "process_management": ["python", "bash"] if self.environment_map.get("security_constraints", {}).get("subprocess_allowed") else []
        }

        return mapping