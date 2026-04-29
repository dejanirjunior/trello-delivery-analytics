# Architecture — Trello Dashboard + Worklog

## 1. Status

Sistema Flask unificado em produção no container `trello-dashboard-container`.

## 2. Infraestrutura

- Host: AWS Lightsail / Ubuntu
- Projeto: `/home/ubuntu/apps/trello-dashboard`
- Domínio: `https://app.optarisbrasil.com`
- Proxy: Nginx
- Porta host: `8001`
- Porta container: `8000`

## 3. Componentes

- Flask + Gunicorn
- Docker Compose
- SQLite
- Nginx
- Trello API
- HTML estático gerado em `/data`

## 4. Módulos

- Dashboard Trello
- Portal de clientes
- Kanban
- Forecast Monte Carlo
- Worklog
- Daily
- Histórico de horas
- Histórico da Daily
- Administração
- Auditoria

## 5. Bancos

### Auth

Container: `/data/auth.db`  
Volume Docker: `trello_auth_data`

Campo crítico:

`users.worklog_developer_name`

### Worklog

Host:

`/home/ubuntu/apps/trello-dashboard/data/worklog.db`

Container:

`/app/data/worklog.db`

Tabelas:

- `worklogs`
- `daily_plan`
- `daily_plan_items`

## 6. Rotas principais

- `/login`
- `/logout`
- `/admin/clientes`
- `/admin/usuarios`
- `/admin/worklog-usuarios`
- `/admin/audit`
- `/daily`
- `/registro-horas`
- `/daily_history`
- `/worklog_history`
- `/trello/update`

## 7. Pipeline Trello

Endpoint:

`POST /trello/update`

Executa:

`python3 app/main.py`

Gera:

- `cards_enriched.csv`
- datasets Kanban
- dashboards HTML
- forecast Monte Carlo
- portais de clientes

## 8. Regras de negócio

### Daily

A Daily sugere cards automaticamente usando score interno baseado em:

- responsável no Trello
- status/lista
- prioridade
- risco
- vencimento
- data compromisso
- histórico recente
- bloqueios
- estimativas

O score continua sendo calculado, mas não é exibido ao usuário.

### Registro de horas

Se existir Daily salva no dia, os cards vêm dela. Caso contrário, o sistema usa sugestão automática.

### Usuários

Perfis:

- `admin`
- `internal`
- `client`

`admin` acessa administração, auditoria e vínculos.  
`internal` acessa operação Worklog/Daily.  
`client` acessa apenas relatórios permitidos.

## 9. Correções recentes

- Worklog migrado para dentro do Trello Dashboard
- `/trello/update` corrigido para retornar JSON
- `/` corrigido para redirecionar corretamente
- Auditoria/Admin com contraste corrigido
- Score removido da exibição da Daily
- Histórico da Daily ajustado visualmente

## 10. Operação

Subir:

`docker compose up -d --build`

Logs:

`docker logs --tail=160 trello-dashboard-container`

Testes:

- `curl -I http://localhost:8001/login`
- `curl -I http://localhost:8001/admin/audit`
- `curl -I http://localhost:8001/daily`
- `curl -I http://localhost:8001/registro-horas`
- `curl -I http://localhost:8001/daily_history`
- `curl -I http://localhost:8001/worklog_history`

## 11. Backup

Projeto:

`tar -czvf trello-dashboard-stable-prod-$(date +%Y%m%d-%H%M).tar.gz trello-dashboard`

Worklog:

`sqlite3 trello-dashboard/data/worklog.db ".backup worklog_backup_stable_$(date +%Y%m%d-%H%M).db"`

## 12. Pendências recomendadas

- proteger `/trello/update` para admin
- impedir múltiplas execuções simultâneas
- criar backup automático
- remover estilos inline gradualmente
- criar design system
- tornar pipeline assíncrono
- adicionar logs estruturados

