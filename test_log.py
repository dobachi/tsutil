from tsutil import Log

def test_log1():
    log = Log("tests/message")
    log.parse()
    assert log.totallines > 100
    
def test_log2():
    ret = []
    def callback(t,v):
        ret.append( (t,v) )
    log = Log("tests/message",callback=callback)
    log.parse()
    assert ret.__len__() > 100

    
