import os
import argparse
import importlib.metadata
import logging
import pathlib
from tempfile import gettempdir
import time
import typing
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


from pykit.loggedrobot import LoggedRobot


logger = logging.getLogger("pyfrc.sim")


entry_points = importlib.metadata.entry_points

AKIT_FILENAME = "akit-log-path.txt"


class PyKitReplayWatch:
    """
    Runs the robot in simulation and replay watch
    """

    do_update: bool = False

    @classmethod
    def doUpdate(cls) -> bool:
        return cls.do_update

    def __init__(self, parser: argparse.ArgumentParser):
        self.simexts = {}

        for entry_point in entry_points(group="robotpy_sim.2026"):
            try:
                sim_ext_module = entry_point.load()
            except ImportError:
                print(f"WARNING: Error detected in {entry_point}")
                continue

            self.simexts[entry_point.name] = sim_ext_module

            try:
                cmd_help = importlib.metadata.metadata(entry_point.dist.name)["summary"]
            except AttributeError:
                cmd_help = "Load specified simulation extension"
            parser.add_argument(
                f"--{entry_point.name}",
                default=False,
                action="store_true",
                help=cmd_help,
            )

    def run(
        self,
        options: argparse.Namespace,  # pylint: disable=unused-argument
        project_path: pathlib.Path,  # pylint: disable=unused-argument
        robot_class: typing.Type[LoggedRobot],  # pylint: disable=unused-argument
    ):

        PyKitReplayWatch.do_update = False

        class UpdateHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith(".py"):
                    print("[PyKit] Modification detected!")
                    PyKitReplayWatch.do_update = True

        file_handler = UpdateHandler()
        self.observer = Observer()
        self.observer.schedule(file_handler, ".", recursive=True)

        self.observer.start()

        if "LOG_PATH" not in os.environ:
            # see if we can pull from ascope's actively loaded log
            readPath = os.path.join(gettempdir(), AKIT_FILENAME)
            if not os.path.exists(readPath):
                print("[PyKit] Cannot load log to replay!")
                return
            with open(
                os.path.join(gettempdir(), AKIT_FILENAME), "r", encoding="utf-8"
            ) as f:
                readfilepath = f.readline()
                os.environ["LOG_PATH"] = readfilepath
                print(f"[PyKit] Logging from {readfilepath}")
        else:
            logpath = os.environ["LOG_PATH"]
            print(f"[PyKit] Logging from {logpath}")

        while True:
            PyKitReplayWatch.do_update = False
            print("[PyKit] Running replay...")
            # this is hacky, a real solution is needed for resetting environment
            os.system("python -m robotpy sim --nogui")
            print("[PyKit] replay finished...")
            while not PyKitReplayWatch.doUpdate():
                time.sleep(1)
