import random

from dagster import (
    Out,
    Output,
    graph,
    op,
    job,
    OpExecutionContext,
    graph_asset,
    graph_multi_asset,
    AssetOut,
    AssetIn,
    In,
    asset,
    define_asset_job,
    AssetSelection,
    Definitions,
    load_assets_from_modules,
)


@op
def start(context: OpExecutionContext) -> int:
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
def finish(context: OpExecutionContext, _i) -> int:
    context.log.info(_i)
    return 4


# @graph
@graph
def branching():
    branch_1, branch_2 = branching_op(start())
    finish(branch_1_op(branch_1))
    finish(branch_2_op(branch_2))


@job
def branching_job():
    branching()


def main():
    res = branching_job.execute_in_process()
    print(res.run_id)


if __name__ == "__main__":
    main()
