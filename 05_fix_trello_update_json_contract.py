from pathlib import Path
from datetime import datetime
import subprocess
import re

server = Path("app/server.py")
content = server.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/server.py.bak_before_json_contract_{stamp}")
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
            stderr = result.stderr[-3000:] if result.stderr else ""
            stdout = result.stdout[-3000:] if result.stdout else ""
            msg = stderr or stdout or "Erro desconhecido ao executar pipeline."

            return jsonify({
                "success": False,
                "ok": False,
                "status": "error",
                "message": msg,
                "error": msg,
                "stdout": stdout,
                "stderr": stderr
            }), 500

        stdout = result.stdout[-3000:] if result.stdout else ""

        return jsonify({
            "success": True,
            "ok": True,
            "status": "success",
            "message": "Dados atualizados com sucesso.",
            "error": None,
            "stdout": stdout,
            "stderr": ""
        }), 200

    except subprocess.TimeoutExpired:
        msg = "Tempo limite excedido ao atualizar os dados. O processo demorou mais de 5 minutos."
        return jsonify({
            "success": False,
            "ok": False,
            "status": "error",
            "message": msg,
            "error": msg
        }), 504

    except Exception as e:
        msg = str(e) or "Erro desconhecido."
        return jsonify({
            "success": False,
            "ok": False,
            "status": "error",
            "message": msg,
            "error": msg
        }), 500
'''

pattern = r'@app\.route\("/trello/update".*?def trello_update\(\):.*?(?=\n@app\.route|\nif __name__|\Z)'

new_content, count = re.subn(
    pattern,
    new_route.strip() + "\n",
    content,
    count=1,
    flags=re.DOTALL
)

if count == 0:
    new_content = content.rstrip() + "\n\n" + new_route.strip() + "\n"

server.write_text(new_content, encoding="utf-8")

check = subprocess.run(
    ["python3", "-m", "py_compile", str(server)],
    capture_output=True,
    text=True
)

if check.returncode != 0:
    server.write_text(content, encoding="utf-8")
    print("ERRO: sintaxe inválida. Backup restaurado.")
    print(check.stderr)
    raise SystemExit(1)

print("OK: contrato JSON da rota /trello/update padronizado.")
