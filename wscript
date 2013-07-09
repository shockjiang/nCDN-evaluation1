## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-

def build(bld):
    obj = bld.create_ns3_program('cdn', ['ndnSIM'])
    obj.source = 'cdn.cc'

    obj = bld.create_ns3_program('cdn-reliability', ['ndnSIM'])
    obj.source = 'cdn-reliability.cc'

    #obj = bld.create_ns3_program('shock', ['ndnSIM'])
    #obj.source = 'test.cc'
