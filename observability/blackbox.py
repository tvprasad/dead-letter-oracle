from dataclasses import dataclass


@dataclass
class TraceEntry:
    step: int
    summary: str
    detail: str = ""


class BlackBox:
    def __init__(self):
        self._entries: list[TraceEntry] = []
        self._counter = 0

    def record(self, summary: str, detail: str = "") -> None:
        self._counter += 1
        self._entries.append(TraceEntry(self._counter, summary, detail))

    def entries(self) -> list[dict]:
        return [{"step": e.step, "summary": e.summary, "detail": e.detail} for e in self._entries]

    def render(self) -> None:
        width = 56
        print("=" * width)
        print("BlackBox Trace")
        print("-" * width)
        for e in self._entries:
            line = f"{e.step:>2}. {e.summary}"
            print(line)
            if e.detail:
                # Wrap detail at 52 chars, indented
                words = e.detail.split()
                current = "      "
                for word in words:
                    if len(current) + len(word) + 1 > 56:
                        print(current.rstrip())
                        current = "      " + word + " "
                    else:
                        current += word + " "
                if current.strip():
                    print(current.rstrip())
        print("=" * width)
