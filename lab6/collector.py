from pathlib import Path

with open("all_py.txt", "w", encoding="utf-8") as out:
    for file in sorted(Path(".").glob("*.py")):
        out.write(f"\n\n# ===== FILE: {file} =====\n\n")
        out.write(file.read_text(encoding="utf-8"))
