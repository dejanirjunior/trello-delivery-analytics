from pathlib import Path
from datetime import datetime

file = Path("app/templates/worklog/registro_horas.html")
content = file.read_text(encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = Path(f"{file}.bak_layout_{stamp}")
backup.write_text(content, encoding="utf-8")
print(f"Backup criado: {backup}")

# 1. remover height do container do botão
content = content.replace(
    'style="display:flex; align-items:flex-end; height:40px;"',
    'style="display:flex; align-items:end;"'
)

# 2. corrigir botão (remover line-height hack)
content = content.replace(
    'line-height:40px;',
    ''
)

# 3. padronizar input date
content = content.replace(
    'type="date" name="work_date" value="{{ today }}" style="width:100%;"',
    'type="date" name="work_date" value="{{ today }}" style="width:100%; height:40px;"'
)

# 4. padronizar select
content = content.replace(
    'select name="developer_name" style="width:100%;"',
    'select name="developer_name" style="width:100%; height:40px;"'
)

file.write_text(content, encoding="utf-8")

print("OK: Registro de Horas corrigido estruturalmente.")
