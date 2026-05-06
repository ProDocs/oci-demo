from .models import ReviewPayload, SourceFile


def review_with_mock_rules(source_files: list[SourceFile]) -> ReviewPayload:
    controller_repository_violations = []
    todo_findings = []

    has_controller = False
    has_service = False
    has_repository = False

    for source_file in source_files:
        normalized_path = source_file.path.lower()
        content = source_file.content

        if "/controller/" in normalized_path:
            has_controller = True
            if "Repository " in content or ".repository." in normalized_path or "repository;" in content:
                controller_repository_violations.append(source_file.path)

        if "/service/" in normalized_path:
            has_service = True

        if "/repository/" in normalized_path:
            has_repository = True

        if "TODO" in content or "FIXME" in content:
            todo_findings.append(source_file.path)

    if controller_repository_violations:
        return ReviewPayload.from_values(
            "BLOCK",
            "Controller acessando repository diretamente em "
            + ", ".join(controller_repository_violations)
            + ". Isso viola a separacao de camadas definida nas guidelines.",
        )

    if not (has_controller and has_service and has_repository):
        return ReviewPayload.from_values(
            "WARN",
            "A estrutura minima controller/service/repository nao foi encontrada por completo. "
            "Revise se todas as camadas relevantes entraram na analise.",
        )

    if todo_findings:
        return ReviewPayload.from_values(
            "WARN",
            "Nao houve violacao clara, mas existem TODO/FIXME em "
            + ", ".join(todo_findings)
            + ". Isso merece revisao antes de promover para producao.",
        )

    return ReviewPayload.from_values(
        "PASS",
        "Controller acessa apenas a service layer, a logica de negocio esta concentrada no service e o repository ficou isolado.",
    )

