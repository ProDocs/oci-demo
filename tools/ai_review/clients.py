from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

from .models import ReviewContext, ReviewPayload
from .prompt_builder import build_messages, build_prompt_parts
from .rules import review_with_mock_rules


class ReviewClient(ABC):

    @abstractmethod
    def review(self, context: ReviewContext) -> ReviewPayload:
        raise NotImplementedError


class MockReviewClient(ReviewClient):

    def __init__(self, scenario: str = "auto") -> None:
        self.scenario = (scenario or "auto").upper()

    def review(self, context: ReviewContext) -> ReviewPayload:
        print(
            f"[AI_REVIEW] client=mock scenario={self.scenario} "
            f"source_files={len(context.source_files)}",
            file=sys.stderr,
            flush=True,
        )
        if self.scenario == "PASS":
            return ReviewPayload.from_values(
                "PASS",
                "Cenario mock PASS: o codigo aderiu as guidelines arquiteturais.",
            )
        if self.scenario == "WARN":
            return ReviewPayload.from_values(
                "WARN",
                "Cenario mock WARN: nao houve violacao clara, mas existem pontos pequenos para revisar antes do merge final.",
            )
        if self.scenario == "BLOCK":
            return ReviewPayload.from_values(
                "BLOCK",
                "Cenario mock BLOCK: foi detectada uma violacao arquitetural clara e o build deve parar antes da compilacao.",
            )

        return review_with_mock_rules(context.source_files)


class OciSdkReviewClient(ReviewClient):

    def __init__(
        self,
        inference_endpoint: str,
        compartment_id: str,
        model: str,
        auth_mode: str,
        config_file: str = "",
        config_profile: str = "DEFAULT",
    ) -> None:
        self.inference_endpoint = inference_endpoint.rstrip("/")
        self.compartment_id = compartment_id
        self.model = model
        self.auth_mode = auth_mode
        self.config_file = config_file
        self.config_profile = config_profile

    def review(self, context: ReviewContext) -> ReviewPayload:
        print(
            "[AI_REVIEW] client=oci-sdk "
            f"auth_mode={self.auth_mode} "
            f"model={self.model} "
            f"inference_endpoint={self.inference_endpoint} "
            f"source_files={len(context.source_files)}",
            file=sys.stderr,
            flush=True,
        )
        oci = _import_oci_sdk()
        client = _build_oci_inference_client(
            oci=oci,
            inference_endpoint=self.inference_endpoint,
            auth_mode=self.auth_mode,
            config_file=self.config_file,
            config_profile=self.config_profile,
        )

        system_prompt, user_prompt = build_prompt_parts(context)
        models = oci.generative_ai_inference.models
        chat_request = models.GenericChatRequest(
            api_format=models.GenericChatRequest.API_FORMAT_GENERIC,
            messages=[
                models.SystemMessage(content=[models.TextContent(text=system_prompt)]),
                models.UserMessage(content=[models.TextContent(text=user_prompt)]),
            ],
            temperature=0,
            max_tokens=400,
        )
        chat_details = models.ChatDetails(
            compartment_id=self.compartment_id,
            serving_mode=models.OnDemandServingMode(model_id=self.model),
            chat_request=chat_request,
        )

        print("[AI_REVIEW] invoking OCI Generative AI chat", file=sys.stderr, flush=True)
        response = client.chat(chat_details)
        _log_oci_sdk_response_metadata(response)
        print("[AI_REVIEW] OCI Generative AI chat completed", file=sys.stderr, flush=True)
        assistant_text = _extract_text_from_oci_sdk_response(response.data)
        return _parse_review_payload(assistant_text)


class OciOpenAiCompatibleReviewClient(ReviewClient):

    def __init__(self, endpoint: str, api_key: str, model: str, timeout_seconds: int = 60) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def review(self, context: ReviewContext) -> ReviewPayload:
        print(
            "[AI_REVIEW] client=oci-openai-compatible "
            f"model={self.model} "
            f"endpoint={self.endpoint} "
            f"source_files={len(context.source_files)}",
            file=sys.stderr,
            flush=True,
        )
        payload = {
            "model": self.model,
            "messages": build_messages(context),
            "temperature": 0,
            "max_tokens": 400,
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            print("[AI_REVIEW] invoking OCI OpenAI-compatible chat", file=sys.stderr, flush=True)
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                _log_openai_compatible_response_metadata(response)
                raw_body = response.read().decode("utf-8")
            print("[AI_REVIEW] OCI OpenAI-compatible chat completed", file=sys.stderr, flush=True)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OCI GenAI retornou HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Falha ao conectar no endpoint OCI GenAI: {exc.reason}") from exc

        parsed_response = json.loads(raw_body)
        assistant_text = _extract_text_from_openai_compatible_response(parsed_response)
        return _parse_review_payload(assistant_text)


def _import_oci_sdk():
    try:
        import oci
    except ImportError as exc:
        raise RuntimeError(
            "OCI Python SDK nao encontrado no ambiente atual. "
            "Adicione `python3 -m pip install oci` ao build_spec ou disponibilize o pacote no PYTHONPATH. "
            "Localmente, instale com `python3 -m pip install oci`."
        ) from exc

    return oci


def _build_oci_inference_client(oci, inference_endpoint: str, auth_mode: str, config_file: str, config_profile: str):
    if auth_mode == "resource_principal":
        signer = oci.auth.signers.get_resource_principals_signer()
        return oci.generative_ai_inference.GenerativeAiInferenceClient(
            config={},
            signer=signer,
            service_endpoint=inference_endpoint,
        )

    if auth_mode == "instance_principal":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        return oci.generative_ai_inference.GenerativeAiInferenceClient(
            config={},
            signer=signer,
            service_endpoint=inference_endpoint,
        )

    if auth_mode == "user_principal":
        config_kwargs = {"profile_name": config_profile}
        if config_file:
            config_kwargs["file_location"] = config_file
        config = oci.config.from_file(**config_kwargs)
        return oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=config,
            service_endpoint=inference_endpoint,
        )

    raise RuntimeError(f"Modo de autenticacao OCI GenAI nao suportado: {auth_mode}")


def _extract_text_from_openai_compatible_response(response_body: dict) -> str:
    choices = response_body.get("choices") or []
    if not choices:
        raise RuntimeError("Resposta OCI GenAI sem choices.")

    message = choices[0].get("message") or {}
    content = message.get("content")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                    continue

                nested_text = item.get("content")
                if isinstance(nested_text, str):
                    parts.append(nested_text)
        joined = "\n".join(part for part in parts if part)
        if joined:
            return joined

    if "output_text" in response_body and isinstance(response_body["output_text"], str):
        return response_body["output_text"]

    raise RuntimeError("Nao foi possivel extrair o texto da resposta OCI GenAI.")


def _extract_text_from_oci_sdk_response(chat_result) -> str:
    chat_response = getattr(chat_result, "chat_response", None)
    if chat_response is None:
        raise RuntimeError("Resposta OCI SDK sem chat_response.")

    choices = getattr(chat_response, "choices", None) or []
    if not choices:
        raise RuntimeError("Resposta OCI SDK sem choices.")

    first_choice = choices[0]
    direct_text = getattr(first_choice, "text", None)
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text

    message = getattr(first_choice, "message", None)
    if message is not None:
        content_items = getattr(message, "content", None) or []
        text_parts = []
        for item in content_items:
            text = getattr(item, "text", None)
            if isinstance(text, str) and text.strip():
                text_parts.append(text)

        if text_parts:
            return "\n".join(text_parts)

    raise RuntimeError("Nao foi possivel extrair texto da resposta OCI SDK.")


def _log_oci_sdk_response_metadata(response) -> None:
    status = getattr(response, "status", None)
    request_id = getattr(response, "request_id", None)
    headers = getattr(response, "headers", None) or {}

    if not request_id and isinstance(headers, dict):
        for key, value in headers.items():
            if str(key).lower() == "opc-request-id":
                request_id = value
                break

    print(
        "[AI_REVIEW] oci_response "
        f"status={status if status is not None else '<unknown>'} "
        f"opc_request_id={request_id or '<missing>'}",
        file=sys.stderr,
        flush=True,
    )


def _log_openai_compatible_response_metadata(response) -> None:
    status = getattr(response, "status", None)
    request_id = response.headers.get("opc-request-id", "")
    print(
        "[AI_REVIEW] oci_response "
        f"status={status if status is not None else '<unknown>'} "
        f"opc_request_id={request_id or '<missing>'}",
        file=sys.stderr,
        flush=True,
    )


def _parse_review_payload(raw_text: str) -> ReviewPayload:
    candidate = raw_text.strip()
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(f"Resposta sem JSON valido: {raw_text}")

    parsed = json.loads(candidate[start:end + 1])
    return ReviewPayload.from_values(
        parsed.get("result", "WARN"),
        parsed.get("comments", "Resposta OCI GenAI sem comments."),
    )
