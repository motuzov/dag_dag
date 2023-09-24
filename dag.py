from pathlib import Path

import json
import os

from dagster import (
    asset,
    ScheduleDefinition,
    define_asset_job,
    AssetSelection,
    sensor,
    RunRequest,
    RunConfig,
    op,
    job,
    Config,
    EnvVar, Definitions, ConfigurableResource,
    create_repository_using_definitions_args
    )  # import the `dagster` library

import pandas as pd

data_dir = '/home/jovyan/work/dagster_home/storage'


@asset  # add the asset decorator to tell Dagster this is an asset
def aleks_msg() -> None:
    hello_msg_str = 'hello liana!'
    with open(f"{data_dir}/aleks_msg.json", "w") as f:
        json.dump(hello_msg_str, f)


@asset(deps=[aleks_msg])
def to_pd() -> None:
    with open(f"{data_dir}/aleks_msg.json", "r") as f:
        aleks_msg_str = json.load(f)

    df = pd.DataFrame(
        {
            'from': ['aleks'],
            'to': ['liana'],
            'msg': ['hello']
        }
    )
    df.to_csv(f"{data_dir}/hello_df.csv")


assets_job = define_asset_job(
    "assets_job_hello",
    selection=AssetSelection.all()
    )


a_schedule = ScheduleDefinition(
    job=assets_job,
    cron_schedule="0 * * * *",  # every hour
)


class FileConfig(Config):
    filename: str = 'trigger.txt'


@op
def process_file(context, config: FileConfig):
    context.log.info(f'log: {config.filename}')


@job
def log_file_job():
    process_file()


MY_DIRECTORY = '/home/jovyan/work/data'


@sensor(job=log_file_job)
def my_directory_sensor():
    conf = FileConfig()
    filepath = os.path.join(MY_DIRECTORY, conf.filename)
    if os.path.isfile(filepath):
        yield RunRequest(
            run_config=RunConfig(
                ops={"process_file": conf}
            ),
        )


class CredentialsResource(ConfigurableResource):
    password: str


named_repo = create_repository_using_definitions_args(
    name="a_repo",
    assets=[aleks_msg, to_pd],
    schedules=[a_schedule],
    sensors=[my_directory_sensor],
    jobs=[assets_job, log_file_job],
    resources={
        "credentials": CredentialsResource(
            password=EnvVar("DB_PASS"),
            )
    }
)
