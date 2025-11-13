"""
Dev Server Detector - Auto-detect project type and dev server command.

Supports:
- Next.js, React, Vite, Vue, Angular (Node.js)
- Flask, Django, FastAPI (Python)
- Express (Node.js)
- Rails (Ruby)
- Custom commands via config
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DevServerConfig:
    """
    Configuration for a detected dev server.

    Attributes:
        project_type: Type of project (nextjs, react, flask, etc.)
        command: Command to start dev server
        port: Expected port number
        health_check_url: URL to check if server is running
        env_vars: Environment variables to set
        working_dir: Directory to run command in
    """
    project_type: str
    command: str
    port: int
    health_check_url: str
    env_vars: Dict[str, str]
    working_dir: Path


class DevServerDetector:
    """
    Detect project type and determine dev server configuration.

    Detection strategies:
    1. Check package.json for Node.js projects
    2. Check requirements.txt / pyproject.toml for Python
    3. Check Gemfile for Ruby
    4. Check for framework-specific files
    5. Use custom config if provided
    """

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize detector.

        Args:
            custom_config: Optional custom configuration overrides
        """
        self.custom_config = custom_config or {}

    def detect(self, repo_path: Path) -> Optional[DevServerConfig]:
        """
        Detect dev server configuration for repository.

        Args:
            repo_path: Path to repository

        Returns:
            DevServerConfig if detected, None otherwise
        """
        logger.info(f"Detecting dev server for {repo_path}")

        # Check custom config first
        if self.custom_config:
            custom = self._check_custom_config(repo_path)
            if custom:
                logger.info(f"Using custom config for {repo_path}")
                return custom

        # Try Node.js projects
        node_config = self._detect_nodejs(repo_path)
        if node_config:
            return node_config

        # Try Python projects
        python_config = self._detect_python(repo_path)
        if python_config:
            return python_config

        # Try Ruby projects
        ruby_config = self._detect_ruby(repo_path)
        if ruby_config:
            return ruby_config

        logger.info(f"No dev server detected for {repo_path}")
        return None

    def _check_custom_config(self, repo_path: Path) -> Optional[DevServerConfig]:
        """Check if custom config exists for this repo"""
        repo_name = repo_path.name
        repo_str = str(repo_path)

        # Check by repo name or path
        for key in [repo_name, repo_str]:
            if key in self.custom_config:
                config = self.custom_config[key]
                return DevServerConfig(
                    project_type='custom',
                    command=config.get('command', ''),
                    port=config.get('port', 3000),
                    health_check_url=config.get('health_check_url', f"http://localhost:{config.get('port', 3000)}"),
                    env_vars=config.get('env_vars', {}),
                    working_dir=repo_path
                )

        return None

    def _detect_nodejs(self, repo_path: Path) -> Optional[DevServerConfig]:
        """Detect Node.js based projects"""
        package_json = repo_path / 'package.json'

        if not package_json.exists():
            return None

        try:
            with open(package_json) as f:
                package = json.load(f)

            scripts = package.get('scripts', {})
            dependencies = package.get('dependencies', {})
            dev_dependencies = package.get('devDependencies', {})
            all_deps = {**dependencies, **dev_dependencies}

            # Next.js
            if 'next' in all_deps:
                return DevServerConfig(
                    project_type='nextjs',
                    command=scripts.get('dev', 'npm run dev'),
                    port=3000,
                    health_check_url='http://localhost:3000',
                    env_vars={},
                    working_dir=repo_path
                )

            # Vite
            if 'vite' in all_deps:
                return DevServerConfig(
                    project_type='vite',
                    command=scripts.get('dev', 'npm run dev'),
                    port=5173,
                    health_check_url='http://localhost:5173',
                    env_vars={},
                    working_dir=repo_path
                )

            # Vue CLI
            if '@vue/cli-service' in all_deps or 'vue' in all_deps:
                port = 8080
                command = scripts.get('serve', scripts.get('dev', 'npm run serve'))
                return DevServerConfig(
                    project_type='vue',
                    command=command,
                    port=port,
                    health_check_url=f'http://localhost:{port}',
                    env_vars={},
                    working_dir=repo_path
                )

            # Angular
            if '@angular/core' in all_deps:
                return DevServerConfig(
                    project_type='angular',
                    command='ng serve',
                    port=4200,
                    health_check_url='http://localhost:4200',
                    env_vars={},
                    working_dir=repo_path
                )

            # React (Create React App)
            if 'react-scripts' in all_deps:
                return DevServerConfig(
                    project_type='react',
                    command=scripts.get('start', 'npm start'),
                    port=3000,
                    health_check_url='http://localhost:3000',
                    env_vars={},
                    working_dir=repo_path
                )

            # Generic Express or Node server
            if 'express' in all_deps:
                command = scripts.get('dev', scripts.get('start', 'npm start'))
                return DevServerConfig(
                    project_type='express',
                    command=command,
                    port=3000,  # Common default
                    health_check_url='http://localhost:3000',
                    env_vars={},
                    working_dir=repo_path
                )

            # Generic Node.js with dev script
            if 'dev' in scripts:
                return DevServerConfig(
                    project_type='nodejs',
                    command=scripts['dev'],
                    port=3000,
                    health_check_url='http://localhost:3000',
                    env_vars={},
                    working_dir=repo_path
                )

        except json.JSONDecodeError:
            logger.error(f"Invalid package.json in {repo_path}")
        except Exception as e:
            logger.error(f"Error reading package.json: {e}")

        return None

    def _detect_python(self, repo_path: Path) -> Optional[DevServerConfig]:
        """Detect Python based projects"""

        # Flask detection
        if (repo_path / 'app.py').exists() or (repo_path / 'wsgi.py').exists():
            # Check if Flask is in requirements
            requirements_file = repo_path / 'requirements.txt'
            if requirements_file.exists():
                try:
                    with open(requirements_file) as f:
                        requirements = f.read().lower()

                    if 'flask' in requirements:
                        return DevServerConfig(
                            project_type='flask',
                            command='flask run --reload',
                            port=5000,
                            health_check_url='http://localhost:5000',
                            env_vars={'FLASK_ENV': 'development', 'FLASK_DEBUG': '1'},
                            working_dir=repo_path
                        )
                except Exception as e:
                    logger.error(f"Error reading requirements.txt: {e}")

        # Django detection
        if (repo_path / 'manage.py').exists():
            return DevServerConfig(
                project_type='django',
                command='python manage.py runserver',
                port=8000,
                health_check_url='http://localhost:8000',
                env_vars={},
                working_dir=repo_path
            )

        # FastAPI detection
        main_py = repo_path / 'main.py'
        if main_py.exists():
            try:
                with open(main_py) as f:
                    content = f.read()

                if 'from fastapi import' in content or 'import fastapi' in content:
                    return DevServerConfig(
                        project_type='fastapi',
                        command='uvicorn main:app --reload',
                        port=8000,
                        health_check_url='http://localhost:8000/docs',
                        env_vars={},
                        working_dir=repo_path
                    )
            except Exception as e:
                logger.error(f"Error reading main.py: {e}")

        return None

    def _detect_ruby(self, repo_path: Path) -> Optional[DevServerConfig]:
        """Detect Ruby based projects"""

        # Rails detection
        if (repo_path / 'Gemfile').exists() and (repo_path / 'config/application.rb').exists():
            return DevServerConfig(
                project_type='rails',
                command='rails server',
                port=3000,
                health_check_url='http://localhost:3000',
                env_vars={},
                working_dir=repo_path
            )

        return None

    def supports_hot_reload(self, config: DevServerConfig) -> bool:
        """Check if project type supports hot reload"""
        hot_reload_types = {
            'nextjs', 'react', 'vite', 'vue', 'angular',
            'flask', 'fastapi', 'express'
        }
        return config.project_type in hot_reload_types
