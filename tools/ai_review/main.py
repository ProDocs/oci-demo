from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .clients import MockReviewClient, OciOpenAiCompatibleReviewClient, OciSdkReviewClient
from .models import ReviewPayload
from .review_engine import ReviewEngine

DEFAULT_INSTRUCTION = (
    "Atue como revisor de arquitetura do projeto. "
    "Verifique se controller nao acessa repository diretamente, se a logica de negocio esta na service layer, "
    "se existe separacao clara entre camadas e se ha violacoes que exigem BLOCK. "
    "Quando houver apenas risco leve, ambiguidade ou sugestao, use WARN. "
    "Quando o codigo estiver aderente, use PASS."
)


def main() -> int:
    parser = _build_argument_parser()
    args = parser.parse_args()

    try:
        review_payload = _execute_review(args)
    except Exception as exc:  # noqa: BLE001
        review_payload = ReviewPayload.from_values(
            "BLOCK",
            f"AI review falhou antes do build: {exc}",
        )

    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(review_payload.as_dict(), indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(review_payload.as_dict()))
    return 0


def _execute_review(args: argparse.Namespace) -> ReviewPayload:
    client = _build_client(args)
    engine = ReviewEngine(client)
    return engine.run(
        guidelines_path=Path(args.guidelines),
        source_dir=Path(args.source_dir),
        instruction=args.instruction,
    )


def _build_client(args: argparse.Namespace):
    mode = args.mode.lower()
    if mode == "mock":
        return MockReviewClient(args.scenario)
    if mode != "oci":
        raise ValueError(f"Modo de revisao nao suportado: {args.mode}")

    auth_mode = args.auth_mode.lower()
    model = args.model

    if auth_mode == "api_key":
        endpoint = _resolve_openai_compatible_endpoint(args.endpoint, args.base_url)
        api_key = args.api_key or os.getenv("OCI_GENAI_API_KEY", "")
        if not endpoint:
            raise ValueError("Defina OCI_GENAI_ENDPOINT ou OCI_GENAI_BASE_URL para usar auth_mode=api_key.")
        if not api_key:
            raise ValueError("Defina OCI_GENAI_API_KEY para usar auth_mode=api_key.")
        if not model:
            raise ValueError("Defina OCI_GENAI_MODEL para usar o modo oci.")

        return OciOpenAiCompatibleReviewClient(
            endpoint=endpoint,
            api_key=api_key,
            model=model,
        )

    if auth_mode not in {"resource_principal", "instance_principal", "user_principal"}:
        raise ValueError(
            "OCI_GENAI_AUTH_MODE deve ser resource_principal, instance_principal, "
            "user_principal ou api_key."
        )

    inference_endpoint = _resolve_inference_endpoint(
        inference_endpoint=args.inference_endpoint,
        endpoint=args.endpoint,
        base_url=args.base_url,
    )
    compartment_id = args.compartment_id

    if not inference_endpoint:
        raise ValueError(
            "Defina OCI_GENAI_INFERENCE_ENDPOINT para usar IAM auth no OCI Generative AI."
        )
    if not compartment_id:
        raise ValueError(
            "Defina OCI_GENAI_COMPARTMENT_OCID para usar IAM auth no OCI Generative AI."
        )
    if not model:
        raise ValueError("Defina OCI_GENAI_MODEL para usar o modo oci.")

    return OciSdkReviewClient(
        inference_endpoint=inference_endpoint,
        compartment_id=compartment_id,
        model=model,
        auth_mode=auth_mode,
        config_file=args.oci_config_file,
        config_profile=args.oci_config_profile,
    )


def _resolve_openai_compatible_endpoint(endpoint: str, base_url: str) -> str:
    if endpoint:
        return endpoint

    if not base_url:
        return ""

    normalized_base_url = base_url.rstrip("/")
    return normalized_base_url + "/chat/completions"


def _resolve_inference_endpoint(inference_endpoint: str, endpoint: str, base_url: str) -> str:
    candidate = (inference_endpoint or "").strip()
    if not candidate:
        candidate = (base_url or endpoint or "").strip()
    if not candidate:
        return ""

    normalized_candidate = candidate.rstrip("/")
    while True:
        stripped = False
        for suffix in ("/openai/v1/chat/completions", "/chat/completions", "/openai/v1"):
            if normalized_candidate.endswith(suffix):
                normalized_candidate = normalized_candidate[: -len(suffix)].rstrip("/")
                stripped = True
                break
        if not stripped:
            break
    return normalized_candidate


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Executa a revisao arquitetural por IA antes do build.")
    parser.add_argument("--guidelines", required=True, help="Arquivo markdown com as guidelines do projeto.")
    parser.add_argument("--source-dir", required=True, help="Diretorio raiz com os fontes Java relevantes.")
    parser.add_argument("--output", default="ai-review.json", help="Arquivo JSON de saida.")
    parser.add_argument("--instruction", default=DEFAULT_INSTRUCTION, help="Instrucao textual da revisao.")
    parser.add_argument("--mode", default=os.getenv("AI_REVIEW_MODE", "mock"), help="mock ou oci.")
    parser.add_argument("--scenario", default=os.getenv("AI_REVIEW_SCENARIO", "auto"), help="pass, warn, block ou auto.")
    parser.add_argument(
        "--auth-mode",
        default=os.getenv("OCI_GENAI_AUTH_MODE", "resource_principal"),
        help="resource_principal, instance_principal, user_principal ou api_key.",
    )
    parser.add_argument(
        "--inference-endpoint",
        default=os.getenv("OCI_GENAI_INFERENCE_ENDPOINT", ""),
        help="Endpoint raiz do OCI Generative AI Inference, sem /openai/v1.",
    )
    parser.add_argument(
        "--compartment-id",
        default=os.getenv("OCI_GENAI_COMPARTMENT_OCID", os.getenv("OCI_GENAI_COMPARTMENT_ID", "")),
        help="Compartment OCID usado na chamada de chat do OCI Generative AI.",
    )
    parser.add_argument(
        "--oci-config-file",
        default=os.getenv("OCI_CONFIG_FILE", ""),
        help="Arquivo de configuracao OCI para user_principal.",
    )
    parser.add_argument(
        "--oci-config-profile",
        default=os.getenv("OCI_CONFIG_PROFILE", "DEFAULT"),
        help="Profile OCI usado com user_principal.",
    )
    parser.add_argument("--endpoint", default=os.getenv("OCI_GENAI_ENDPOINT", ""), help="Endpoint completo do chat completions.")
    parser.add_argument("--base-url", default=os.getenv("OCI_GENAI_BASE_URL", ""), help="Base URL OCI GenAI compativel com OpenAI.")
    parser.add_argument("--api-key", default=os.getenv("OCI_GENAI_API_KEY", ""), help="API key OCI GenAI.")
    parser.add_argument("--model", default=os.getenv("OCI_GENAI_MODEL", ""), help="Modelo OCI GenAI.")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
