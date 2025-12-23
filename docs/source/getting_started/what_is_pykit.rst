What is PyKit
===================

PyKit is a logging framework, using the same principles found in the Java project `AdvantageKit <https://docs.advantagekit.org>`_.

PyKit is designed with the same underlying principle as AdvantageKit:

* Log all inputs from the robot
* Allow the capability to replay those same inputs later from a log file, simulating robot behavior on different code
* Provide a way of viewing outputs and robot state

Because PyKit captures all the data that is flowing into and out of robot code, and is deterministic, it is able to accurately replay back the internal logic. This allows for functionality that would otherwise not be possible without deterministic log replay. For example

* Log extra fields and reveal what was internally going on
* See how pipelines would've functioned during a match, based on changes

Coming off of the field or some test session, the state and functionality of a robot can be analyzed, and tested for any changes or fixes, and how they would impact the robot had those fixes been deployed. 
