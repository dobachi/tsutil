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
import os, sys, re, datetime, time
import subprocess 

def _normalize(name):
    """normalize metric names.
    %idle -> idle
    byte/s -> bytePs
    dev252-0 -> dev252_0
    ...
    """
    name = name.replace("%","")
    name = name.replace("/","P")
    name = name.replace("-","_")
    return name

class Sar(object):
    """This class maps sar.out to python object"""

    def __init__(self,fname="sar.out",interval=10,binabspath="/usr/bin/sar"):
        self.fname = fname
        self.sarbin = binabspath
        self.interval = interval
        assert os.path.exists(self.fname) and os.path.exists(self.sarbin)
        self._databag = {}
        self._databag_av = {}
        self._analyze()
        assert self.__str__()

    def get_metric_names(self):
        return sorted(self._databag.keys())

    def get_metric(self,mname):
        return self._databag[mname]

    def get_metric2(self,mname):
        return [
            [ datetime.datetime.fromtimestamp(i[0]) for i in self._databag[mname]],
            [ i[1] for i in self._databag[mname]],
        ]

    def get_averages(self):
        return self._databag_av

    def dump(self,fname):
        import json
        with open(fname,"w") as f:
            json.dump(self._databag, f)

    def __str__(self):
        period = "%s %s-%s" % (self.datestr, self.start_time.strftime("%H:%M:%S"), self.end_time.strftime("%H:%M:%S"))
        cpucount = self.cpucount
        ifaces = ",".join(self.ifaces)
        devs = ",".join(self.iodevs)
        memtotal = self.get_metric("mem.kbmemused")[0][1] / 1024. / 1024. / self.get_metric("mem.memused")[0][1] * 100.
        host = self.hostname
        return "<Sar %(host)s Period:[%(period)s]  CPU:[%(cpucount)d] RAM:[%(memtotal).1fGB] ifaces:[%(ifaces)s] iodevs:[%(devs)s]>" % locals()

    def _analyze(self):
        #first sar invokation
        popen = subprocess.Popen("LANG=C %s -f %s -u" %(self.sarbin, self.fname) , stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
        lines = popen.stdout.read()
        self.datestr = re.search(r"(\d\d/\d\d/\d\d)",lines.splitlines()[0]).group(1)
        self.hostname = re.search(r"\(([^)]*)\)",lines.splitlines()[0]).group(1)
        for line in lines.splitlines():
            mo = re.match(r"^(?P<time>\d\d:\d\d:\d\d)\s+", line)
            if not mo:
                continue
            if not hasattr(self,"start_time"):
                self.start_time = datetime.datetime.strptime(mo.group("time"),"%H:%M:%S")
            self.end_time = datetime.datetime.strptime(mo.group("time"),"%H:%M:%S")

        #invoke sar multiple times for getting information 
        self._parse("-b",       "io",       1)
        self._parse("-B",       "io",       1)
        self._parse("-d",       "devio",    2)
        self._parse("-P ALL",   "cpu",      2)
        self._parse("-n DEV",   "net",      2)
        self._parse("-n EDEV",  "neterr",   2)
        self._parse("-n SOCK",  "sock",     1)
        self._parse("-n IP",    "ip",       1)
        self._parse("-n EIP",   "iperr",    1)
        self._parse("-n ICMP",  "icmp",     1)
        self._parse("-n EICMP", "icmperr",  1)
        self._parse("-n TCP",   "tcp",      1)
        self._parse("-n ETCP",  "tcperr",   1)
        self._parse("-n UDP",   "udp",      1)
        self._parse("-q",       "load",     1)
        self._parse("-r",       "mem",      1)
        self._parse("-R",       "mem",      1)
        self._parse("-S",       "swap",     1)
        self._parse("-v",       "inode",    1)
        self._parse("-w",       "task",     1)
        self._parse("-W",       "swap",     1)

        #extract infomation for use
        self.cpucount = len( set( [ x.split(".")[-2] for x in self._databag.keys() if re.match(r"^cpu\.\d+\.",x)] ) )
        self.ifaces = [ iface for iface in  ( set( [ x.split(".")[-2] for x in self._databag.keys() if re.match(r"^net\.\w+\.",x)] ) ) ]
        self.iodevs = [ dev for dev in  ( set( [ x.split(".")[-2] for x in self._databag.keys() if re.match(r"^devio\.[_\w]+\.",x)] ) ) ]
        self.start = datetime.datetime.fromtimestamp(self.get_metric(self.get_metric_names()[0])[0][0])
        self.stop  = datetime.datetime.fromtimestamp(self.get_metric(self.get_metric_names()[0])[-1][0])
        self.ramsize_gb = self.get_metric("mem.kbmemused")[0][1] / 1024. / 1024. / self.get_metric("mem.memused")[0][1] * 100.
        self.swapsize_gb= self.get_metric("swap.kbswpused")[0][1] / 1024. / 1024. / self.get_metric("swap.swpused")[0][1] * 100.

    def _parse(self, option, prefix, parsetype):
        """parse the output of sar"""
        stime = self.start_time.strftime("%H:%M:%S")
        etime = self.end_time.strftime("%H:%M:%S")
        cmd = "LANG=C %s -f %s %s -s %s -e %s %d" % (self.sarbin, self.fname, option, stime, etime, self.interval)

        try:
            popen = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
            lines = popen.stdout.read().splitlines()
            header = lines[2] #version specific??

            if parsetype == 1:
                cols = header.split()[1:]
                regex    = r"^(\d\d:\d\d:\d\d)\s+"  + len(cols) * r"([-.\d]+)\s*"
                regex_av = r"^(Average:)\s+"  + len(cols) * r"([-.\d]+)\s*"
                for line in lines:
                    # Data
                    mo = re.match(regex,line)
                    if mo:
                        epoch = int(datetime.datetime.strptime(self.datestr+mo.group(1), "%m/%d/%y%H:%M:%S").strftime("%s"))
                        for i, col in enumerate(cols):
                            col = _normalize(col)
                            if "%s.%s"%(prefix,col) not in self._databag.keys():
                                self._databag["%s.%s"%(prefix,col)] = [] 
                            self._databag["%s.%s"%(prefix,col)].append( [epoch, float(mo.group(i+2))] )
                        continue
                    # Average data
                    mo = re.match(regex_av,line)
                    if mo:
                        for i, col in enumerate(cols):
                            col = _normalize(col)
                            self._databag_av["%s.%s"%(prefix,col)]=float(mo.group(i+2))
                #assert at least 10 lines of data are stored.
                assert len (self._databag["%s.%s"%(prefix,_normalize(cols[0]))]) > 10 
                return

            elif parsetype == 2:
                cols = header.split()[2:]
                regex    = r"^(\d\d:\d\d:\d\d)\s+" + r"([-\w]+)\s+" + len(cols) * r"([.\d]+)\s*" 
                regex_av = r"^(Average:)\s+" + r"([-\w]+)\s+" + len(cols) * r"([.\d]+)\s*" 
                for line in lines:
                    mo = re.match(regex,line)
                    if  mo:
                        epoch = int(datetime.datetime.strptime(self.datestr+mo.group(1), "%m/%d/%y%H:%M:%S").strftime("%s"))
                        label = _normalize(mo.group(2))
                        for i, col in enumerate(cols):
                            col = _normalize(col)
                            if not "%s.%s.%s"%(prefix,label,col) in self._databag.keys():
                                self._databag["%s.%s.%s"%(prefix,label,col)] = []
                            self._databag["%s.%s.%s"%(prefix,label,col)].append([epoch,float(mo.group(i+3))])
                        continue
                    mo = re.match(regex_av,line)
                    if mo:
                        label = _normalize(mo.group(2))
                        for i, col in enumerate(cols):
                            col = _normalize(col)
                            self._databag_av["%s.%s.%s"%(prefix,label,col)]=float(mo.group(i+3))
                return
        except Exception, e:
            sys.stderr.write( "Error while parsing sar %s\n" %(option))

if __name__ == '__main__':
    pass
