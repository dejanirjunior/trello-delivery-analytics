# 📊 Trello Analytics & Probabilistic Forecast

Dashboard completo para análise de delivery de times de desenvolvimento, com forecast probabilístico baseado em Monte Carlo.

---

## 🚀 Visão Geral

Este projeto transforma dados de um board Trello em:

- dashboards operacionais
- métricas de fluxo (lead time, cycle time)
- análises por cliente, tipo e prioridade
- **forecast probabilístico (Monte Carlo)**

O objetivo é apoiar decisões reais de entrega, capacidade e planejamento.

---

## 🎯 Principais Funcionalidades

### 📌 1. Visão do Gerente de Projetos
- backlog completo
- filtros por cliente, status e bloqueio
- KPIs de esforço, horas executadas e volume
- visão consolidada operacional

---

### 📈 2. Flow Analytics
- lead time e cycle time
- análise de fluxo de trabalho
- identificação de gargalos

---

### 🎲 3. Probabilistic Forecast (Monte Carlo)

Simulação baseada em histórico real do time:

- forecast por:
  - cards
  - story points
  - effort
- percentis:
  - P50 (provável)
  - P70/P85 (conservador)
  - P95 (alta segurança)

---

### 🧠 4. Simulação de Cenários (What-if)

Permite testar decisões antes de executá-las:

- adicionar X cards ao backlog
- definir tamanho médio (story point)
- definir esforço médio
- visualizar impacto no prazo

---

### 🔍 5. Filtros Inteligentes

- por cliente
- por tipo:
  - Feature
  - Bug
  - Débito Técnico

Permite análises como:
- quanto tempo só bugs levam
- impacto de um cliente específico
- esforço por tipo de demanda

---

### 📊 6. Sumário Executivo Automático

Interpretação automática do forecast:

- leitura de risco
- confiança do modelo
- recomendação prática de uso dos percentis

---

## 🏗️ Arquitetura

```text
Trello API
   ↓
trello_api.py
   ↓
datasets (kanban / flow / forecast)
   ↓
Monte Carlo Simulation
   ↓
HTML dashboards (PM / Diretor / Forecast)
   ↓
Flask server (trigger de atualização)
