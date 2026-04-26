# Trello Dashboard - Architecture

## 1. Visão Geral

Sistema web para acompanhamento de projetos baseado em dados do Trello, com foco em visibilidade para clientes, gerentes de projeto, área interna e diretoria.

O ambiente atual está publicado em uma instância AWS EC2 com Ubuntu, usando Docker para separar os serviços principais e Nginx como reverse proxy.

## 2. Infraestrutura

### Ambiente

- Cloud: AWS EC2
- Sistema operacional: Ubuntu 24.04 LTS
- Usuário SSH: ubuntu
- IP público atual: 18.208.210.2
- Domínio principal: app.optarisbrasil.com
- Acesso remoto: VS Code Remote SSH

### Diretório base

```text
/home/ubuntu/apps/
Projetos existentes
/home/ubuntu/apps/
├── trello-dashboard
├── trello-dashboard-backup
├── worklog-analytics
├── worklog-analytics_backup
├── trello-dashboard.tar.gz
└── worklog-analytics.tar.gz
3. Serviços e Containers
trello-dashboard

Aplicação principal do portal e dashboards baseados no Trello.

Container: trello-dashboard-container
Porta externa no host: 8001
Porta interna provável: 8000
Diretório: /home/ubuntu/apps/trello-dashboard
worklog-analytics

Aplicação complementar para controle de worklogs, apontamentos, planejamento diário e análises internas.

Container: worklog-analytics-container
Porta externa no host: 8003
Diretório: /home/ubuntu/apps/worklog-analytics
4. Separação Conceitual dos Sistemas
trello-dashboard

Responsável por:

Coletar ou consumir dados do Trello
Gerar visões de Kanban
Gerar dashboards por cliente
Gerar visões para PMs, diretoria e clientes
Publicar páginas HTML ou rotas web
Exibir métricas de fluxo, status e acompanhamento de projetos
worklog-analytics

Responsável por:

Registrar apontamentos de horas
Apoiar planejamento diário
Relacionar desenvolvedores, cards e atividades
Validar esforço, horas e possíveis desvios
Complementar a visão gerencial do Trello Dashboard
5. Fluxo Geral de Dados
Trello API
   ↓
Scripts Python de coleta/processamento
   ↓
Arquivos JSON/CSV internos
   ↓
Dashboards / HTML / Flask / Dash
   ↓
Cliente, PM, área interna e diretoria
6. Perfis de Usuário e Visibilidade
Admin

Acesso esperado:

Todas as visões
Configurações
Cadastro de clientes
Gestão de permissões
Dados internos e externos
Métricas consolidadas
Internals / PMs

Acesso esperado:

Visão operacional
Cards por status
Worklogs
Alertas
Bloqueios
Riscos
Métricas de fluxo
Planejamento semanal e diário
Clientes

Acesso esperado:

Portal do próprio cliente
Kanban filtrado por cliente
Dashboard do cliente
Status report
Indicadores de progresso
Bloqueios e pendências relevantes
Itens entregues, em andamento e planejados

Clientes não devem visualizar dados de outros clientes.

7. Identificação de Clientes

Atualmente, a identificação do cliente está relacionada aos rótulos dos cards no Trello.

Atenção: nem todo rótulo deve ser tratado como cliente.

Regra recomendada:

Criar uma configuração explícita de clientes
O sistema só deve gerar portal de cliente para rótulos cadastrados como cliente
A interface administrativa deve permitir cadastrar cliente, nome de exibição, rótulo Trello, permissões e URLs geradas
8. Views Esperadas

Exemplos de views existentes ou planejadas:

Cliente
Portal do cliente
Kanban do cliente
Dashboard do cliente
Status report
Visão semanal
PM / Interno
Visão operacional
Cards por status
Itens bloqueados
Alertas de prazo
Worklogs
Métricas de fluxo
Planejamento diário/semanal
Diretoria
Visão consolidada
Indicadores executivos
Entregas por cliente
Gargalos
Capacidade
Forecast
Tendência de fluxo
9. Rotas e URLs

As rotas precisam ser documentadas e validadas diretamente no código Flask/Dash.

Comandos úteis para localizar rotas:

cd ~/apps/trello-dashboard
grep -R "@app.route\|Blueprint\|register_blueprint\|weekly\|kanban\|dashboard" -n . --exclude-dir=.git --exclude-dir=__pycache__

Testes locais:

curl -I http://localhost:8001/
curl -I http://localhost:8001/kanban
curl -I http://localhost:8001/dashboard
curl -I http://localhost:8001/weekly

Testes pelo domínio:

curl -I https://app.optarisbrasil.com/
10. Nginx

O Nginx atua como reverse proxy entre o domínio público e os containers.

Cuidados:

Conferir se o domínio aponta para o IP correto
Conferir se o proxy_pass aponta para a porta correta
Conferir se autenticação básica está ativa ou não
Conferir se arquivos estáticos estão sendo servidos corretamente
Sempre testar configuração antes de recarregar

Comandos úteis:

sudo nginx -t
sudo systemctl reload nginx
sudo systemctl status nginx

Logs úteis:

sudo tail -n 100 /var/log/nginx/access.log
sudo tail -n 100 /var/log/nginx/error.log
11. Docker

Comandos úteis:

docker ps
docker logs trello-dashboard-container --tail 100
docker logs worklog-analytics-container --tail 100
docker restart trello-dashboard-container
docker restart worklog-analytics-container

Se o projeto usar Docker Compose:

docker compose ps
docker compose up -d
docker compose down

Antes de usar docker compose, confirmar se existe compose.yaml ou docker-compose.yml no diretório.

12. Processo Seguro de Alteração

Antes de qualquer alteração:

cd ~/apps/trello-dashboard
git status

Se for alterar arquivo importante:

cp caminho/do/arquivo caminho/do/arquivo.bak_$(date +%Y%m%d_%H%M%S)

Depois da alteração:

docker restart trello-dashboard-container
curl -I http://localhost:8001/

Se estiver funcionando:

git status
git add .
git commit -m "documenta arquitetura e ajustes do sistema"
13. Padrão de Trabalho no VS Code

Sempre:

Conferir se o arquivo existe
Abrir e ler o conteúdo antes de alterar
Fazer backup antes de mudanças relevantes
Alterar com calma
Reiniciar o container correto
Testar localmente
Testar pelo domínio
Ver logs em caso de erro
Fazer commit em ponto estável
14. Pontos Críticos
Rotas Flask/Dash precisam estar registradas corretamente
Nginx pode mascarar erro de aplicação
404 em localhost normalmente indica rota inexistente ou não registrada
404 no domínio, mas não no localhost, normalmente indica problema de Nginx
Mudanças no código geralmente exigem restart do container
Cliente não pode acessar dados de outro cliente
Rótulos do Trello não devem ser assumidos automaticamente como clientes
15. Roadmap Técnico

Itens previstos ou recomendados:

Implementar autenticação por usuário
Separar perfis: admin, interno e cliente
Criar cadastro gráfico de clientes
Gerar automaticamente portal, kanban e dashboard por cliente cadastrado
Documentar todas as rotas
Criar status report automático
Melhorar visão semanal
Criar documentação técnica de API
Melhorar observabilidade com logs e health checks
Padronizar deploy e rollback
Criar pipeline de backup antes de alterações críticas
16. Comandos de Diagnóstico Rápido
cd ~/apps/trello-dashboard
pwd
ls -la
git status
docker ps
docker logs trello-dashboard-container --tail 50
curl -I http://localhost:8001/

Para o worklog:

cd ~/apps/worklog-analytics
pwd
ls -la
docker logs worklog-analytics-container --tail 50
curl -I http://localhost:8003/
17. Observação Final

Este documento deve ser mantido atualizado sempre que houver mudança relevante em:

Rotas
Containers
Portas
Domínio
Nginx
Fluxo de autenticação
Regras de negócio
Estrutura de pastas
Processo de deploy
