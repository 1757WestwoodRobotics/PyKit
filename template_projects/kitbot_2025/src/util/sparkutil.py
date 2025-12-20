from typing import Callable

from rev import REVLibError, SparkBase


def tryUntilOk(attemps: int, command: Callable[[], REVLibError]):
    for _ in range(attemps):
        error = command()
        if error == REVLibError.kOk:
            break


def isOk(
    spark: SparkBase, supplier: Callable[[], float], consumer: Callable[[float], None]
):
    value = supplier()
    if spark.getLastError() == REVLibError.kOk:
        consumer(value)


def isOkMulti(
    spark: SparkBase,
    suppliers: list[Callable[[], float]],
    consumer: Callable[[list[float]], None],
):
    values: list[float] = []
    for supplier in suppliers:
        values.append(supplier())
        if spark.getLastError() is not REVLibError.kOk:
            return

    consumer(values)
