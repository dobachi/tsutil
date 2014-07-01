#!/usr/bin/env python
"""
Copyright (c) 2014, sakamotomsh All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from tsutil import Sar

tmpl="""
==============================================================================
- IDENTITY
  - HOSTNAME: %(hostname)s
  - DATETIME: %(start)s - %(stop)s
- H/W
  - CPU: %(cpucount)d
  - RAM: %(ramsize).2f GB
  - SWAP: %(swapsize).2f GB
  - DISC: %(iodevs)s
  - NETWORK: %(ifaces)s

- METRICS SUMMARY:
%(summary)s
==============================================================================
"""

if __name__ == '__main__':
    import sys
    s = Sar(sys.argv[1])
    print

    hostname = s.hostname
    start = s.start.strftime("%Y-%m-%d %H:%M:%S")
    stop = s.stop.strftime("%Y-%m-%d %H:%M:%S")
    cpucount = s.cpucount
    ifaces = ", ".join(s.ifaces)
    iodevs = ", ".join(s.iodevs)
    ramsize = s.ramsize_gb
    swapsize = s.swapsize_gb

    summary=""
    data = s.get_averages()
    keys = sorted(data.keys())
    for k in keys:
        tmp = " %s(%.2lf)" %(k, data[k])
        if (summary.split("\n")[-1] + tmp).__len__() > 79:
            summary += "\n"
        summary += tmp
    print tmpl % locals()
