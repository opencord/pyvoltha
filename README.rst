DEPRECATED
==========

`No Maintenance Intended <http://unmaintained.tech/badge.svg)](http://unmaintained.tech/>`_

`VOLTHA 2.6` was the last release that officially used the `pyvoltha` library in any of the VOLTHA components.
From `2.7` onwards no VOLTHA component is in python, thus the repo has been deprecated, the go equivalent is `voltha-lib-go <https://github.com/opencord/voltha-lib-go>`_. This codebase is going to be removed after the VOLTHA 2.8 release LTS support ends in December 2022.

PyVOLTHA
========

PyVOLTHA is a collection of shared Python libraries that are use to
create Python-based
`VOLTHA <https://wiki.opencord.org/display/CORD/VOLTHA>`__ Device
Adapters and other Python utilities (CLI, …) that need to work with the
VOLTHA v2.0 and later Golang core.

Initially PyVOLTHA will target only Python 2.7, but contributors are
encouraged to write or refactor any library methods to eventually
support Python 3.6.x or later.

Installation instruction
------------------------

.. code:: bash

   pip install pyvoltha

Release History
---------------

+---------+------------+-----------------------------------------------+
| Version | Date       | Notes                                         |
+=========+============+===============================================+
| v0.1.0  | 2019-02-01 | Initial pypy release available. This is       |
|         |            | primarily for testing out pip install support |
|         |            | and is not expected to be useful outside of   |
|         |            | that.                                         |
+---------+------------+-----------------------------------------------+

Detailed Release History
~~~~~~~~~~~~~~~~~~~~~~~~~~~

v2.7.0 (2021-01-27)
^^^^^^^^^^^^^^^^^^^

-  Changed KPI frequency units from 1/10 second to 1 second to match
   what is implemented in the voltha-lib-go library.

-  Changed KPI Event titles from "Ethernet" and "PON" to "ETHERNET_NNI"
   and "PON_OLT" to match what is implemented in the voltha-lib-go
   library.

v0.1.0 (2019-02-01)
^^^^^^^^^^^^^^^^^^^

-  Experimental release of pyvoltha to test pip install capabilities.
   This version has manually created protobuf definitions and will
   probably not be very usable by any device adapters.
-  This version is not under source control management at this time.
   Initial VCS support is anticipated in the very near future when
   portions of this project can be consumed by a device adapter
   developer.
-  Protobuf files in the ‘proto’ directory were hand copied over from
   the voltha-go repository. These will eventually be in a separate repo
   that developers will need to include.
-  Most all import paths fixed but that does not mean everything works
-  A fair number of original unit tests are working after import
   changes. Others need work.
