#!/bin/bash

echo "===================================="
echo "Pipeline iniciado em: $(date)"
echo "===================================="

docker exec trello-dashboard-container python /app/app/main.py

echo "===================================="
echo "Pipeline finalizado em: $(date)"
echo "===================================="
