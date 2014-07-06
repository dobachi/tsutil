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
from tsutil import Log

import datetime
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.dates
import numpy as np

def count_events(t,bins=500):
    """by default, matplotlib and numpy cannot handle datetime for histogram,
    so I made this small function, wchich counts the occurence of the event
    into specified bins.
    """
    assert isinstance(t[0],datetime.datetime)
    ts = [int(d.strftime("%s")) for d in t ] #convert to epoch
    hist, bin_edges = np.histogram(ts,bins)
    t = [ datetime.datetime.fromtimestamp(s) for s in bin_edges[:-1] ] # len(bin_edges) = len(hist) +1 ]
    assert t.__len__() == hist.__len__()
    return t, hist

def make_graph(data, fname):
    fig = plt.figure(1)
    gs = GridSpec(data.keys().__len__(),1, hspace=0.1)
    min_ = min([min(data[k]) for k in data.keys()])
    max_ = max([max(data[k]) for k in data.keys()])

    for i,event in enumerate(data.keys()):
        ax = fig.add_subplot(gs[i,0])
        t, freq = count_events(data[event])
        ax.vlines(t,[0]*t.__len__(),freq)

        if i == 0:
            ax.set_title("count logs by error level")
        ax.set_xlim(min_,max_)
        ax.set_ylim(0,None)
        ax.grid(True)
        ax.set_ylabel(event)

        #set xlabel only for the last chart.
        if i != data.keys().__len__()-1:
            for xtick in ax.xaxis.get_major_ticks():
                xtick.label.set_visible(False)
        else:
            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%m/%d"))
            for xtick in ax.xaxis.get_major_ticks():
                xtick.label.set_rotation('vertical')

    fig.savefig(fname)

if __name__ == '__main__':
    fname = sys.argv[1]

    #parse
    data = []
    def cb(t,v):
        data.append((t,v)) 
    log = Log(fname,callback=cb)

    #count by group
    kinds = set([x[1] for x in data]) 
    result = {}
    for k in kinds:
        result[k] = sorted([ x[0] for x in data if x[1] == k ])
    result["total"] = sorted([x[0] for x in data])

    for r in result:
        print r, result[r].__len__()

    #make graph
    make_graph(result, "/var/www/html/tmp/j.png")

