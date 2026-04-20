import subprocess
import sys


def run_step(description, command):
    print(f"\n=== {description} ===")
    result = subprocess.run(command, shell=True)

    if result.returncode != 0:
        print(f"Erro ao executar: {description}")
        sys.exit(1)


def main():
    print("Iniciando pipeline Trello Analytics...")

    run_step(
        "1. Extraindo dados do Trello",
        "python app/trello_api.py"
    )

    run_step(
        "2. Gerando dataset Kanban",
        "python app/kanban_dataset.py"
    )

    run_step(
        "3. Captando movimentações (actions)",
        "python app/trello_actions.py"
    )

    run_step(
        "4. Calculando métricas de fluxo",
        "python app/flow_metrics.py"
    )

    run_step(
        "5. Gerando Kanban HTML",
        "python app/generate_kanban_html.py"
    )

    run_step(
        "6. Gerando Dashboard Executivo",
        "python app/generate_dashboard.py"
    )

    run_step(
        "7. Gerando visão PM",
        "python app/generate_pm_view.py"
    )

    run_step(
        "8. Gerando visão Diretoria",
        "python app/generate_director_view.py"
    )

    run_step(
        "9. Gerando visão Flow Diretoria",
        "python app/generate_director_flow_view.py"
    )

    run_step(
        "10. Gerando visão Flow PM",
        "python app/generate_pm_flow_view.py"
    )

    run_step(
        "11. Gerando dataset de forecast",
        "python app/forecast_dataset.py"
    )

    run_step(
        "12. Rodando Monte Carlo",
        "python app/forecast_montecarlo.py"
    )

    run_step(
        "13. Gerando visão Forecast PM",
        "python app/generate_pm_forecast_view.py"
    )

    print("\nPipeline concluído com sucesso!")


if __name__ == "__main__":
    main()

