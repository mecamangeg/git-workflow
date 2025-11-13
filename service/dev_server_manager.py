"""
Dev Server Manager - Manage lifecycle of development servers.

Features:
- Start/stop/restart dev servers
- Health monitoring
- Auto-restart on failures
- Process management
- Port conflict detection
"""

import asyncio
import logging
import subprocess
import signal
import time
import aiohttp
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime

from .dev_server_detector import DevServerDetector, DevServerConfig

logger = logging.getLogger(__name__)


@dataclass
class ServerProcess:
    """Running dev server process information"""
    config: DevServerConfig
    process: asyncio.subprocess.Process
    started_at: datetime
    pid: int
    repo_path: Path
    branch_name: str
    restart_count: int = 0
    last_health_check: Optional[datetime] = None
    is_healthy: bool = False


class DevServerManager:
    """
    Manage development server lifecycle.

    Features:
    - Start server on branch sync
    - Stop server on branch change
    - Restart server on failures
    - Health monitoring
    - Resource cleanup
    """

    def __init__(self, config: dict):
        """
        Initialize dev server manager.

        Args:
            config: Configuration dict from sync.yaml
        """
        self.config = config
        self.detector = DevServerDetector(
            custom_config=config.get('dev_servers', {}).get('custom', {})
        )

        # Track running servers by repo path
        self.running_servers: Dict[str, ServerProcess] = {}

        # Health check settings
        self.health_check_interval = config.get('dev_servers', {}).get('health_check_interval', 30)
        self.max_restart_attempts = config.get('dev_servers', {}).get('max_restart_attempts', 3)
        self.startup_timeout = config.get('dev_servers', {}).get('startup_timeout', 60)

    async def start_server(
        self,
        repo_path: Path,
        branch_name: str,
        force_restart: bool = False
    ) -> bool:
        """
        Start dev server for repository.

        Args:
            repo_path: Path to repository
            branch_name: Current branch name
            force_restart: Force restart if already running

        Returns:
            True if server started successfully, False otherwise
        """
        repo_key = str(repo_path)

        # Check if server already running
        if repo_key in self.running_servers:
            if force_restart:
                logger.info(f"Force restarting server for {repo_path.name}")
                await self.stop_server(repo_path)
            else:
                logger.info(f"Server already running for {repo_path.name}")
                return True

        # Detect dev server config
        server_config = self.detector.detect(repo_path)
        if not server_config:
            logger.info(f"No dev server detected for {repo_path.name}")
            return False

        logger.info(f"Starting {server_config.project_type} dev server for {repo_path.name}")
        logger.info(f"Command: {server_config.command}")
        logger.info(f"Port: {server_config.port}")

        try:
            # Check if port is available
            if not await self._is_port_available(server_config.port):
                logger.warning(f"Port {server_config.port} already in use")
                # Try to kill process using port (optional, can be dangerous)
                # For now, just fail
                return False

            # Prepare environment
            env = self._prepare_environment(server_config)

            # Start process
            process = await asyncio.create_subprocess_shell(
                server_config.command,
                cwd=server_config.working_dir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL
            )

            # Create server process record
            server_process = ServerProcess(
                config=server_config,
                process=process,
                started_at=datetime.now(),
                pid=process.pid,
                repo_path=repo_path,
                branch_name=branch_name
            )

            self.running_servers[repo_key] = server_process

            logger.info(f"Dev server started (PID: {process.pid})")

            # Wait for server to be healthy
            await self._wait_for_healthy(server_process)

            return True

        except Exception as e:
            logger.error(f"Failed to start dev server: {e}", exc_info=True)
            return False

    async def stop_server(self, repo_path: Path) -> bool:
        """
        Stop dev server for repository.

        Args:
            repo_path: Path to repository

        Returns:
            True if stopped successfully, False otherwise
        """
        repo_key = str(repo_path)

        if repo_key not in self.running_servers:
            logger.debug(f"No server running for {repo_path.name}")
            return True

        server_process = self.running_servers[repo_key]

        logger.info(f"Stopping dev server for {repo_path.name} (PID: {server_process.pid})")

        try:
            # Try graceful shutdown first (SIGTERM)
            try:
                server_process.process.terminate()
                await asyncio.wait_for(server_process.process.wait(), timeout=10)
                logger.info(f"Server stopped gracefully")
            except asyncio.TimeoutError:
                # Force kill if graceful shutdown fails
                logger.warning(f"Graceful shutdown timeout, force killing...")
                server_process.process.kill()
                await server_process.process.wait()
                logger.info(f"Server force killed")

            # Remove from running servers
            del self.running_servers[repo_key]
            return True

        except Exception as e:
            logger.error(f"Error stopping server: {e}", exc_info=True)
            return False

    async def restart_server(self, repo_path: Path, branch_name: str) -> bool:
        """
        Restart dev server for repository.

        Args:
            repo_path: Path to repository
            branch_name: Current branch name

        Returns:
            True if restarted successfully
        """
        logger.info(f"Restarting dev server for {repo_path.name}")

        await self.stop_server(repo_path)
        await asyncio.sleep(2)  # Brief pause
        return await self.start_server(repo_path, branch_name)

    async def health_check(self, repo_path: Path) -> bool:
        """
        Check if dev server is healthy.

        Args:
            repo_path: Path to repository

        Returns:
            True if healthy, False otherwise
        """
        repo_key = str(repo_path)

        if repo_key not in self.running_servers:
            return False

        server_process = self.running_servers[repo_key]

        # Check if process is still alive
        if server_process.process.returncode is not None:
            logger.warning(f"Dev server process died (exit code: {server_process.process.returncode})")
            server_process.is_healthy = False
            return False

        # HTTP health check
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    server_process.config.health_check_url,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    is_healthy = response.status < 500
                    server_process.is_healthy = is_healthy
                    server_process.last_health_check = datetime.now()

                    if is_healthy:
                        logger.debug(f"Health check passed for {repo_path.name}")
                    else:
                        logger.warning(f"Health check failed: HTTP {response.status}")

                    return is_healthy

        except aiohttp.ClientError as e:
            logger.debug(f"Health check failed: {e}")
            server_process.is_healthy = False
            return False
        except asyncio.TimeoutError:
            logger.debug(f"Health check timeout")
            server_process.is_healthy = False
            return False

    async def monitor_servers(self):
        """Monitor all running servers and restart if needed"""
        while True:
            try:
                for repo_key, server_process in list(self.running_servers.items()):
                    repo_path = server_process.repo_path

                    # Check health
                    is_healthy = await self.health_check(repo_path)

                    if not is_healthy:
                        logger.warning(f"Server unhealthy: {repo_path.name}")

                        # Auto-restart if configured and under max attempts
                        auto_restart = self.config.get('dev_servers', {}).get('auto_restart', True)

                        if auto_restart and server_process.restart_count < self.max_restart_attempts:
                            logger.info(f"Auto-restarting server (attempt {server_process.restart_count + 1}/{self.max_restart_attempts})")
                            server_process.restart_count += 1

                            success = await self.restart_server(
                                repo_path,
                                server_process.branch_name
                            )

                            if success:
                                logger.info(f"Server restarted successfully")
                            else:
                                logger.error(f"Server restart failed")
                        else:
                            logger.error(f"Max restart attempts reached, giving up")
                            await self.stop_server(repo_path)

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"Error in server monitoring: {e}", exc_info=True)
                await asyncio.sleep(self.health_check_interval)

    async def stop_all_servers(self):
        """Stop all running dev servers"""
        logger.info(f"Stopping all dev servers ({len(self.running_servers)} running)")

        for repo_path in list(self.running_servers.keys()):
            await self.stop_server(Path(repo_path))

        logger.info("All dev servers stopped")

    def get_running_servers(self) -> Dict[str, Dict]:
        """Get info about all running servers"""
        return {
            repo_key: {
                'project_type': server.config.project_type,
                'port': server.config.port,
                'url': server.config.health_check_url,
                'pid': server.pid,
                'branch': server.branch_name,
                'started_at': server.started_at.isoformat(),
                'is_healthy': server.is_healthy,
                'restart_count': server.restart_count
            }
            for repo_key, server in self.running_servers.items()
        }

    def _prepare_environment(self, config: DevServerConfig) -> dict:
        """Prepare environment variables for dev server"""
        import os

        # Start with current environment
        env = os.environ.copy()

        # Add server-specific env vars
        env.update(config.env_vars)

        # Add common dev environment variables
        env['NODE_ENV'] = env.get('NODE_ENV', 'development')

        return env

    async def _is_port_available(self, port: int) -> bool:
        """Check if port is available"""
        import socket

        try:
            # Try to bind to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()

            # If connection failed, port is available
            return result != 0

        except Exception as e:
            logger.error(f"Error checking port {port}: {e}")
            return False

    async def _wait_for_healthy(self, server_process: ServerProcess):
        """Wait for server to become healthy"""
        logger.info(f"Waiting for server to be healthy (timeout: {self.startup_timeout}s)...")

        start_time = time.time()
        last_log_time = start_time

        while time.time() - start_time < self.startup_timeout:
            # Check if process died
            if server_process.process.returncode is not None:
                logger.error(f"Server process died during startup (exit code: {server_process.process.returncode})")
                raise Exception("Server process died during startup")

            # Try health check
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        server_process.config.health_check_url,
                        timeout=aiohttp.ClientTimeout(total=3)
                    ) as response:
                        if response.status < 500:
                            logger.info(f"Server is healthy! {server_process.config.health_check_url}")
                            server_process.is_healthy = True
                            server_process.last_health_check = datetime.now()
                            return
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass

            # Log progress every 10 seconds
            if time.time() - last_log_time > 10:
                elapsed = int(time.time() - start_time)
                logger.info(f"Still waiting for server... ({elapsed}s elapsed)")
                last_log_time = time.time()

            await asyncio.sleep(2)

        logger.warning(f"Server did not become healthy within {self.startup_timeout}s")
        logger.warning(f"Server may still be starting, continuing anyway...")
