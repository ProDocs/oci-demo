from pathlib import Path

from .clients import ReviewClient
from .models import ReviewContext, ReviewPayload, SourceFile

RELEVANT_SUFFIXES = ("Controller.java", "Service.java", "Repository.java", "Application.java")


class ReviewEngine:

    def __init__(self, review_client: ReviewClient) -> None:
        self.review_client = review_client

    def run(self, guidelines_path: Path, source_dir: Path, instruction: str) -> ReviewPayload:
        guidelines = guidelines_path.read_text(encoding="utf-8")
        source_files = _collect_relevant_source_files(source_dir)
        review_context = ReviewContext(
            guidelines=guidelines,
            instruction=instruction,
            source_files=source_files,
        )
        return self.review_client.review(review_context)


def _collect_relevant_source_files(source_dir: Path) -> list[SourceFile]:
    candidates = sorted(source_dir.rglob("*.java"))
    relevant_files = [file for file in candidates if file.name.endswith(RELEVANT_SUFFIXES)]
    if not relevant_files:
        relevant_files = candidates

    if not relevant_files:
        raise RuntimeError(f"Nenhum arquivo Java encontrado em {source_dir}")

    return [
        SourceFile(
            path=file.as_posix(),
            content=file.read_text(encoding="utf-8"),
        )
        for file in relevant_files
    ]

