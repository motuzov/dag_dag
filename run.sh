export DAGSTER_HOME=/home/jovyan/work/dagster_home
mkdir -p $DAGSTER_HOME
dagster dev -h 0.0.0.0 -f dag.py
