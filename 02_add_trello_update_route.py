from pathlib import Path
import subprocess
from datetime import datetime

server = Path("app/server.py")
main_script = Path("app/main.py")

if not server.exists():
    raise SystemExit("ERRO: app/server.py não encontrado")

if not main_script.exists():
    raise SystemExit("ERRO: app/main.py não encontrado — abortando para evitar erro")

content = server.read_text(encoding="utf-8")

if "/trello/update" in content:
    print("Rota /trello/update já existe. Nenhuma alteração feita.")
    raise SystemExit(0)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"app/server.py.bak_before_trello_update_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

route_code = '''

@app.route("/trello/update", methods=["POST"])
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
                "message": "Erro ao atualizar dados",
                "stderr": result.stderr[-1000:]
            }), 500

        return jsonify({
            "success": True,
            "message": "Dados atualizados com sucesso"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

'''

new_content = content.rstrip() + "\n" + route_code
server.write_text(new_content, encoding="utf-8")

# valida sintaxe antes de subir
check = subprocess.run(
    ["python3", "-m", "py_compile", str(server)],
    capture_output=True,
    text=True
)

if check.returncode != 0:
    print("ERRO de sintaxe detectado. Restaurando backup.")
    server.write_text(content, encoding="utf-8")
    print(check.stderr)
    raise SystemExit(1)

print("OK: rota adicionada e código válido.")
