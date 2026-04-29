from pathlib import Path
import shutil
import subprocess
from datetime import datetime

server = Path("app/server.py")
candidates = [
    Path("app/server.py.bak_20260429-012541"),
    Path("app/server.py.bak_final_fix"),
    Path("app/server.py.bak_targeted_fix_20260429-0107"),
]

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
current_backup = Path(f"app/server.py.broken_before_restore_{stamp}")

if server.exists():
    shutil.copy2(server, current_backup)
    print(f"Backup do server atual quebrado: {current_backup}")

chosen = None
for candidate in candidates:
    if candidate.exists():
        shutil.copy2(candidate, server)
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(server)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            chosen = candidate
            print(f"Restaurado com sucesso a partir de: {candidate}")
            break
        else:
            print(f"Backup inválido: {candidate}")
            print(result.stderr)

if not chosen:
    raise SystemExit("ERRO: nenhum backup válido de app/server.py foi encontrado.")

print("OK: app/server.py compila sem erro.")
