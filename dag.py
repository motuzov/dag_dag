from dsml4s8e.define_job import define_job
from dagstermill import local_output_notebook_io_manager
from dagster import job

from pathlib import Path

import json
import os

import requests
from dagster import (asset,
                     repository,
                     ScheduleDefinition,
                     define_asset_job,
                     AssetSelection)  # import the `dagster` library
import pandas as pd


@asset  # add the asset decorator to tell Dagster this is an asset
def topstory_ids() -> None:
    newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    top_new_story_ids = requests.get(newstories_url).json()[:100]

    os.makedirs("data", exist_ok=True)
    with open("data/topstory_ids.json", "w") as f:
        json.dump(top_new_story_ids, f)


@asset(deps=[topstory_ids])  # this asset is dependent on topstory_ids
def topstories() -> None:
    with open("data/topstory_ids.json", "r") as f:
        topstory_ids = json.load(f)

    results = []
    for item_id in topstory_ids:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

        if len(results) % 20 == 0:
            print(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)
    df.to_csv("data/topstories.csv")


@job(
    name='simple_pipeline',
    tags={"cdlc_stage": "dev"},
    resource_defs={
        "output_notebook_io_manager": local_output_notebook_io_manager,
    }
)
def dagstermill_pipeline():
    module_path = Path(__file__)
    define_job(
        root_path=module_path.parent.parent,
        nbs_sequence=[
            "data_load/nb_0.ipynb",
            "data_load/nb_1.ipynb",
            "data_load/nb_2.ipynb"
        ]
    )


assets_job = define_asset_job(
    "assets_job_all",
    selection=AssetSelection.all()
    )


a_schedule = ScheduleDefinition(
    job=assets_job,
    cron_schedule="0 * * * *",  # every hour
)


@repository(
    name='my_repo',
    metadata={
        'team': 'Team A',
        'repository_version': '1.2.3',
        'environment': 'production', 
        }
 )
def simple_repository_2():
    return [dagstermill_pipeline,
            topstory_ids,
            topstories,
            assets_job,
            a_schedule
            ]
