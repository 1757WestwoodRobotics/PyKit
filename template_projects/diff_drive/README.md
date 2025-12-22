# PyKit Differential Drive Robot Template

This is a robot project using PyKit for a basic differential drive robot.

## Basic Usage

Ensure you have [python 3.10+](https://www.python.org/downloads/release/python-31013/) and [uv](https://docs.astral.sh/uv/getting-started/installation/) are installed.

```sh
uv sync
```
should deal with all the installation details

## Running

To simulate the robot, use the following:

```sh
uv run -- robotpy --main src sim
```

To run back a log file in replay mode, set the `LOG_PATH` environment variable and then run in simulation

An example is to run the following:

```sh
LOG_PATH=/path/to/log/file.wpilog uv run -- robotpy --main src sim
```

For replay watch, do the following:

```sh
LOG_PATH=/path/to/log/file.wpilog uv run -- robotpy --main src watch
```

## On real hardware

On real hardware, to deploy onto a robot use the following

```sh
uv run -- robotpy --main src deploy
```
