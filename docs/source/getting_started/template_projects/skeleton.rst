Skeleton Template
=================

A barebones template project with PyKit integrated, but without any control logic.

This robot is set up to use the `uv <https://docs.astral.sh/uv/>`_ python package manager for dependency management. 

    This template is very minimal, so it is suggested to use one of the other template projects instead.

To install the dependencies, run

.. code-block:: bash

    uv sync

This will install all dependencies specified in the ``pyproject.toml`` file.

To run the robot code, use

.. code-block:: bash

    uv run robotpy --main src sim

This will run the robot code in simulation mode. To deploy to a real robot, use

.. code-block:: bash

    uv run robotpy --main src deploy

.. Note:: Since all source code in each template is under the ``src`` folder, it is important to tell robotpy where the main source code is located using the ``--main`` flag.

This project is configured to save log files while running on a real robot. A FAT32 formatted USB drive **MUST** be plugged into the robot in order to save log files. Log files will be saved to the root of the USB drive.

