import os
import argparse
import importlib.metadata
import logging
import pathlib
import sys
import time
import typing
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


from pykit.loggedrobot import LoggedRobot


logger = logging.getLogger("pyfrc.sim")


if sys.version_info < (3, 10):

    def entry_points(group):
        eps = importlib.metadata.entry_points()
        return eps.get(group, [])

else:
    entry_points = importlib.metadata.entry_points


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
        options: argparse.Namespace,
        project_path: pathlib.Path,
        robot_class: typing.Type[LoggedRobot],
    ):


        PyKitReplayWatch.do_update = False

        class UpdateHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith(".py"):
                    print(f"[PyKit] Modification detected!")
                    PyKitReplayWatch.do_update = True

        file_handler = UpdateHandler()
        self.observer = Observer()
        self.observer.schedule(file_handler, ".", recursive=True)

        self.observer.start()

        while True:
            PyKitReplayWatch.do_update = False
            print("[PyKit] Running replay...")
            a = os.system("python -m robotpy sim --nogui") # this is hacky, a real solution is needed for resetting environment
            print("[PyKit] replay finished...")
            while not PyKitReplayWatch.doUpdate():
                time.sleep(1)
        # # Some extensions (gui) changes the current directory
        # cwd = os.getcwd()

        # for name, module in self.simexts.items():
        #     if getattr(options, name.replace("-", "_"), False):
        #         try:
        #             module.loadExtension()
        #         except:
        #             print(f"Error loading {name}!", file=sys.stderr)
        #             raise

        # os.chdir(cwd)

        # # initialize physics, attach to the user robot class
        # from pyfrc.physics.core import PhysicsInterface, PhysicsInitException

        # try:
        #     _, robot_class = PhysicsInterface._create_and_attach(
        #         robot_class, project_path
        #     )

        #     # run the robot
        #     retval = robot_class.main(robot_class)
        #     print(retval)
        #     return retval

        # except PhysicsInitException:
        #     return False
