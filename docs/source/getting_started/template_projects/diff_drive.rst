Differential Drive Template
===========================

The differential drive template is designed for robots using a SparkMAX, or TalonFX motor controller, and a NavX or Pigeon 2 gyro. Some features of this template are

* on-controller feedback loops
* physics simulation
* automated charactarization routines
* pose estimation
* **Deterministic Log Replay**

Setup
-----

1. Download the differential drive template from the latest PyKit release, and open up the project in your favorite code editor.

2. Install the dependencies using `uv <https://docs.astral.sh/uv/>`_ by running

.. code-block:: bash

        uv sync

3. Navigate to ``src/subsystems/driveconstants.py``
4. Update the motor controller CAN IDs, and gyro type to match your robot's configuration.
5. Update the value of ``kMotorReduction`` based on the robot's gearing. These values are *reduction* and *not* *ratio*. For example, a 10.71:1 reduction would be represented as ``10.71``.
6. Update the value of ``kTrackWidth`` to match the distance between the left and right wheels on your robot, in meters. There are constants provided in ``src/constants/math.py`` for converting between imperial and metric units.
7. Update the value of ``kWheelDiameter`` to match the theorhetical diameter of the wheels on your robot, in meters. 
8. Update the value of ``kMaxSpeed`` to match the maximum speed of your robot, in meters per second. 
9. Update the value of ``kPigeonCANId`` if using a Pigeon 2 gyro. **See the below customization section if you are using a NavX.**
10. Set the CAN IDs for the left and right leader and follower motor controllers. 
11. In ``src/robotcontainer.py``, update the IO implementations for your chosen hardware. The default is TalonFX and Pigeon 2.
12. Deploy the project to your robot, and connect using AdvantageScope.
13. Check that there are no errors, if there any errors, verify up to date firmware on all motor controllers and the gyro, as well as CAN IDs and configuration of all devices
14. *With the robot disabled* verify each drive side's rotation is correctly being updated by viewing in AdvantageScope (``)


