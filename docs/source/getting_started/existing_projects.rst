Existing Projects
=================

PyKit package
-------------

To install PyKit, simply install the ``robotpy-pykit`` package into your repository. You may optionally want the ``robotpy-pykit-watch`` package, which provides replay watch through the robotpy entrypoints.

For projects using python's builtin ``venv`` module:

.. code-block:: bash

    source path/to/venv/bin/activate
    pip install robotpy-pykit robotpy-pykit-watch

For projects using ``Pipenv`` for dependency management:

.. code-block:: bash

    pipenv install robotpy-pykit robotpy-pykit-watch

For projects using ``poetry``:

.. code-block:: bash

   poetry add robotpy-pykit robotpy-pykit-watch

For projects using ``uv``: (this is the suggested method and included in all pykit templates)

.. code-block:: bash

   uv add robotpy-pykit robotpy-pykit-watch

Inside the project's ``pyproject.toml`` file, pykit will also need to be added to the robot's install dependancies

.. code-block:: toml

    [tool.robotpy]
    ...
    requires = [
        "robotpy-pykit==0.2.1"
    ]

.. Note:: do **not** include ``robotpy-pykit-watch`` in your robot-installed dependancies, as it is for replay watch only, and will not install properly on a RoboRIO


Robot Configuration
-------------------

The main ``Robot`` class **must inherit from LoggedRobot**

``LoggedRobot`` behaves the same as ``TimedRobot`` except for the following:

* It does not support extra periodic functions
* It exposes a property ``useTiming`` which can control the operation of the robot, disabling ``useTiming`` will allow a robot to run as fast as possible, used during replay

.. code-block:: python

   from pykit.loggedrobot import LoggedRobot
   ...
   class Robot(LoggedRobot):
        def __init__(self) -> None:
            super().__init__() # MUST happen before other robot operatoins
            ...


Initialization of the logging framework is left to the user. This setup should be placed in the constructor of your Robot class *before any other initialization*. 

An example ``__init__`` is included below:

.. code-block:: python

    from pykit.logger import Logger
    from pykit.wpilog.wpilogwriter import WPILOGWriter
    from pykit.wpilog.wpilogreader import WPILOGReader
    from pykit.networktables.nt4Publisher import NT4Publisher
    from pykit.loggedrobot import LoggedRobot
    ...
    class Robot(LoggedRobot):
        def __init__(self) -> None:
            super().__init__()

            Logger.recordMetadata("ProjectName", "MyProject") # set a metadata field

            if self.isReal():
                Logger.addDataReciever(WPILOGWriter()) # Log to a USB stick
                Logger.addDataReciever(NT4Publisher(True)) # pass True to mimic AdvantageKit's publishing
            else:
                self.useTiming = False # run as fast as possible
                log_path = os.environ["LOG_PATH"] # fetch log file from environment variable
                log_path = os.path.abspath(log_path) # get absolute path
                Logger.setReplaySource(WPILOGReader(log_path)) # set replay source to WPILog under environment variable path
                Logger.addDataReciever(WPILOGWriter(log_path[:-7] + "_sim.wpilog")) # write out a new log file for the simulation

            Logger.start()

.. Note:: By default, ``WPILOGWriter`` writes to a USB stick when running on the robot. **A FAT32 Formatted USB Drive must be connected to a roboRIO port to capture log data**

In this minimal setup, all simulation runs in replay. If you plan on using the physics simulator, additional logic is required. See the `template projects <template_projects/index.html>`_ for one method on implementing this logic.




