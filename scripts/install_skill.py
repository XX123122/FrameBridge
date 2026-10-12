"""Install only this project's authored SKILL.md; never overwrite an existing skill."""
import argparse
import os
from pathlib import Path


def install(project, destination):
    source = Path(project).resolve() / "SKILL.md"
    content = source.read_text(encoding="utf-8").replace("PROJECT_ROOT_VALUE", str(Path(project).resolve()))
    target = Path(destination) / "framebridge-web-imagegen" / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_text(encoding="utf-8") != content:
            raise FileExistsError(f"已有不同版本，未覆盖: {target}")
    else:
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    return target.resolve()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=str(Path(__file__).resolve().parents[1]))
    codex_directory = Path(os.environ["CODEX_HOME"]) if os.environ.get("CODEX_HOME") else Path.home() / ".codex"
    parser.add_argument("--destination", default=str(codex_directory / "skills"))
    args = parser.parse_args()
    print(install(args.project, args.destination))
