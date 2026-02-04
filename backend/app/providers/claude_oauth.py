"""Claude OAuth Provider using Claude Code CLI.

Uses Claude Max subscription via OAuth authentication.
No API key required - uses locally stored OAuth tokens from `claude login`.

IMPORTANT: Claude CLI requires a PTY (pseudo-terminal) to output properly.
This provider uses pty.spawn() or script command to handle this.
"""

import asyncio
import json
import logging
import os
import pty
import re
import select
import subprocess
from pathlib import Path
from typing import AsyncIterator, List, Optional, Dict, Any

from app.providers.base import (
    BaseProvider,
    ProviderConfig,
    Message,
    Role,
    CompletionResponse,
    StreamEvent,
)

logger = logging.getLogger(__name__)


class ClaudeOAuthProvider(BaseProvider):
    """
    Provider that uses Claude Code CLI with OAuth authentication.
    
    This allows using Claude Max subscription ($20/month unlimited)
    instead of pay-as-you-go API costs.
    
    Requirements:
    - Claude Code CLI installed: `npm install -g @anthropic-ai/claude-code`
    - Logged in via: `claude login`
    - OAuth tokens stored in ~/.claude/
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.claude_config_dir = config.extra.get(
            "claude_config_dir",
            os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude"))
        )
        self._cli_available: Optional[bool] = None
        self._oauth_available: Optional[bool] = None

    @property
    def provider_type(self) -> str:
        return "claude-code"

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_tools(self) -> bool:
        # Claude CLI has built-in tools (Read, Write, Edit, Bash)
        return True

    def _check_cli_available(self) -> bool:
        """Check if Claude CLI is installed."""
        if self._cli_available is not None:
            return self._cli_available
        
        import shutil
        self._cli_available = shutil.which("claude") is not None
        return self._cli_available

    def _check_oauth_available(self) -> bool:
        """Check if OAuth credentials exist."""
        if self._oauth_available is not None:
            return self._oauth_available
            
        try:
            creds_file = Path(self.claude_config_dir) / ".credentials.json"
            if not creds_file.exists():
                self._oauth_available = False
                return False
                
            with open(creds_file) as f:
                creds = json.load(f)
            
            oauth_data = creds.get("claudeAiOauth", {})
            self._oauth_available = bool(oauth_data.get("accessToken"))
            return self._oauth_available
            
        except Exception as e:
            logger.warning(f"Failed to check OAuth credentials: {e}")
            self._oauth_available = False
            return False

    def _build_prompt(
        self,
        messages: List[Message],
        system: Optional[str] = None,
    ) -> str:
        """Build a prompt string from messages."""
        parts = []
        
        if system:
            parts.append(f"<system>\n{system}\n</system>\n")
        
        for msg in messages:
            if msg.role == Role.USER:
                parts.append(f"<user>\n{msg.content}\n</user>")
            elif msg.role == Role.ASSISTANT:
                parts.append(f"<assistant>\n{msg.content}\n</assistant>")
        
        return "\n".join(parts)

    def _run_cli_with_pty(self, cmd: List[str], env: dict, timeout: int) -> str:
        """
        Run Claude CLI with PTY support using Python's pty module.
        
        Claude CLI requires a TTY to output properly.
        """
        import errno
        import signal
        
        # Create environment
        full_env = {**os.environ, **env}
        
        output_chunks = []
        
        def read_pty_output(fd, timeout_seconds):
            """Read output from PTY until EOF or timeout."""
            import time
            start_time = time.time()
            
            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    raise RuntimeError(f"PTY read timeout after {timeout_seconds}s")
                
                # Check if data is available
                try:
                    r, _, _ = select.select([fd], [], [], 1.0)
                    if fd in r:
                        try:
                            data = os.read(fd, 4096)
                            if not data:
                                break  # EOF
                            output_chunks.append(data)
                        except OSError as e:
                            if e.errno == errno.EIO:
                                break  # PTY closed
                            raise
                except select.error:
                    break
        
        logger.info(f"Running CLI with native PTY: {cmd[0]}...")
        
        try:
            # Create a pseudo-terminal
            master_fd, slave_fd = pty.openpty()
            
            # Fork and execute
            pid = os.fork()
            
            if pid == 0:
                # Child process
                os.close(master_fd)
                os.setsid()
                
                # Set up slave as controlling terminal
                os.dup2(slave_fd, 0)
                os.dup2(slave_fd, 1)
                os.dup2(slave_fd, 2)
                
                if slave_fd > 2:
                    os.close(slave_fd)
                
                # Execute command
                os.execvpe(cmd[0], cmd, full_env)
            else:
                # Parent process
                os.close(slave_fd)
                
                # Read output with timeout
                try:
                    read_pty_output(master_fd, timeout)
                except Exception as e:
                    logger.warning(f"PTY read error: {e}")
                finally:
                    os.close(master_fd)
                
                # Wait for child with timeout
                try:
                    _, status = os.waitpid(pid, 0)
                    exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
                    logger.info(f"CLI exit code: {exit_code}")
                except ChildProcessError:
                    pass
            
            # Decode output
            output = b''.join(output_chunks).decode('utf-8', errors='replace')
            
            # Remove ANSI escape codes
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_output = ansi_escape.sub('', output)
            
            # Remove control characters but keep newlines
            clean_output = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', clean_output)
            
            return clean_output.strip()
            
        except Exception as e:
            logger.error(f"PTY execution failed: {e}")
            raise

    async def complete(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs,
    ) -> CompletionResponse:
        """Generate completion using Claude CLI with PTY support."""
        if not self._check_cli_available():
            raise RuntimeError("Claude CLI not installed. Run: npm install -g @anthropic-ai/claude-code")
        
        if not self._check_oauth_available():
            raise RuntimeError("OAuth not configured. Run: claude login")

        prompt = self._build_prompt(messages, system)
        
        # Build command
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "--print",
            "--output-format", "text",  # Use text format, easier to parse
        ]
        
        # Add model if specified
        if self.model:
            cmd.extend(["--model", self.model])
        
        # Add allowed tools if specified
        allowed_tools = kwargs.get("allowed_tools", self.config.allowed_tools)
        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])
        
        # Prompt goes at the end
        cmd.append(prompt)

        logger.info(f"Executing Claude CLI with PTY support...")
        
        env = {"CLAUDE_CONFIG_DIR": self.claude_config_dir}
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            content = await loop.run_in_executor(
                None,
                self._run_cli_with_pty,
                cmd,
                env,
                self.timeout,
            )
            
            logger.info(f"Claude CLI returned {len(content)} chars")
            
            if not content:
                logger.warning("Claude CLI returned empty content")
            
            return CompletionResponse(
                content=content,
                model=self.model,
                tokens_used=None,  # CLI doesn't report tokens
                finish_reason="stop",
            )
            
        except Exception as e:
            logger.error(f"Claude CLI failed: {e}")
            raise RuntimeError(f"Claude CLI error: {e}")

    async def stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[StreamEvent]:
        """
        Stream completion using Claude CLI.
        
        Note: True streaming with PTY is complex. For now, we use
        the complete() method and yield the result as chunks.
        This provides the same interface while ensuring PTY compatibility.
        """
        try:
            # Use complete() which handles PTY properly
            response = await self.complete(messages, system, **kwargs)
            
            # Yield the content in chunks to simulate streaming
            content = response.content
            chunk_size = 100  # Characters per chunk
            
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield StreamEvent(type="text_delta", content=chunk)
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)
            
            yield StreamEvent(type="done")
            
        except Exception as e:
            yield StreamEvent(type="error", error=str(e))

    async def _stream_legacy(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[StreamEvent]:
        """Legacy streaming method (doesn't work without PTY)."""
        if not self._check_cli_available():
            yield StreamEvent(type="error", error="Claude CLI not installed")
            return
        
        if not self._check_oauth_available():
            yield StreamEvent(type="error", error="OAuth not configured. Run: claude login")
            return

        prompt = self._build_prompt(messages, system)
        
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "--print", prompt,
            "--output-format", "stream-json",
        ]
        
        if self.model:
            cmd.extend(["--model", self.model])
        
        allowed_tools = kwargs.get("allowed_tools", self.config.allowed_tools)
        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])

        try:
            env = {
                **os.environ,
                "CLAUDE_CONFIG_DIR": self.claude_config_dir,
            }
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            
            async def read_stream():
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    
                    try:
                        data = json.loads(line.decode().strip())
                        event_type = data.get("type", "")
                        
                        if event_type == "assistant" and "message" in data:
                            # Extract text content
                            msg = data["message"]
                            if isinstance(msg, dict) and "content" in msg:
                                for block in msg.get("content", []):
                                    if block.get("type") == "text":
                                        yield StreamEvent(
                                            type="text_delta",
                                            content=block.get("text", ""),
                                        )
                        elif event_type == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield StreamEvent(
                                    type="text_delta",
                                    content=delta.get("text", ""),
                                )
                        elif event_type == "result":
                            # Final result
                            if "result" in data:
                                yield StreamEvent(
                                    type="text_delta",
                                    content=data["result"],
                                )
                            yield StreamEvent(type="done")
                            
                    except json.JSONDecodeError:
                        # Plain text output
                        text = line.decode().strip()
                        if text:
                            yield StreamEvent(type="text_delta", content=text)
            
            async for event in read_stream():
                yield event
            
            await process.wait()
            
            if process.returncode != 0:
                stderr = await process.stderr.read()
                yield StreamEvent(
                    type="error",
                    error=stderr.decode().strip() if stderr else "CLI error",
                )
            else:
                yield StreamEvent(type="done")
                
        except asyncio.TimeoutError:
            yield StreamEvent(type="error", error=f"Timeout after {self.timeout}s")
        except Exception as e:
            yield StreamEvent(type="error", error=str(e))

    async def health_check(self) -> bool:
        """Check if OAuth provider is available."""
        cli_ok = self._check_cli_available()
        oauth_ok = self._check_oauth_available()
        logger.info(f"OAuth health check: cli_available={cli_ok}, oauth_available={oauth_ok}")
        return cli_ok and oauth_ok
