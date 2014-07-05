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
import sys
import os
import re
import datetime

class Reader(object):
    rule = {
        "time_exp": [ r"(\w+\s\d\d\s\d\d:\d\d:\d\d)", r"%b %d %H:%M:%S" ],
        "category": {
            "error":r"\[ERROR\]",
            "warn": r"\[WARN\]",
            "info": r"\[INFO\]",
            "log":  r"\[LOG\]"
        }
    }

    def __init__(self, fh, rule=None):
        self.fh = fh
        self.counter = {}
        #setting
        self._do_parse = self._do_parse_syslog
        self._do_emit = self._do_emit_stderr
        self.rule = self.__class__.rule

    def __str__(self):
        ret = "<Parser: "
        ret += "lines:%d "% self.totallines
        for k in self.counter.keys():
            ret += "%s:%d " %(k,self.counter[k])
        ret +=">"
        return ret

    def parse(self):
        lines = 0
        for i, line in enumerate(self.fh):
            lines += 1 
            ret = self._do_parse(line)
            if ret is None:
                self._emit(0,"unparsable")
            else:
                self._emit(*ret)
        self.totallines = lines

    def _emit(self,t,v):
        self.counter[v] = self.counter.get(v,0) + 1 
        self._do_emit(t,v)

    def _do_emit_stderr(self,t,v):
        print t, v

    def _do_parse_syslog(self,line):
        mo = re.search(self.rule["time_exp"][0],line)
        if mo is None:
            return None
        offset = datetime.datetime.strptime(mo.group(1), self.rule["time_exp"][1]) - datetime.datetime(1900,1,1)
        t = datetime.datetime(datetime.date.today().year,1,1) + datetime.timedelta(days=offset.days, seconds=offset.seconds)
        kind = "other"
        for k in self.rule["category"].keys():
            mo2 = re.search(self.rule["category"][k],line)
            if mo2:
                kind = k
                break
        return (t,kind)

def main(logname):
    assert os.path.exists(logname)
    with open(logname) as f:
        reader = Reader(f)
        reader.parse()
        print reader

if __name__ == '__main__':
    main(sys.argv[1])
