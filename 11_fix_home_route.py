from pathlib import Path
from datetime import datetime
import subprocess
import re

server = Path("app/server.py")
content = server.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/server.py.bak_before_home_fix_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

new_home = '''
@app.route("/")
def home():
    if not is_logged():
        return redirect("/login")

    return redirect("/admin/clientes")
'''

pattern = r'@app\.route\("/"\).*?def home\(\):.*?(?=\n@app\.route|\Z)'

new_content, count = re.subn(
    pattern,
    new_home.strip() + "\n",
    content,
    count=1,
    flags=re.DOTALL
)

if count == 0:
    raise SystemExit("ERRO: não encontrei a rota / para substituir.")

server.write_text(new_content, encoding="utf-8")

check = subprocess.run(
    ["python3", "-m", "py_compile", str(server)],
    capture_output=True,
    text=True
)

if check.returncode != 0:
    server.write_text(content, encoding="utf-8")
    print("ERRO: sintaxe inválida. Rollback aplicado.")
    print(check.stderr)
    raise SystemExit(1)

print("OK: rota / corrigida com sucesso.")
