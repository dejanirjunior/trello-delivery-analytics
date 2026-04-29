from pathlib import Path
import re
import subprocess
from datetime import datetime

server = Path("app/server.py")
content = server.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/server.py.bak_before_fix_existing_trello_update_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

new_route = r'''
@app.route("/trello/update", methods=["POST", "GET"])
def trello_update():
    import subprocess
    from flask import jsonify

    try:
        result = subprocess.run(
            ["python3", "app/main.py"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            return jsonify({
                "success": False,
                "message": "Erro ao atualizar dados.",
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-2000:]
            }), 500

        return jsonify({
            "success": True,
            "message": "Dados atualizados com sucesso.",
            "stdout": result.stdout[-2000:]
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
'''

pattern = r'''
@app\.route\("/trello/update",\s*methods=\[[^\]]+\]\)
def\s+trello_update\(\):
(?:\n    .*)+
'''

if "/trello/update" not in content:
    content = content.rstrip() + "\n\n" + new_route + "\n"
else:
    content = re.sub(pattern, new_route, content, count=1, flags=re.MULTILINE)

server.write_text(content, encoding="utf-8")

check = subprocess.run(
    ["python3", "-m", "py_compile", str(server)],
    capture_output=True,
    text=True
)

if check.returncode != 0:
    server.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
    print("ERRO: sintaxe inválida. Backup restaurado.")
    print(check.stderr)
    raise SystemExit(1)

print("OK: rota /trello/update corrigida.")
