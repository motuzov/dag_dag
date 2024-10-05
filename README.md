Deploy with docker compose
```bash
mkdir -p /tmp/DHOME
sudo cp dagster.yaml /tmp/DHOME/
docker compose up --force-recreate
docker compose down --rmi all
```

Setup dev container
```bash
docker create --name dagdag -p 3000:3000 -v /home/$USER/src/dag_dag:/home/dag/dag_dag:rw dagdag
```

Run dagster
```bash
dagster-webserver -h 0.0.0.0 -p 3000
dagster-daemon run
```
