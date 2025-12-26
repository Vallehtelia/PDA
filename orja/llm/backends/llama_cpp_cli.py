from __future__ import annotations

import json
import logging
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import error, request

from orja.llm.provider import ChatMessage, LLMProvider

logger = logging.getLogger(__name__)


class LlamaCppCliProvider(LLMProvider):
    """LLM provider that uses llama.cpp CLI via subprocess."""

    _server_proc: Optional[subprocess.Popen] = None
    _server_host: str = "127.0.0.1"
    _server_port: int = 8080

    def __init__(self, config: Dict[str, Any]) -> None:
        self.llama_config = config.get("llama_cpp", {})
        self.system_prompt = config.get("system_prompt", "")
        self.history_messages = config.get("history_messages", 6)

        # Extract llama.cpp parameters
        self.bin_path = Path(self.llama_config.get("bin_path", ""))
        self.model_path = Path(self.llama_config.get("model_path", ""))
        self.threads = self.llama_config.get("threads", 4)
        self.ctx_size = self.llama_config.get("ctx_size", 2048)
        self.max_tokens = self.llama_config.get("max_tokens", 160)
        self.temperature = self.llama_config.get("temperature", 0.7)
        self.top_p = self.llama_config.get("top_p", 0.9)
        self.repeat_penalty = self.llama_config.get("repeat_penalty", 1.1)
        self.batch_size = self.llama_config.get("batch_size", 256)
        self.timeout_sec = self.llama_config.get("timeout_sec", 45)
        self.server_enabled = self.llama_config.get("server", {}).get("enabled", False)
        self.server_host = self.llama_config.get("server", {}).get("host", "127.0.0.1")
        self.server_port = int(self.llama_config.get("server", {}).get("port", 8080))
        self.server_bin_path = Path(
            self.llama_config.get("server_bin_path")
            or self.bin_path.parent / "llama-server"
        )

        if self.server_enabled:
            self._ensure_server()

    def _build_prompt(
        self, messages: List[ChatMessage], *, system_prompt: Optional[str] = None
    ) -> str:
        """Build chat format prompt from messages."""
        applied_system = system_prompt if system_prompt is not None else self.system_prompt
        system_msg = f"<|im_start|>system\n{applied_system}<|im_end|>\n"

        conversation = ""
        for msg in messages:
            if msg.role == "user":
                conversation += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
            elif msg.role == "assistant":
                conversation += f"<|im_start|>assistant\n{msg.content}<|im_end|>\n"

        conversation += "<|im_start|>assistant\n"
        return system_msg + conversation

    def _run_llama_cli(self, prompt: str, *, max_tokens: int, temperature: float, top_p: float, repeat_penalty: float) -> str:
        """Run llama-cli with the given prompt and return response."""
        if not self.bin_path.exists():
            raise FileNotFoundError(f"llama-cli binary not found at: {self.bin_path}")
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found at: {self.model_path}")

        cmd = [
            str(self.bin_path),
            "--model",
            str(self.model_path),
            "--prompt",
            prompt,
            "--threads",
            str(self.threads),
            "--ctx-size",
            str(self.ctx_size),
            "--n-predict",
            str(max_tokens),
            "--temp",
            str(temperature),
            "--top-p",
            str(top_p),
            "--repeat-penalty",
            str(repeat_penalty),
            "--batch-size",
            str(self.batch_size),
            "--simple-io",
        ]

        logger.debug("Running llama-cli command: %s", " ".join(cmd[:-1]) + " --simple-io")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout_sec,
        )

        if result.returncode != 0:
            error_msg = f"llama-cli failed with code {result.returncode}: {result.stderr}"
            logger.error(error_msg)
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )

        return result.stdout.strip()

    def _ensure_server(self) -> None:
        """Start llama-server if not already running."""
        # If already running and reachable, keep it.
        if self._server_proc and self._server_proc.poll() is None:
            if self._server_ready():
                return

        if not self.server_bin_path.exists():
            raise FileNotFoundError(
                f"llama-server binary not found at: {self.server_bin_path}"
            )
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found at: {self.model_path}")

        cmd = [
            str(self.server_bin_path),
            "--model",
            str(self.model_path),
            "--host",
            self.server_host,
            "--port",
            str(self.server_port),
            "--ctx-size",
            str(self.ctx_size),
            "--threads",
            str(self.threads),
            "--batch-size",
            str(self.batch_size),
        ]

        logger.info(
            "Starting llama-server on %s:%s using model %s",
            self.server_host,
            self.server_port,
            self.model_path,
        )
        self._server_proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self._server_host = self.server_host
        self._server_port = self.server_port

        # Wait for server to be ready
        start = time.time()
        while time.time() - start < self.timeout_sec:
            if self._server_ready():
                logger.info("llama-server is ready at %s:%s", self.server_host, self.server_port)
                return
            time.sleep(0.5)

        raise TimeoutError(
            f"llama-server did not become ready within {self.timeout_sec} seconds"
        )

    def _server_ready(self) -> bool:
        try:
            with socket.create_connection(
                (self.server_host, self.server_port), timeout=1
            ):
                return True
        except OSError:
            return False

    def _run_server_completion(
        self,
        prompt: str,
        *,
        max_tokens: int,
        temperature: float,
        top_p: float,
        repeat_penalty: float,
    ) -> str:
        """Send completion request to llama-server."""
        if not self._server_ready():
            self._ensure_server()

        url = f"http://{self.server_host}:{self.server_port}/completion"
        payload = {
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "repeat_penalty": repeat_penalty,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_sec) as resp:
                body = resp.read().decode("utf-8")
                parsed = json.loads(body)
                # server returns {"content": "..."} or {"completion": "..."}
                if isinstance(parsed, dict):
                    if "content" in parsed:
                        return parsed["content"].strip()
                    if "completion" in parsed:
                        return parsed["completion"].strip()
                return str(parsed)
        except error.HTTPError as exc:
            raise RuntimeError(f"Server HTTP error: {exc}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Server URL error: {exc}") from exc

    def generate(
        self,
        messages: List[ChatMessage],
        *,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        json_mode: Optional[bool] = None,
    ) -> str:
        """Generate response from messages using llama.cpp CLI."""
        _ = json_mode  # reserved for future JSON-mode integrations
        try:
            recent_messages = messages[-self.history_messages :] if messages else []
            prompt = self._build_prompt(recent_messages, system_prompt=system_prompt)
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            temp = temperature if temperature is not None else self.temperature
            top_p_val = top_p if top_p is not None else self.top_p
            repeat_penalty = self.repeat_penalty
            if self.server_enabled:
                response = self._run_server_completion(
                    prompt,
                    max_tokens=tokens,
                    temperature=temp,
                    top_p=top_p_val,
                    repeat_penalty=repeat_penalty,
                )
            else:
                response = self._run_llama_cli(
                    prompt,
                    max_tokens=tokens,
                    temperature=temp,
                    top_p=top_p_val,
                    repeat_penalty=repeat_penalty,
                )

            if response.startswith(prompt):
                response = response[len(prompt) :].strip()
            response = response.split("<|im_end|>")[0].strip()
            response = response.split("<|im_start|>")[0].strip()
            return response if response else "I don't have an answer for that."

        except FileNotFoundError as err:
            logger.error("LLM provider error: %s", err)
            return self._fallback_response(messages)
        except subprocess.TimeoutExpired:
            logger.error("LLM provider timeout after %ss", self.timeout_sec)
            return "The response took too long. Please try again."
        except subprocess.CalledProcessError as err:
            logger.error("LLM provider subprocess error: %s", err)
            return self._fallback_response(messages)
        except Exception as err:  # pragma: no cover - defensive
            logger.error("Unexpected LLM provider error: %s", err)
            return self._fallback_response(messages)

    def _fallback_response(self, messages: List[ChatMessage]) -> str:
        """Fallback response when llama.cpp fails."""
        user_msg = messages[-1].content if messages else "unknown question"
        return (
            "Local response (llama.cpp failed): "
            f"{user_msg[:100]}... Providing a brief fallback."
        )

