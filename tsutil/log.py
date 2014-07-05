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

rule_default = {
    "time_exp": [ r"(\w+\s\d\d\s\d\d:\d\d:\d\d)", r"%b %d %H:%M:%S" ],
    "category": {
        "error":r"\[ERROR\]",
        "warn": r"\[WARN\]",
        "info": r"\[INFO\]",
        "log":  r"\[LOG\]"
    }
}

class Log(object):
    def __init__(self, fname, parser=None, callback=None, rule=None):
        self.fname = fname
        assert os.path.exists(fname)
        self.counter = {}

        #rule
        if rule:
            self._rule = rule
        else:
            self._rule = rule_default

        #parser
        if parser:
            self._do_parse = parser
        else:
            self._do_parse = self._do_parse_syslog

        #callback
        if callback:
            self._do_callback = callback
        else:
            self._do_callback = self._do_emit_stderr

    def __str__(self):
        ret = "<Parser: "
        ret += "lines:%d "% self.totallines
        for k in self.counter.keys():
            ret += "%s:%d " %(k,self.counter[k])
        ret +=">"
        return ret

    def parse(self):
        with open(self.fname) as fh:
            lines = 0
            for i, line in enumerate(fh):
                lines += 1 
                ret = self._do_parse(line)
                if ret is None:
                    self._callback(0,"unparsable")
                else:
                    self._callback(*ret)
            self.totallines = lines

    def _do_parse_syslog(self,line):
        """syslog does not contain year information, and datetime.datetime.strptime
        regards year as 1900 if year is not specified. So We need to handle it as  
        logs are generated this year.
        """
        mo = re.search(self._rule["time_exp"][0],line)
        if mo is None:
            return None
        offset = datetime.datetime.strptime(mo.group(1), self._rule["time_exp"][1]) - datetime.datetime(1900,1,1)
        t = datetime.datetime(datetime.date.today().year,1,1) + datetime.timedelta(days=offset.days, seconds=offset.seconds)
        kind = "other"
        for k in self._rule["category"].keys():
            mo2 = re.search(self._rule["category"][k],line)
            if mo2:
                kind = k
                break
        return (t,kind)

    def _callback(self,t,v):
        self.counter[v] = self.counter.get(v,0) + 1 
        return self._do_callback(t,v)

    def _do_emit_stderr(self,t,v):
        print t, v

def main(logname):
    assert os.path.exists(logname)
    with open(logname) as f:
        reader = Log(f)
        reader.parse()
        print reader

if __name__ == '__main__':
    main(sys.argv[1])
