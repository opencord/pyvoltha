## VOLTHA TESTS

Currently only unit tests are supported by the PyVoltha package
* **Unit Tests**
    *  These tests exercise the smallest testable parts of the code. They 
    are designed to be fully automated and can be executed by a build 
    machine (e.g. Jenkins).  
    
This document focuses on running the unit tests only.

##### Running the utests
* **Triggering all the utests as a batch run**: Unit tests under voltha can be run as follows:
```
cd /pyvoltha/
. ./env.sh
make utest
```
