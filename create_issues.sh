#!/bin/bash

gh issue create --title "Trazer assigned members de forma robusta para o dataset" --body "Incluir responsáveis atribuídos nos datasets principais.

Problema:
Hoje não temos rastreabilidade clara por dev.

Objetivo:
- suportar múltiplos responsáveis por card
- permitir métricas por pessoa

Entregáveis:
- coluna com membros atribuídos
- padronização no dataset final"

gh issue create --title "Incorporar o campo Total Horas Executado no pipeline" --body "Trazer o custom field 'Total Horas Executado' para os datasets.

Objetivo:
- comparar esforço planejado vs executado

Entregáveis:
- campo integrado no dataset
- padronização numérica"

gh issue create --title "Criar métricas de completude por dev" --body "Medir adesão dos desenvolvedores ao preenchimento dos cards.

Métricas:
- total de cards atribuídos
- cards 100% preenchidos
- percentual de completude

Objetivo:
avaliar adoção do processo"

gh issue create --title "Criar relatório de cards incompletos por dev" --body "Listar cards atribuídos com campos obrigatórios faltantes.

Campos:
- effort
- data de entrega
- prioridade
- risco

Objetivo:
corrigir qualidade dos dados"

gh issue create --title "Implementar capacidade semanal vs effort por dev" --body "Comparar capacidade semanal (35h) com effort das demandas.

Objetivo:
- identificar sobrecarga
- identificar ociosidade

Entregáveis:
- cálculo por dev
- visualização no dashboard"

gh issue create --title "Comparar effort estimado vs horas executadas" --body "Comparar Effort com Total Horas Executado.

Objetivo:
- medir precisão das estimativas
- medir eficiência

Entregáveis:
- cálculo de desvio
- indicador de performance"

gh issue create --title "Criar métricas de backlog para refinado por período" --body "Medir quantos cards saem do backlog para refinado.

Granularidade:
- semanal
- mensal

Objetivo:
acompanhar entrada no fluxo"

gh issue create --title "Calcular tempo em cada etapa do fluxo" --body "Calcular tempo gasto em cada etapa:

- Refinado
- Em dev
- Q.A.
- Concluído
- Deploy

Objetivo:
identificar gargalos"

gh issue create --title "Criar lead time por card, cliente e dev" --body "Calcular tempo total de entrega.

Cortes:
- por card
- por cliente
- por desenvolvedor

Objetivo:
melhorar previsibilidade"

gh issue create --title "Criar throughput semanal e mensal" --body "Medir quantidade de cards entregues por período.

Objetivo:
- acompanhar volume de entrega
- medir capacidade real do time"
