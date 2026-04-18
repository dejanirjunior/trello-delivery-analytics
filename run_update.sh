#!/bin/bash
cd /home/junior/trello-dashboard || exit 1
source venv/bin/activate

python app/trello_api.py &&
python app/trello_actions.py &&
python app/kanban_dataset.py &&
python app/flow_metrics.py &&
python app/generate_kanban_html.py &&
python app/generate_dashboard.py &&
python app/generate_client_portal.py &&
python app/generate_director_view.py &&
python app/generate_pm_view.py &&
python app/generate_director_flow_view.py &&
python app/generate_pm_flow_view.py

