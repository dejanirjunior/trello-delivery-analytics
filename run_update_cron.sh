#!/bin/bash

LOG_FILE="/home/junior/trello-dashboard/logs/cron_update.log"
URL="http://localhost:8001/update"

echo "==================================================" >> "$LOG_FILE"
echo "Início: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

HTTP_CODE=$(curl -s -o /tmp/trello_update_response.json -w "%{http_code}" -X POST "$URL")

echo "HTTP_CODE=$HTTP_CODE" >> "$LOG_FILE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "Resposta:" >> "$LOG_FILE"
    cat /tmp/trello_update_response.json >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    echo "Status: OK" >> "$LOG_FILE"
else
    echo "Status: ERRO" >> "$LOG_FILE"
    echo "Resposta:" >> "$LOG_FILE"
    cat /tmp/trello_update_response.json >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
fi

echo "Fim: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
