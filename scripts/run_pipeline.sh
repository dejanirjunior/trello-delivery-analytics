#!/bin/bash

LOCKFILE="/tmp/trello_pipeline.lock"

if [ -f "$LOCKFILE" ]; then
  echo "Pipeline já está rodando. Abortando."
  exit 1
fi

touch $LOCKFILE

cd /home/ubuntu/apps/trello-dashboard

python3 app/main.py

rm -f $LOCKFILE

#!/bin/bash

echo "===================================="
echo "Pipeline iniciado em: $(date)"
echo "===================================="

docker exec trello-dashboard-container python /app/app/main.py

echo "===================================="
echo "Pipeline finalizado em: $(date)"
echo "===================================="
