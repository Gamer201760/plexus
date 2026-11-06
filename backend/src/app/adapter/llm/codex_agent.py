import json
import tempfile
from collections.abc import Mapping

from openai_codex import ApprovalMode, AsyncCodex, CodexConfig, CodexError, Sandbox, TurnResult
from openai_codex.types import ReasoningEffort, TurnStatus

from app.domain.errors import ModelFailure
from app.domain.inference import Completion, StructuredRequest, Tier, Usage

DEFAULT_MODELS = {Tier.FAST: "gpt-6-luna", Tier.SMART: "gpt-6.1-sol"}
ISOLATION_OVERRIDES = (
    "features.shell_tool=false",
    "features.unified_exec=false",
    "features.view_image=false",
    'web_search="disabled"',
    "project_doc_max_bytes=0",
)


class CodexAgentModel:
    def __init__(self, models: Mapping[Tier, str] = DEFAULT_MODELS) -> None:
        self._models = dict(models)

    async def _run(self, request: StructuredRequest, cwd: str) -> TurnResult:
        config = CodexConfig(config_overrides=ISOLATION_OVERRIDES, cwd=cwd)
        async with AsyncCodex(config) as codex:
            thread = await codex.thread_start(
                approval_mode=ApprovalMode.deny_all,
                base_instructions=request.system,
                cwd=cwd,
                ephemeral=True,
                model=self._models[request.tier],
                sandbox=Sandbox.read_only,
            )
            return await thread.run(
                request.prompt,
                effort=ReasoningEffort(request.effort.value) if request.effort else None,
                output_schema=request.schema,
            )

    async def complete(self, request: StructuredRequest) -> Completion:
        try:
            with tempfile.TemporaryDirectory(prefix="llm-agent-") as cwd:
                result = await self._run(request, cwd)
        except (CodexError, RuntimeError) as exc:
            raise ModelFailure(f"Language model failed: {exc}") from exc
        if result.status != TurnStatus.completed or result.final_response is None:
            reason = result.error.message if result.error else result.status.value
            raise ModelFailure(f"Language model failed: {reason}")
        try:
            output = json.loads(result.final_response)
        except json.JSONDecodeError as exc:
            raise ModelFailure(f"Language model failed: {exc}") from exc
        if not isinstance(output, dict):
            raise ModelFailure("Language model failed: output is not an object")
        tokens = result.usage.total if result.usage else None
        return Completion(
            output=output,
            usage=Usage(
                model=self._models[request.tier],
                duration_ms=result.duration_ms or 0,
                input_tokens=tokens.input_tokens if tokens else None,
                output_tokens=tokens.output_tokens if tokens else None,
            ),
        )
