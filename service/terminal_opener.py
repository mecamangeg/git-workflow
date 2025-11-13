"""
Terminal Opener - Cross-platform terminal opening utility.

Opens terminal in specified directory with optional command execution.
Supports Windows, macOS, and Linux with multiple terminal emulators.
"""

import logging
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TerminalConfig:
    """Terminal configuration"""
    preferred_terminal: Optional[str] = None
    fallback_terminals: List[str] = None

    def __post_init__(self):
        if self.fallback_terminals is None:
            self.fallback_terminals = []


class TerminalOpener:
    """
    Cross-platform terminal opener.

    Supports:
    - Windows: Windows Terminal, PowerShell, cmd
    - macOS: Terminal.app, iTerm2
    - Linux: gnome-terminal, konsole, xfce4-terminal, xterm
    """

    def __init__(self, config: Optional[TerminalConfig] = None):
        """
        Initialize terminal opener.

        Args:
            config: Optional terminal configuration
        """
        self.config = config or TerminalConfig()
        self.system = platform.system()

    def open_terminal(
        self,
        working_dir: Path,
        command: Optional[str] = None,
        title: Optional[str] = None
    ) -> bool:
        """
        Open terminal in specified directory.

        Args:
            working_dir: Directory to open terminal in
            command: Optional command to execute after opening
            title: Optional window title

        Returns:
            True if terminal opened successfully, False otherwise
        """
        working_dir = Path(working_dir).resolve()

        if not working_dir.exists():
            logger.error(f"Directory does not exist: {working_dir}")
            return False

        logger.info(f"Opening terminal in {working_dir}")

        try:
            if self.system == 'Windows':
                return self._open_windows_terminal(working_dir, command, title)
            elif self.system == 'Darwin':
                return self._open_macos_terminal(working_dir, command, title)
            else:  # Linux and others
                return self._open_linux_terminal(working_dir, command, title)
        except Exception as e:
            logger.error(f"Failed to open terminal: {e}", exc_info=True)
            return False

    def _open_windows_terminal(
        self,
        working_dir: Path,
        command: Optional[str],
        title: Optional[str]
    ) -> bool:
        """Open terminal on Windows"""

        # Try Windows Terminal first (modern)
        if self._has_command('wt') or self.config.preferred_terminal == 'wt':
            try:
                args = ['wt', '-d', str(working_dir)]

                if title:
                    args.extend(['--title', title])

                if command:
                    args.extend([';', 'powershell', '-NoExit', '-Command', command])

                subprocess.Popen(args, cwd=working_dir)
                logger.info("Opened Windows Terminal")
                return True
            except Exception as e:
                logger.debug(f"Windows Terminal failed: {e}")

        # Try PowerShell
        if self._has_command('powershell') or self.config.preferred_terminal == 'powershell':
            try:
                if command:
                    args = [
                        'powershell',
                        '-NoExit',
                        '-Command',
                        f'cd "{working_dir}"; {command}'
                    ]
                else:
                    args = ['powershell', '-NoExit', '-Command', f'cd "{working_dir}"']

                subprocess.Popen(args)
                logger.info("Opened PowerShell")
                return True
            except Exception as e:
                logger.debug(f"PowerShell failed: {e}")

        # Fallback to cmd
        try:
            if command:
                args = ['cmd', '/k', f'cd /d "{working_dir}" && {command}']
            else:
                args = ['cmd', '/k', f'cd /d "{working_dir}"']

            subprocess.Popen(args)
            logger.info("Opened cmd")
            return True
        except Exception as e:
            logger.error(f"All Windows terminal options failed: {e}")
            return False

    def _open_macos_terminal(
        self,
        working_dir: Path,
        command: Optional[str],
        title: Optional[str]
    ) -> bool:
        """Open terminal on macOS"""

        # Try iTerm2 first if preferred
        if self.config.preferred_terminal == 'iterm':
            try:
                script = f'''
                tell application "iTerm"
                    create window with default profile
                    tell current session of current window
                        write text "cd '{working_dir}'"
                        {f'write text "{command}"' if command else ''}
                    end tell
                end tell
                '''
                subprocess.Popen(['osascript', '-e', script])
                logger.info("Opened iTerm2")
                return True
            except Exception as e:
                logger.debug(f"iTerm2 failed: {e}")

        # Default to Terminal.app
        try:
            # Create AppleScript to open Terminal and cd to directory
            script_parts = [
                'tell application "Terminal"',
                '    activate',
                f'    do script "cd \\"{working_dir}\\""',
            ]

            if command:
                script_parts.append(f'    do script "{command}" in front window')

            script_parts.append('end tell')
            script = '\n'.join(script_parts)

            subprocess.Popen(['osascript', '-e', script])
            logger.info("Opened Terminal.app")
            return True
        except Exception as e:
            logger.error(f"macOS Terminal failed: {e}")
            return False

    def _open_linux_terminal(
        self,
        working_dir: Path,
        command: Optional[str],
        title: Optional[str]
    ) -> bool:
        """Open terminal on Linux"""

        # List of terminals to try (in order)
        terminals = []

        if self.config.preferred_terminal:
            terminals.append(self.config.preferred_terminal)

        terminals.extend([
            'gnome-terminal',
            'konsole',
            'xfce4-terminal',
            'mate-terminal',
            'lxterminal',
            'xterm',
        ])

        for terminal in terminals:
            if not self._has_command(terminal):
                continue

            try:
                if terminal == 'gnome-terminal':
                    args = ['gnome-terminal', '--working-directory', str(working_dir)]
                    if title:
                        args.extend(['--title', title])
                    if command:
                        args.extend(['--', 'bash', '-c', f'{command}; exec bash'])

                elif terminal == 'konsole':
                    args = ['konsole', '--workdir', str(working_dir)]
                    if title:
                        args.extend(['--title', title])
                    if command:
                        args.extend(['-e', 'bash', '-c', f'{command}; exec bash'])

                elif terminal in ['xfce4-terminal', 'mate-terminal', 'lxterminal']:
                    args = [terminal, '--working-directory', str(working_dir)]
                    if title:
                        args.extend(['--title', title])
                    if command:
                        args.extend(['-e', f'bash -c "{command}; exec bash"'])

                elif terminal == 'xterm':
                    if command:
                        args = ['xterm', '-e', f'cd "{working_dir}" && {command} && bash']
                    else:
                        args = ['xterm', '-e', f'cd "{working_dir}" && bash']

                else:
                    # Generic fallback
                    args = [terminal, '--working-directory', str(working_dir)]
                    if command:
                        args.extend(['-e', f'bash -c "{command}; exec bash"'])

                subprocess.Popen(args)
                logger.info(f"Opened {terminal}")
                return True

            except Exception as e:
                logger.debug(f"{terminal} failed: {e}")
                continue

        logger.error("No working terminal emulator found on Linux")
        return False

    def _has_command(self, command: str) -> bool:
        """Check if command is available in PATH"""
        return shutil.which(command) is not None

    def get_available_terminals(self) -> List[str]:
        """Get list of available terminal emulators on this system"""
        available = []

        if self.system == 'Windows':
            candidates = ['wt', 'powershell', 'cmd']
        elif self.system == 'Darwin':
            candidates = ['Terminal', 'iTerm']
            # macOS always has Terminal.app
            return ['Terminal']
        else:  # Linux
            candidates = [
                'gnome-terminal', 'konsole', 'xfce4-terminal',
                'mate-terminal', 'lxterminal', 'xterm'
            ]

        for cmd in candidates:
            if self._has_command(cmd):
                available.append(cmd)

        return available
