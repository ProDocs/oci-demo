from dataclasses import dataclass

VALID_RESULTS = {"PASS", "WARN", "BLOCK"}


@dataclass(frozen=True)
class SourceFile:
    path: str
    content: str


@dataclass(frozen=True)
class ReviewContext:
    guidelines: str
    instruction: str
    source_files: list[SourceFile]


@dataclass(frozen=True)
class ReviewPayload:
    result: str
    comments: str

    @classmethod
    def from_values(cls, result: str, comments: str) -> "ReviewPayload":
        normalized_result = (result or "WARN").upper()
        if normalized_result not in VALID_RESULTS:
            normalized_result = "WARN"

        normalized_comments = " ".join((comments or "").strip().split())
        if not normalized_comments:
            normalized_comments = "Revisao concluida sem comentarios adicionais."

        return cls(result=normalized_result, comments=normalized_comments)

    def as_dict(self) -> dict[str, str]:
        return {
            "result": self.result,
            "comments": self.comments,
        }

