"""Tiny document model rendered to both Markdown and self-contained HTML."""

import base64
import html
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Heading:
    level: int
    text: str


@dataclass
class Paragraph:
    text: str


@dataclass
class BulletList:
    items: list[str]


@dataclass
class Table:
    headers: list[str]
    rows: list[list[str]]


@dataclass
class Image:
    path: Path  # absolute path on disk
    rel: str  # path relative to the Markdown file
    alt: str


@dataclass
class Code:
    text: str
    lang: str = ""


Block = Heading | Paragraph | BulletList | Table | Image | Code


@dataclass
class Document:
    title: str
    blocks: list[Block] = field(default_factory=list)

    def add(self, *blocks: Block) -> None:
        self.blocks.extend(blocks)


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def to_markdown(doc: Document) -> str:
    out: list[str] = [f"# {doc.title}", ""]
    for b in doc.blocks:
        if isinstance(b, Heading):
            out += [f"{'#' * b.level} {b.text}", ""]
        elif isinstance(b, Paragraph):
            out += [b.text, ""]
        elif isinstance(b, BulletList):
            out += [f"- {item}" for item in b.items] + [""]
        elif isinstance(b, Table):
            out.append("| " + " | ".join(_md_cell(h) for h in b.headers) + " |")
            out.append("|" + "|".join("---" for _ in b.headers) + "|")
            out += ["| " + " | ".join(_md_cell(c) for c in row) + " |" for row in b.rows]
            out.append("")
        elif isinstance(b, Image):
            out += [f"![{b.alt}]({b.rel})", ""]
        elif isinstance(b, Code):
            out += [f"```{b.lang}", b.text.rstrip(), "```", ""]
    return "\n".join(out).rstrip() + "\n"


_CSS = """
:root { color-scheme: light dark; }
body { font-family: system-ui, sans-serif; max-width: 1100px; margin: 2rem auto;
       padding: 0 16px; line-height: 1.5; background: Canvas; color: CanvasText; }
table { border-collapse: collapse; margin: 0.5rem 0 1.5rem; font-size: 0.9rem;
        display: block; overflow-x: auto; }
th, td { border: 1px solid GrayText; padding: 4px 8px; text-align: left; vertical-align: top; }
th { font-weight: 600; }
img { max-width: 100%; height: auto; }
pre { overflow-x: auto; padding: 8px; border: 1px solid GrayText; font-size: 0.8rem; }
"""


def _inline(text: str) -> str:
    """Escape, then render **bold** and `code` spans (the only inline markup used)."""
    escaped = html.escape(text)
    parts = escaped.split("**")
    escaped = "".join(f"<strong>{p}</strong>" if i % 2 else p for i, p in enumerate(parts))
    parts = escaped.split("`")
    return "".join(f"<code>{p}</code>" if i % 2 else p for i, p in enumerate(parts))


def to_html(doc: Document) -> str:
    out = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{html.escape(doc.title)}</title><style>{_CSS}</style></head><body>",
        f"<h1>{html.escape(doc.title)}</h1>",
    ]
    for b in doc.blocks:
        if isinstance(b, Heading):
            out.append(f"<h{b.level}>{_inline(b.text)}</h{b.level}>")
        elif isinstance(b, Paragraph):
            out.append(f"<p>{_inline(b.text)}</p>")
        elif isinstance(b, BulletList):
            out.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in b.items) + "</ul>")
        elif isinstance(b, Table):
            head = "".join(f"<th>{_inline(h)}</th>" for h in b.headers)
            body = "".join(
                "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>" for row in b.rows
            )
            out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
        elif isinstance(b, Image):
            data = base64.b64encode(b.path.read_bytes()).decode("ascii")
            out.append(f'<img alt="{html.escape(b.alt)}" src="data:image/png;base64,{data}">')
        elif isinstance(b, Code):
            out.append(f"<pre><code>{html.escape(b.text)}</code></pre>")
    out.append("</body></html>")
    return "\n".join(out) + "\n"
