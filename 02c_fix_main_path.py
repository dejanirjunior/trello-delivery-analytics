from pathlib import Path
import subprocess
from datetime import datetime

server = Path("app/server.py")
content = server.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/server.py.bak_fix_main_path_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

# substituição direta e segura
new_content = content.replace('"main.py"', '"app/main.py"')

if new_content == content:
    print("Nenhuma ocorrência de main.py encontrada para substituir.")
    raise SystemExit(0)

server.write_text(new_content, encoding="utf-8")

# valida sintaxe
check = subprocess.run(
    ["python3", "-m", "py_compile", str(server)],
    capture_output=True,
    text=True
)

if check.returncode != 0:
    server.write_text(content, encoding="utf-8")
    print("ERRO de sintaxe — rollback aplicado")
    print(check.stderr)
    raise SystemExit(1)

print("OK: caminho corrigido com sucesso.")
