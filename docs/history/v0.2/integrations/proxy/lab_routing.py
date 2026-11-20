"""Selectively apply the maintained Switchyard Stage plugin to two-model groups.

All fixed lab groups contain exactly one deployment. The authored config is
validated by validate_config.py so a routed group can never silently become a
single-model fixed group. Logging contains routing metadata only, never prompts.
"""

import base64
import json
import logging

from switchyard_litellm import StageRoutingPlugin
from switchyard_litellm.plugins.lite_llm_request_rewriter import LiteLLMRequestRewriter

LOGGER = logging.getLogger("learning_lab.routing")


class LabRoutingPlugin(LiteLLMRequestRewriter):
    def __init__(self):
        super().__init__()
        self.stage = StageRoutingPlugin(
            picker="efficient_first",
            confidence_threshold=0.5,
            recent_window=3,
            only_on_wrong_signal_escalation=True,
        )

    async def run(self, context):
        count = len(set(context.candidate_models))
        if count == 1:
            context.signals["learning_lab"] = {"route": "fixed", "candidate_count": 1}
            return context
        if count != 2:
            raise ValueError("The lab routing group must have exactly two distinct candidates")
        result = await self.stage.run(context)
        decision = result.signals.get("switchyard", {})
        public_decision = {
            key: value
            for key, value in decision.items()
            if key not in {"request_patch", "messages", "prompt", "request", "response", "content"}
        }
        LOGGER.info(
            json.dumps(
                {
                    "event": "switchyard_decision",
                    "policy": "stage",
                    "decision": public_decision,
                }
            )
        )
        return result

    async def async_post_call_response_headers_hook(
        self, data, user_api_key_dict, response, request_headers=None, litellm_call_info=None
    ):
        """Return native decision metadata on this response, without any prompt.

        LiteLLM's public callback receives the routing metadata persisted by its
        Router plugin boundary. Missing evidence stays missing; configuration
        cannot synthesize a Switchyard decision.
        """
        del user_api_key_dict, response, request_headers
        evidence = None
        for key in ("litellm_metadata", "metadata"):
            metadata = data.get(key)
            if not isinstance(metadata, dict):
                continue
            signals = metadata.get("routing_plugin_signals")
            if isinstance(signals, dict) and isinstance(signals.get("switchyard"), dict):
                evidence = signals["switchyard"]
                break
        if evidence is None:
            return None
        # The upstream decision structure contains a request patch in some
        # algorithms. Only scalar decision fields are safe browser evidence.
        allowed = {
            key: value
            for key, value in evidence.items()
            if key not in {"request_patch", "messages", "prompt", "request", "response", "content"}
            and isinstance(value, (str, int, float, bool, type(None)))
        }
        if litellm_call_info and litellm_call_info.get("model_id"):
            allowed["deployment_id"] = str(litellm_call_info["model_id"])
        payload = json.dumps(
            {"version": 1, "source": "switchyard", "decision": allowed}, separators=(",", ":")
        )
        if len(payload.encode()) > 3000:
            raise ValueError("Switchyard decision metadata exceeded its bounded evidence envelope")
        return {"x-lab-routing-decision": base64.urlsafe_b64encode(payload.encode()).decode()}


ROUTING_PLUGIN = LabRoutingPlugin()
