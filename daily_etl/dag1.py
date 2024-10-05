from dagster import (
    asset,
    AssetDep,
    DailyPartitionsDefinition,
    TimeWindowPartitionMapping,
    define_asset_job,
    build_schedule_from_partitioned_job,
    Definitions,
    AssetExecutionContext,
    ScheduleDefinition,
    AssetIn,
    BackfillPolicy,
    sensor,
    SensorEvaluationContext,
    RunRequest,
    asset_sensor,
    AssetKey,
    EventLogEntry,
    ConfigurableIOManager,
    InputContext, 
    OutputContext

)
import time
from typing import List
from datetime import datetime

# Define the daily partition
daily_partition = DailyPartitionsDefinition(start_date="2024-10-01")


# Define the upstream asset
@asset(
    partitions_def=daily_partition,
    backfill_policy=BackfillPolicy.single_run(),
)
def upstream_asset(context: AssetExecutionContext) -> str:
    # Logic for the upstream asset
    time.sleep(2)
    msg = f"upstream_assset immite masg at {time.time()}"
    start_datetime, end_datetime = context.partition_time_window
    context.log.info(context.partition_time_window)
    context.log.info(msg)
    # res : List[str] = [msg]
    return msg


# Define the downstream asset with a dependency on the upstream asset
@asset(
    partitions_def=daily_partition,
    backfill_policy=BackfillPolicy.single_run(),
    # deps=[
    #    AssetDep(
    #        upstream_asset,
    #        partition_mapping=TimeWindowPartitionMapping(
    #            start_offset=-1, end_offset=-1
    #        ),
    #    )
    # ],
    ins={
        "upstream_asset": AssetIn(),
    },
)
def downstream_asset(context: AssetExecutionContext, upstream_asset: str):
    # Logic for the downstream asset
    msg = f"downstream_asset get msg from upstream: '{upstream_asset}' \n at {time.time()}"
    context.log.info(msg)


# Define jobs for both assets
upstream_job = define_asset_job("upstream_job", selection=[upstream_asset])
downstream_job = define_asset_job("downstream_job", selection=[downstream_asset])

# Create schedules for both jobs
upstream_schedule = build_schedule_from_partitioned_job(upstream_job)
# downstream_schedule = build_schedule_from_partitioned_job(downstream_job)

class MyIOManager(ConfigurableIOManager):
    # specifies an optional string list input, via config system
    path_prefix: List[str] = []

    def _get_path(self, context) -> str:
        return "/".join(self.path_prefix + context.asset_key.path)

    def handle_output(self, context: OutputContext, obj):
        #handle upstream data and store it
        context.log.info(f'hendl upstream data: {obj}')

    def load_input(self, context: InputContext):
        #load data in downsteam asset
        context.log.info('input from upstream asset')
        return 'input from upstream asset'

@asset_sensor(asset_key=AssetKey("upstream_asset"), jobs=[upstream_job, downstream_job])
def upstream_asset_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    # Get the latest partition key for the upstream job
    print(context)
    context.log.info("AAAAAAAAAAAAAAAA!!!!!!!!!!!!!!!")
    context.log.info(asset_event.run_id)
    context.log.info(asset_event.dagster_event.materialization.partition)
    latest_partition_key = asset_event.dagster_event.materialization.partition
    context.log.info(asset_event.to_json())
    # latest_partition_key = context.cursor.last_run_key
    # print(daily_partition.get_last_partition_key(datetime.now()))
    # print(context)

    # Check if the upstream job has completed for the latest partition
    # if context.instance.has_asset_materialization(
    #    asset_key="upstream_asset", partition_key=latest_partition_key
    # ):
    yield RunRequest(job_name="downstream_job", partition_key=latest_partition_key)


# Define the Dagster definitions
defs = Definitions(
    assets=[upstream_asset, downstream_asset],
    jobs=[upstream_job, downstream_job],
    schedules=[upstream_schedule],
    resources={'io_manager': MyIOManager()},
    sensors=[upstream_asset_sensor],
)
