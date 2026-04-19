from flask import Flask, jsonify
from flask_cors import CORS
import subprocess
from pathlib import Path

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent.parent


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "Servidor de atualização ativo"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "trello-dashboard-update-server"
    })


@app.route("/update", methods=["POST"])
def update():
    try:
        python_executable = str(BASE_DIR / "venv" / "bin" / "python")
        main_script = str(BASE_DIR / "app" / "main.py")

        result = subprocess.run(
            [python_executable, main_script],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )

        status = "success" if result.returncode == 0 else "error"

        return jsonify({
            "status": status,
            "output": result.stdout[-4000:],
            "warnings": result.stderr[-4000:] if status == "success" and result.stderr else None,
            "error": result.stderr[-4000:] if status == "error" else None
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


