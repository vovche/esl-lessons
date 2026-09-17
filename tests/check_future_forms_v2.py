from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "9" / "future-forms" / "index.html"
V2 = ROOT / "9" / "future-forms-v2" / "index.html"


def headings(path: Path):
    class H(HTMLParser):
        def __init__(self):
            super().__init__(); self.inside = False; self.buf = []; self.items = []
        def handle_starttag(self, tag, attrs):
            if tag == "h2": self.inside = True; self.buf = []
        def handle_data(self, data):
            if self.inside: self.buf.append(data)
        def handle_endtag(self, tag):
            if tag == "h2" and self.inside:
                self.items.append(" ".join("".join(self.buf).split())); self.inside = False
    h = H(); h.feed(path.read_text(encoding="utf-8")); return h.items


def main():
    assert V1.exists(), "main lesson missing"
    assert V2.exists(), "experimental v2 lesson missing"
    source = V2.read_text(encoding="utf-8")
    numbered = [h for h in headings(V2) if h.split(".", 1)[0].isdigit()]
    assert len(numbered) == 18, f"expected 18 numbered lesson screens, got {len(numbered)}"
    for n in range(1, 19):
        assert any(h.startswith(f"{n}.") for h in numbered), f"screen {n} missing"
    required = [
        'class="story-deck"', 'id="sceneProgress"', 'id="scenePrev"',
        'id="sceneNext"', 'id="sceneMap"', 'id="rotateGate"',
        'aria-live="polite"', 'data-v2-ready="true"',
        '@media (orientation:portrait)', 'touchstart', 'keydown'
    ]
    for marker in required:
        assert marker in source, f"missing UX marker: {marker}"
    assert 'href="../future-forms/"' in source, "missing link to stable lesson"
    print("future-forms-v2 contract: PASS")


if __name__ == "__main__":
    main()
