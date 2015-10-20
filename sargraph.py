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
import sys, re, datetime
import subprocess 
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.ticker as ticker
import numpy as np
from optparse import OptionParser

from tsutil import Sar

CANVAS_SIZE = (10,20) #in inch

class SarGraph(object):
    def __init__(self, sars=[], targets=["LOAD","CPU","MEM","DISK","NET"], verbose=False):
        self.sars = sars
        self.targets = targets
        self.verbose = verbose

    def dump(self,fname="/var/www/html/tmp/a.png"):
        assert len(self.sars) > 0
        self.x_start = min( [ s.get_metric2(s.get_metric_names()[0])[0][0] for s in self.sars] )
        self.x_stop  = max( [ s.get_metric2(s.get_metric_names()[0])[0][-1] for s in self.sars] ) 

        fig = plt.figure(1)
        fig.set_size_inches(*CANVAS_SIZE)
        title = "Sar Info: %s  %s - %s  @%s " % (s.datestr, self.x_start.strftime("%H:%M:%S"), self.x_stop.strftime("%H:%M:%S"), s.hostname)
        fig.text(0.03, 0.99, title, horizontalalignment='left', verticalalignment='top')
        fig.subplots_adjust(top=0.95, left=0.35, right=0.92)

        row_weights = self._get_row_weights()
        gs = GridSpec(len(row_weights), 1, height_ratios=row_weights, hspace=0.05)
        offset = 0
        if "LOAD" in self.targets:
            for s in self.sars:
                ax = fig.add_subplot(gs[offset,0])
                self._do_make_graph_load(s,ax,fig)
                offset += 1
        if "CPU" in self.targets:
            for s in self.sars:
                ax = fig.add_subplot(gs[offset,0])
                self._do_make_graph_cpu(s,ax,fig)
                offset += 1
                if self.verbose:
                    for cpuid in range(s.get_cpucount()):
                        ax = fig.add_subplot(gs[offset,0])
                        self._do_make_graph_cpu(s,ax,fig,cpuid)
                        offset += 1
        if "MEM" in self.targets:
            for s in self.sars:
                ax = fig.add_subplot(gs[offset,0])
                self._do_make_graph_mem1(s,ax,fig)
                offset += 1
                ax = fig.add_subplot(gs[offset,0])
                self._do_make_graph_mem2(s,ax,fig)
                offset += 1
        if "DISK" in self.targets:
            for s in self.sars:
                ax = fig.add_subplot(gs[offset,0])
                self._do_make_graph_disk1(s,ax,fig)
                offset += 1
                for devname in s.iodevs:
                    ax = fig.add_subplot(gs[offset,0])
                    self._do_make_graph_disk_detail(s,ax,fig,devname)
                    offset += 1
                    ax = fig.add_subplot(gs[offset,0])
                    self._do_make_graph_disk_detail2(s,ax,fig,devname)
                    offset += 1
        if "NET" in self.targets:
            for s in self.sars:
                ax = fig.add_subplot(gs[offset,0])
                self._do_make_graph_network1(s,ax,fig)
                offset +=1
            for s in self.sars:
                for iface in s.ifaces:
                    ax = fig.add_subplot(gs[offset,0])
                    self._do_make_graph_network_iface(s,ax,fig,iface)
                    offset += 1
        plt.savefig(fname)

    def _get_row_weights(self):
        ret = []
        if "LOAD" in self.targets:
            for i in range(self.sars.__len__()):
                ret.extend([1])
        if "CPU" in self.targets:
            for i in range(self.sars.__len__()):
                ret.extend([1])
                if self.verbose:
                    ret.extend([1]*s.cpucount())
        if "MEM" in self.targets:
            for i in range(self.sars.__len__()):
                ret.extend([1]) #MEM
                ret.extend([1]) #swap
        if "DISK" in self.targets:
            for i in range(self.sars.__len__()):
                ret.extend([1]) #IO(ALL)
                ret.extend([1]*len(sar.iodevs)*2) #DISK(indivisual)
        if "NET" in self.targets:
            for i in range(self.sars.__len__()):
                ret.extend([1]) #SOCKET
                ret.extend([1]*len(sar.ifaces))
        return ret

    def __draw_tmpl(self,ax,ylabels,ylims=None):
        ax2 = ax.twinx()
        ax.grid(True)
        ax.set_xlim(self.x_start,self.x_stop)
        ax2.set_xlim(self.x_start,self.x_stop)

        ax.set_ylabel(ylabels[0])
        if ylabels[1]:
            ax2.set_ylabel(ylabels[1])
        for xtick in ax.xaxis.get_major_ticks():
            xtick.label.set_rotation('vertical')
        for ytick in ax.yaxis.get_major_ticks():
            ytick.label.set_visible(False)
        ax.yaxis.get_major_ticks()[-1].label.set_visible(True)
        for ytick in ax2.yaxis.get_major_ticks():
            ytick.label2.set_visible(False)
        if ylabels[1]:
            ax2.yaxis.get_major_ticks()[-1].label2.set_visible(True)
        if ylims:
            ax.set_ylim(*ylims[0])
            if ylabels[1]:
                ax2.set_ylim(*ylims[1])
        return ax,ax2

    def __put_text(self,fig,ax,content):
        label_ypos = ax.get_position().y1
        fig.text(0.03, label_ypos, content, horizontalalignment='left', verticalalignment='top')

    def _do_make_graph_load(self,s,ax,fig):
        x1, y1 = s.get_metric2("task.procPs")
        x2, y2 = s.get_metric2("task.cswchPs")
        ax, ax2 = self.__draw_tmpl(ax, ["proc","cs"])
        ax.plot(x1, y1,color="black")
        ax2.plot(x2, y2, color="orange", alpha=0.8)
        ax2.yaxis.label.set_color("orange")
        ax2.tick_params(axis='y', colors="orange")
        self.__put_text(fig,ax,"LOAD")

    def _do_make_graph_cpu(self,s,ax,fig):
        x1, y1 = s.get_metric2("cpu.all.user")
        x2, y2 = s.get_metric2("cpu.all.system")
        x3, y3 = s.get_metric2("cpu.all.iowait")
        x4, y4 = s.get_metric2("cpu.all.idle")
        assert len(x1) == len (x2) and len(x1) == len (x3) and len(x1) == len(x4)
        ax, _ = self.__draw_tmpl(ax,["Use[%]",""],[(0,100),(None,None)])
        ax.stackplot(x1, y1, y2, y3, y4, colors=["orange","blue","purple","0.75"],linewidth=0)
        self.__put_text(fig,ax,"CPU")

    def _do_make_graph_cpu_detail(self,s,ax,fig,i):
        x1, y1 = s.get_metric2("cpu.%d.user" %(cpuid,))
        x2, y2 = s.get_metric2("cpu.%d.system"%(cpuid,))
        x3, y3 = s.get_metric2("cpu.%d.iowait"%(cpuid,))
        x4, y4 = s.get_metric2("cpu.%d.idle"%(cpuid,))
        assert len(x1) == len (x2) and len(x1) == len (x3) and len(x1) == len(x4)
        ax.set_ylim(0,100)
        ax.set_xlim(self.x_start,self.x_stop)
        ax.grid(True)
        ax.stackplot(x1, y1, y2, y3, y4, colors=["red","blue","purple","0.75"],linewidth=0)
        ax.set_yticklabels([])
        for xtick in ax.xaxis.get_major_ticks():
            xtick.label.set_rotation('vertical')
        label_ypos = ax.get_position().y1
        fig.text(0.03, label_ypos, "    CPU#%d"%(cpuid,), horizontalalignment='left', verticalalignment='top')

    def _do_make_graph_mem1(self,s,ax,fig):
        x1, y1_ = s.get_metric2("mem.kbmemused")
        x2, y2_ = s.get_metric2("mem.kbbuffers")
        x3, y3_ = s.get_metric2("mem.kbcached")
        x4, y4 = s.get_metric2("swap.pswpinPs")
        x5, y5 = s.get_metric2("swap.pswpoutPs")
        y1 = [ y / 1024. for y in y1_ ]
        y2 = [ y / 1024. for y in y2_ ]
        y3 = [ y / 1024. for y in y3_ ]
        assert len(x1) == len (x2) and len(x1) == len (x3)
        ax, ax2 = self.__draw_tmpl(ax,["Use[MB]","swapcount"])
        ax.stackplot(x1, y1, y2, y3, colors=["orange","0.50","0.75"],linewidth=0)
        ax.set_ylim(0,None)
        ax2.vlines(x4, [0], y4, colors=["red"])
        ax2.vlines(x5, [0], [-y for y in y5] , colors=["blue"])
        _ = 1.1 * max([max(y4),max(y5)])
        ax2.set_ylim(-_,_)
        ax2.yaxis.label.set_color("red")
        ax2.tick_params(axis='y', colors="red")
        self.__put_text(fig,ax,"RAM")

    def _do_make_graph_mem2(self,s,ax,fig):
        x1, y1_ = s.get_metric2("swap.kbswpused")
        x2, y2_ = s.get_metric2("swap.kbswpfree")
        y1 = [ y / 1024. for y in y1_ ]
        y2 = [ y / 1024. for y in y2_ ]
        assert len(x1) == len (x2)
        ax, _ = self.__draw_tmpl(ax,["Use[MB]",""])
        ax.stackplot(x1, y2, y1, colors=["0.75","orange"], linewidth=0)
        self.__put_text(fig,ax,"swap")

    def _do_make_graph_disk1(self,s,ax,fig):
        x1, y1_ = s.get_metric2("io.breadPs") 
        x2, y2_ = s.get_metric2("io.bwrtnPs") 
        y1 = [ y * 512 /1024. /1024. for y in y1_ ] 
        y2 = [ y * 512 /1024. /1024. for y in y2_ ] 
        assert len(x1) == len(x2)
        x = x1
        ax ,_ = self.__draw_tmpl(ax,["R/W[MB]",None])
        ax.fill_between(x,y1,color="orange",edgecolor="orange")
        ax.fill_between(x,[-y for y in y2],color="purple",edgecolor="purple")
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x,pos: abs(x)))
        self.__put_text(fig,ax,"Disk")

    def _do_make_graph_disk_detail(self,s,ax,fig,devname):
        x1, y1_ = s.get_metric2("devio.%s.rd_secPs" % (devname,) ) 
        x2, y2_ = s.get_metric2("devio.%s.wr_secPs" % (devname,) )
        y1 = [ y * 512 /1024. /1024. for y in y1_] 
        y2 = [ y * 512 /1024. /1024. for y in y2_] 
        assert len(x1) == len(x2)
        x = x1
        ax, _  = self.__draw_tmpl(ax,["R/W[MB]",None])
        ax.fill_between(x,y1,color="orange",edgecolor="orange")
        ax.fill_between(x,[-y for y in y2],color="purple",edgecolor="purple")
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x,pos: abs(x)))
        self.__put_text(fig,ax,"Disk[%(devname)s]" % locals())

    def _do_make_graph_disk_detail2(self,s,ax,fig,devname):
        x1, y1 = s.get_metric2("devio.%s.util" % (devname,) )
        x2, y2 = s.get_metric2("devio.%s.await" % (devname,) )
        ax,ax2  = self.__draw_tmpl(ax,["util","await"],[[0,100],[0,max(y2)*1.1]])
        ax.plot(x1,y1, color="black")
        ax2.plot(x2,y2, color="orange", alpha=0.75)
        ax2.yaxis.label.set_color("orange")
        ax2.tick_params(axis='y', colors="orange")

    def _do_make_graph_network1(self,s,ax,fig):
        x1, y1 = s.get_metric2("sock.tcpsck")
        x2, y2 = s.get_metric2("sock.tcp_tw")
        x3, y3 = s.get_metric2("sock.totsck")
        ax, ax2 = self.__draw_tmpl(ax,["tcpsock","total"])
        ax.stackplot(x1,y2,y1, colors=["orange","0.75"], linewidth=0)
        ax2.plot(x3,y3, color="purple")
        ax2.yaxis.label.set_color("purple")
        ax2.tick_params(axis='y', colors="purple")
        self.__put_text(fig,ax,"Network(SOCK)")

    def _do_make_graph_network_iface(self,s,ax,fig,iface):
        x1, y1 = s.get_metric2("net.%s.rxkBPs" % (iface,) )
        x2, y2 = s.get_metric2("net.%s.txkBPs" % (iface,) )
        assert len(x1) == len(x2)
        x = x1
        ax, _ = self.__draw_tmpl(ax,["Rx/Tx[kB]",None])
        ax.fill_between(x,y1,color="orange",edgecolor="orange")
        ax.fill_between(x,[-y for y in y2],color="purple",edgecolor="purple")
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x,pos: abs(x)))
        self.__put_text(fig,ax,"Network[%(iface)s]" % locals())

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--interval", dest="interval",
                      help="The interval", metavar="INTEGER", default=1)
    parser.add_option("-f", "--font-size", dest="font_size",
                      help="The font size", metavar="INTEGER", default=10)


    (options, args) = parser.parse_args()
    (input_path, output_path) = args

    font = {'family' : 'normal',
            'size'   : 10}
    plt.rc('font', **font)

    sar = Sar(input_path, int(options.interval))

    g = SarGraph([sar,],targets=["LOAD","CPU","MEM","DISK","NET"])
    g.dump(output_path)
