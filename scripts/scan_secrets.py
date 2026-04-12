"""
scan_secrets.py — Varre o repositório em busca de chaves hardcoded.

Detecta padrões de: OpenAI, GitHub, Airtable, Notion, Evolution API e senhas genéricas.
Ignora .env (gerenciado separadamente), .git/, venvs e binários.

Uso:
    python scripts/scan_secrets.py
    python scripts/scan_secrets.py --root /caminho/personalizado
"""

import re
import sys
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Padrões de detecção
# ---------------------------------------------------------------------------
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("OpenAI API Key",      re.compile(r"sk-proj-[A-Za-z0-9_\-]{80,}")),
    ("OpenAI API Key (v1)", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("GitHub Token",        re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("GitHub Fine-grained", re.compile(r"github_pat_[A-Za-z0-9_]{80,}")),
    ("Airtable PAT",        re.compile(r"pat[A-Za-z0-9]{14}\.[0-9a-f]{64}")),
    ("Airtable Legacy Key", re.compile(r"key[A-Za-z0-9]{14}")),
    ("Notion Token",        re.compile(r"ntn_[A-Za-z0-9]{50,}")),
    ("Notion Secret",       re.compile(r"secret_[A-Za-z0-9]{40,}")),
    # Evolution API keys costumam ser hashes hex de 32 chars (heurística)
    ("Possible Hex Secret", re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{32}(?![0-9a-fA-F])")),
]

# ---------------------------------------------------------------------------
# Arquivos / diretórios a ignorar
# ---------------------------------------------------------------------------
IGNORE_DIRS = {
    ".git", ".venv", "__pycache__", "node_modules",
    "dist", "build", ".mypy_cache", ".ruff_cache",
    "chromadb", "bm25_indexes",
}

IGNORE_FILES = {
    ".env",           # gerenciado via git-filter-repo
    ".env.example",   # só tem placeholders
    "scan_secrets.py",  # o próprio script
}

IGNORE_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".pdf", ".docx", ".xlsx", ".zip", ".tar", ".gz",
    ".lock",  # poetry.lock / uv.lock têm hashes, não segredos
}


def should_skip(path: Path) -> bool:
    if any(part in IGNORE_DIRS for part in path.parts):
        return True
    if path.name in IGNORE_FILES:
        return True
    if path.suffix.lower() in IGNORE_EXTENSIONS:
        return True
    return False


def scan_file(path: Path) -> list[dict]:
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        return findings

    for line_no, line in enumerate(text.splitlines(), start=1):
        # Pula linhas que são claramente placeholders
        if any(marker in line for marker in ("XXXXXXX", "sua_", "SUA_", "SEU_", "<", ">")):
            continue
        for label, pattern in PATTERNS:
            # Heurística: ignora "Possible Hex Secret" se a linha
            # já contém palavras de config não-sensível
            if label == "Possible Hex Secret" and any(
                kw in line.lower()
                for kw in ("hash", "uuid", "id", "checksum", "sha", "md5", "color", "colour")
            ):
                continue
            match = pattern.search(line)
            if match:
                findings.append({
                    "file": str(path),
                    "line": line_no,
                    "type": label,
                    "snippet": line.strip()[:120],
                })
    return findings


def main():
    parser = argparse.ArgumentParser(description="Varre o repo por segredos hardcoded.")
    parser.add_argument("--root", default=".", help="Diretório raiz do repositório")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    all_findings: list[dict] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if should_skip(path.relative_to(root)):
            continue
        all_findings.extend(scan_file(path))

    if not all_findings:
        print("Nenhum segredo detectado.")
        return 0

    print(f"\n{'='*70}")
    print(f"  SEGREDOS DETECTADOS: {len(all_findings)} ocorrência(s)")
    print(f"{'='*70}\n")

    current_file = None
    for f in all_findings:
        if f["file"] != current_file:
            current_file = f["file"]
            print(f"\n  Arquivo: {f['file']}")
            print(f"  {'─'*60}")
        print(f"  Linha {f['line']:>4} [{f['type']}]")
        print(f"           {f['snippet']}")

    print(f"\n{'='*70}")
    print("  Ação recomendada:")
    print("  1. Rotacione TODAS as chaves encontradas imediatamente.")
    print("  2. Use variáveis de ambiente (.env local, não commitado).")
    print("  3. Limpe o histórico git com: git filter-repo --path .env --invert-paths")
    print(f"{'='*70}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
