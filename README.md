tsutil
=======

About
-----------
"tsutil" is a collection of small python libraries and scripts for troubleshooting.

Concept
----------

* Small and handy
    * no other dependencies except python
    * self-contained
    * pure python module

Components
-------------
* Sar tools and library
    * __tsutil.Sar__ (python module): parses sar binary output.
    * __sarview.py__ : summarizes sar.out to console.
    * __sargraph.py__:  visualize sar.out
    * __sar2influx.py__ : connector for sar.out -> influxdb tools

* Log analyze tools and library
    * log2influx.py
    * logsummary.py

TODO
-------------

LISENCE
------------
BSD
