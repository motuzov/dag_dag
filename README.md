Deploy with docker compose
```bash
mkdir -p /tmp/DHOME
sudo cp dagster.yaml /tmp/DHOME/
docker compose up --force-recreate
docker compose down --rmi all
```
