from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

from pdbe_bioskills.fetcher import content_dir

ItemKind = Literal["skill", "agent"]


@dataclass
class Item:
    kind: ItemKind
    name: str
    description: str
    source_dir: Path


def _content_root() -> Path:
    return content_dir()


def _parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip().strip('"\'')
    return result


def discover_skills() -> Iterator[Item]:
    skills_root = _content_root() / "skills"
    if not skills_root.is_dir():
        return
    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        fm = _parse_frontmatter(skill_md)
        name = fm.get("name", skill_md.parent.name)
        desc = fm.get("description", "")
        yield Item(kind="skill", name=name, description=desc, source_dir=skill_md.parent)


def discover_agents() -> Iterator[Item]:
    profiles_root = _content_root() / "profiles"
    if not profiles_root.is_dir():
        return
    for agents_md in sorted(profiles_root.rglob("AGENTS.md")):
        fm = _parse_frontmatter(agents_md)
        name = fm.get("name", agents_md.parent.name)
        desc = fm.get("description", "Agent profile")
        yield Item(kind="agent", name=name, description=desc, source_dir=agents_md.parent)


def discover_all() -> list[Item]:
    return list(discover_skills()) + list(discover_agents())
