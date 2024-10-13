from dagster import (
    Out,
    Output,
    op,
    OpExecutionContext,
    graph_asset,
    AssetIn,
    asset,
    define_asset_job,
    AssetSelection,
    Definitions,
    Config,
    RunConfig,
    ExecuteInProcessResult,
)

from typing import List


class BranchingConfiguration(Config):
    condition: int


@asset
def branching_configuration_asset(
    context: OpExecutionContext, config: BranchingConfiguration
) -> int:
    default_branch = 1
    if config.condition != 1:
        default_branch = 2
    context.log.info(f"active branch: {default_branch}")
    return default_branch


@op(out={"branch_1": Out(is_required=False), "branch_2": Out(is_required=False)})
def branching_op(context: OpExecutionContext, branch):
    if branch == 1:
        yield Output(1, "branch_1")
    else:
        yield Output(2, "branch_2")


@op
def branch_1_op(context: OpExecutionContext, _input) -> int:
    context.log.info(_input)
    return _input


@op
def branch_2_op(context: OpExecutionContext, _input) -> int:
    context.log.info(_input)
    return _input


@op
def skip_non_active_baranch(context: OpExecutionContext, i: List[int]) -> int:
    context.log.info(i[0])
    return i[0]


@graph_asset(
    ins={"branching_configuration_asset": AssetIn("branching_configuration_asset")}
)
def branching_graph_asset(branching_configuration_asset) -> int:
    branch_1, branch_2 = branching_op(branching_configuration_asset)
    return skip_non_active_baranch([branch_1_op(branch_1), branch_2_op(branch_2)])


@asset(ins={"branching_graph_asset": AssetIn("branching_graph_asset")})
def end_asset(context: OpExecutionContext, branching_graph_asset) -> int:
    context.log.info(branching_graph_asset)
    return branching_graph_asset


assets_job = define_asset_job(
    name="assets_job_with_conditional_branch_ops", selection=AssetSelection.all()
)

defs = Definitions(
    assets=[branching_graph_asset, branching_configuration_asset, end_asset],
    jobs=[assets_job],
)


if __name__ == "__main__":
    res: ExecuteInProcessResult = defs.get_job_def(
        "assets_job_with_conditional_branch_ops"
    ).execute_in_process(
        run_config=RunConfig(
            {"branching_configuration_asset": BranchingConfiguration(condition=2)}
        )
    )
    print(res.run_id)
    print(res.output_for_node("end_asset"))
