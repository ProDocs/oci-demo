from .models import ReviewContext

MAX_FILE_CHARS = 3500


def build_prompt_parts(context: ReviewContext) -> tuple[str, str]:
    system_prompt = (
        "Voce e um revisor de arquitetura de software para um pipeline OCI DevOps. "
        "Analise apenas aderencia arquitetural. "
        "Responda exclusivamente com JSON valido contendo as chaves result e comments. "
        "Use BLOCK somente em violacao arquitetural clara. "
        "Use WARN para riscos leves, ambiguidades ou melhorias. "
        "Use PASS quando o codigo aderir as guidelines."
    )

    code_sections = []
    for source_file in context.source_files:
        truncated_content = source_file.content[:MAX_FILE_CHARS]
        code_sections.append(
            f"Arquivo: {source_file.path}\n"
            f"```java\n{truncated_content}\n```"
        )

    joined_code_sections = "\n\n".join(code_sections)
    user_prompt = (
        "Faca a revisao arquitetural do projeto.\n\n"
        f"Guidelines do projeto:\n{context.guidelines}\n\n"
        f"Instrucao de revisao:\n{context.instruction}\n\n"
        "Codigo relevante:\n"
        f"{joined_code_sections}\n\n"
        "Retorne somente JSON neste formato exato:\n"
        "{\n"
        '  "result": "PASS|WARN|BLOCK",\n'
        '  "comments": "feedback textual"\n'
        "}"
    )

    return system_prompt, user_prompt


def build_messages(context: ReviewContext) -> list[dict[str, str]]:
    system_prompt, user_prompt = build_prompt_parts(context)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
