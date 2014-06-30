import tsutil
import datetime

def test_sar1():
    sar = tsutil.Sar("tests/sar.out")
    assert sar.cpucount == 2
    assert sar.get_metric_names().__len__() > 10
    m = sar.get_metric_names()[0]
    values = sar.get_metric(m)
    assert values.__len__() > 100
    assert values[0].__len__() == 2 and \
           isinstance(values[0][0],int) and \
           isinstance(values[0][1],float)

def test_sar2():
    sar = tsutil.Sar("tests/sar.out")
    m = sar.get_metric_names()[0]
    values = sar.get_metric2(m)
    assert values.__len__() == 2 and \
           isinstance(values[0][0],datetime.datetime) and \
           isinstance(values[1][0],float)
    assert values[0].__len__() > 10

def test_sar3():
    sar = tsutil.Sar("tests/sar.out")
    assert sar.hostname
    assert sar.start
    assert sar.stop

