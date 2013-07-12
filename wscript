## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-

def build(bld):
    obj = bld.create_ns3_program('cdn', ['ndnSIM'])
    obj.source = 'cdn.cc'

    obj = bld.create_ns3_program('cdn-nodedown', ['ndnSIM'])
    obj.source = 'cdn-nodedown.cc'

    obj = bld.create_ns3_program('cdn-linkfail', ['ndnSIM'])
    obj.source = 'cdn-linkfail.cc'

    obj = bld.create_ns3_program('test', ['ndnSIM'])
    obj.source = 'test.cc'
