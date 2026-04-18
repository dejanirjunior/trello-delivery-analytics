# Trello Delivery Analytics Portal

Portal de acompanhamento de demandas construído a partir de dados estruturados do Trello.

## O que o projeto entrega

- visão simplificada para cliente
- dashboard executivo por cliente
- visão tática para gerente de projetos
- visão executiva interna para diretoria
- métricas de fluxo a partir das movimentações dos cards
- automação de atualização dos arquivos

## Estrutura das visões

### Cliente
- portal do cliente
- kanban simplificado
- dashboard executivo do cliente

### Gestão interna
- visão do gerente de projetos
- visão da diretoria
- dashboards de flow

## Tecnologias
- Python
- Pandas
- Trello API
- HTML
- Chart.js

## Segurança dos dados

Este repositório público **não contém dados reais de clientes**.

Arquivos com dados reais gerados pelo projeto ficam fora do versionamento via `.gitignore`.

A pasta `demo/` contém apenas dados fictícios para demonstração.

## Demo

A pasta `demo/` contém uma demonstração pública com dados simulados.

## Como executar

1. Criar ambiente virtual
2. Instalar dependências
3. Configurar `.env`
4. Rodar os scripts de geração

## Observação

Para uso real, é necessário configurar credenciais da API do Trello em arquivo `.env`, que não é versionado.
