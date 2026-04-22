#!/bin/bash

LOG_FILE="/home/junior/trello-dashboard/data/cron.log"

echo "========================================" >> $LOG_FILE
echo "INÍCIO: $(date '+%Y-%m-%d %H:%M:%S')" >> $LOG_FILE

curl -s -X POST http://localhost:8080/trello/update >> $LOG_FILE 2>&1

echo "FIM: $(date '+%Y-%m-%d %H:%M:%S')" >> $LOG_FILE
echo "" >> $LOG_FILE
