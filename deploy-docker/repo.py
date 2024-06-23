from dagster import (
    FilesystemIOManager,
    define_asset_job,
    op,
    asset,
    Definitions,
    schedule,
    graph_asset,
)
from dagster_docker import docker_executor


@asset
def upstream_asset():
    return 1


@op
def hello(upstream_asset):
    return upstream_asset + 1


@op
def goodbye(hello):
    return hello + 1


@graph_asset
def my_ops_graph(upstream_asset):
    return goodbye(hello(upstream_asset))


@asset
def end(my_ops_graph):
    return my_ops_graph + 1


dev_job = define_asset_job(
    name="dev_job", selection=[upstream_asset, my_ops_graph, end]
)


my_step_isolated_job = define_asset_job(
    name="my_step_isolated_job",
    selection=[upstream_asset, my_ops_graph, end],
    executor_def=docker_executor,
)

"""
my_graph.to_job(
    name="my_step_isolated_job",
    # executor_def=docker_executor,
    resource_defs={
        "io_manager": FilesystemIOManager(base_dir="/tmp/io_manager_storage")
    },
)
"""


defs = Definitions(
    assets=[upstream_asset, my_ops_graph, end],
    jobs=[dev_job, my_step_isolated_job],
    resources={"io_manager": FilesystemIOManager(base_dir="/tmp/io_manager_storage")},
)
