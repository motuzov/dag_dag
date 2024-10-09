import random

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
)


@asset
def start_asset(context: OpExecutionContext) -> int:
    context.log.info("start!")
    return 0


@op(out={"branch_1": Out(is_required=False), "branch_2": Out(is_required=False)})
def branching_op(context: OpExecutionContext, zero):
    context.log.info(zero)
    num = random.randint(0, 1)
    if num == 0:
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
def finish(context: OpExecutionContext, i) -> int:
    context.log.info(i)
    return 4


@op
def define(context: OpExecutionContext, i):
    context.log.info(i[0])
    return i


# @graph
@graph_asset(ins={"start_asset": AssetIn("start_asset")})
def branching_graph_asset(start_asset) -> int:
    branch_1, branch_2 = branching_op(start_asset)
    out1 = branch_1_op(branch_1)
    out2 = branch_2_op(branch_2)
    outs = []
    for o in [out1, out2]:
        outs.append(o)
    m = define(outs)
    t = finish(m)
    return t


@asset(ins={"branching_graph_asset": AssetIn("branching_graph_asset")})
def end_asset(context: OpExecutionContext, branching_graph_asset) -> int:
    context.log.info(branching_graph_asset)
    return branching_graph_asset


assets_job = define_asset_job(
    name="assets_job_with_conditional_branch_ops", selection=AssetSelection.all()
)

defs = Definitions(
    assets=[branching_graph_asset, start_asset, end_asset],
    jobs=[assets_job],
)


def main():
    res = defs.get_job_def(
        "assets_job_with_conditional_branch_ops"
    ).execute_in_process()
    print(res.run_id)


if __name__ == "__main__":
    main()
