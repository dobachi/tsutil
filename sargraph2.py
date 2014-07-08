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
import matplotlib.pylab as plt
import numpy as np
import sys

def put_text(fig,ax,target,data):
    label_ypos = ax.get_position().y1
    av = np.average(data)
    median =np.median(data)
    max = np.max(data)
    content = "%(target)s(med: %(median).1f max: %(max).1f $\mu$: %(av).1f)" %locals()
    fig.text(0.01, label_ypos, content, fontsize=8, horizontalalignment='left', verticalalignment='top')

sar = Sar(sys.argv[1])
metric_names = sorted(sar.get_metric_names())

fig, axes = plt.subplots(nrows=metric_names.__len__(), sharex=True)
fig.set_size_inches(10,24)
fig.subplots_adjust(top=0.98, left=0.45, right=0.92, bottom=0.01)
for i,ax in enumerate(axes):
    t,x = sar.get_metric2(metric_names[i])
    ax.fill_between(t,[0]*t.__len__(),x, linewidth=0, color="purple")
    ax.set_axis_off()
    put_text(fig,ax,metric_names[i],x)

fig.savefig(sys.argv[2])
