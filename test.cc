/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2011-2012 University of California, Los Angeles
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author: Alexander Afanasyev <alexander.afanasyev@ucla.edu>
 */
// ndn-grid.cc
#include <ctime>

#include <sstream>
#include "ns3/ptr.h"
#include "ns3/log.h"
#include "ns3/simulator.h"
#include "ns3/packet.h"
#include "ns3/callback.h"
#include "ns3/string.h"

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/animation-interface.h"
#include "ns3/ndn-app-face.h"
#include "ns3/ndn-interest.h"
#include "ns3/ndn-content-object.h"
#include "ns3/ndnSIM-module.h"
#include "ns3/ndn-app.h"
#include "../src/ndnSIM/apps/cdn-ip-consumer.h"
//#include "ns3/ndn-producer.h"
#include "../src/ndnSIM/apps/ndn-producer.h"
#include "../src/ndnSIM/model/fib/ndn-fib-entry.h"
#include <boost/foreach.hpp>
#include <boost/ref.hpp>
#include <boost/lexical_cast.hpp>

#include "ns3/topology-read-module.h"
//#include "../../internet/model/rtt-estimator.h"
#include "ns3/inet-topology-reader.h"
#include <list>
#include <ns3/ndnSIM/utils/tracers/ndn-app-delay-tracer.h>
#include <vector>
#include <map>


using namespace ns3;
using namespace std;

/**
 * This scenario simulates a grid topology (using PointToPointGrid module)
 *
 * (consumer) -- ( ) ----- ( )
 *     |          |         |
 *    ( ) ------ ( ) ----- ( )
 *     |          |         |
 *    ( ) ------ ( ) -- (producer)
 *
 * All links are 1Mbps with propagation 10ms delay.
 *
 * FIB is populated using NdnGlobalRoutingHelper.
 *
 * Consumer requests data from producer with frequency 100 interests per second
 * (interests contain constantly increasing sequence number).
 *
 * For every received interest, producer replies with a data packet, containing
 * 1024 bytes of virtual payload.
 *
 * To run scenario and see what is happening, use the following command:
 *
 *     NS_LOG=ndn.Consumer:ndn.Producer ./waf --run=ndn-grid
 */


void disableLink(Ptr<ndn::Face> face1, Ptr<ndn::Face> face2)
{
	face1->SetUp(false);
	face2->SetUp(false);
	cout<<Simulator::Now().ToDouble(Time::MS)<<"\tdisable link"<<endl;
}

void enableLink(Ptr<ndn::Face> face1, Ptr<ndn::Face> face2)
{
	face1->SetUp(true);
	face2->SetUp(true);
	cout<<Simulator::Now().ToDouble(Time::MS)<<"\tenable link"<<endl;
}

int
main (int argc, char *argv[])
{
  // Setting default parameters for PointToPoint links and channels
//  Config::SetDefault ("ns3::PointToPointNetDevice::DataRate", StringValue ("1Mbps"));
//  Config::SetDefault ("ns3::PointToPointChannel::Delay", StringValue ("10ms"));
  Config::SetDefault ("ns3::DropTailQueue::MaxPackets", StringValue ("10"));

  // Read optional command-line parameters (e.g., enable visualizer with ./waf --run=<> --visualize
  CommandLine cmd;
  cmd.Parse (argc, argv);

  Config::SetDefault("ns3::ndn::fw::Nacks::EnableNACKs", StringValue("true"));

    AnnotatedTopologyReader topologyReader ("", 10);


    topologyReader.SetFileName ("examples/shock/input/topo-6-node.txt");
    	topologyReader.Read ();


      NodeContainer leaves;
      NodeContainer gw;
      NodeContainer bb;

    NodeContainer nodes = topologyReader.GetNodes();
    //std::list<Link> links = topologyReader.GetLinks();
    for (NodeContainer::Iterator node = nodes.Begin (); node != nodes.End (); node++)
    {
    	Ptr<Node> pn = *node;

    	if (Names::FindName (pn).compare (0, 5, "leaf-")==0)
		  {
			leaves.Add (pn);
		  }
		else if (Names::FindName (pn).compare (0, 3, "gw-")==0)
		  {
			gw.Add (pn);
		  }
		else if (Names::FindName (pn).compare (0, 3, "bb-")==0)
		  {
			bb.Add (pn);
		  }
    }


  // Install NDN stack on all nodes
  ndn::StackHelper ndnHelper;
  ndnHelper.SetForwardingStrategy ("ns3::ndn::fw::SmartFlooding");
  //ndnHelper.SetContentStore("ns3::ndn::cs::CDNContentStore::Lru");
  ndnHelper.InstallAll ();

  // Installing global routing interface on all nodes
  ndn::GlobalRoutingHelper ndnGlobalRoutingHelper;
  ndnGlobalRoutingHelper.InstallAll ();

  NodeContainer producerNodes;
  // Getting containers for the consumer/producer

  // Install NDN applications
  std::string prefix = "/prefix";

  ndn::AppHelper consumerHelper ("ns3::ndn::ConsumerCbr");
  consumerHelper.SetPrefix (prefix);
  consumerHelper.SetAttribute ("Frequency", StringValue ("100")); // 100 interests a second
  consumerHelper.Install (leaves);

  ndn::AppHelper producerHelper ("ns3::ndn::Producer");
  producerHelper.SetPrefix (prefix);
  producerHelper.SetAttribute ("PayloadSize", StringValue("1024"));
  producerHelper.Install (producerNodes);
  ndnGlobalRoutingHelper.AddOrigins (prefix, producerNodes);

  producerHelper.SetPrefix(prefix);
  producerHelper.Install(gw);
  ndnGlobalRoutingHelper.AddOrigins(prefix, gw);

  // Add /prefix origins to ndn::GlobalRouter


  // Calculate and install FIBs
  ndn::GlobalRoutingHelper::CalculateRoutes ();
  Ptr<Node> node1 = Names::Find<Node>("bb-2");
  Ptr<Node> node2 = Names::Find<Node>("gw-1");


  //AnimationInterface::SetNodeColor(node1, 255, 0, 0);

  Ptr<ndn::L3Protocol> ndn1 = node1->GetObject<ndn::L3Protocol> ();
  Ptr<ndn::L3Protocol> ndn2 = node2->GetObject<ndn::L3Protocol> ();

  // iterate over all faces to find the right one
  for (uint32_t faceId = 0; faceId < ndn1->GetNFaces (); faceId++)
    {
      Ptr<ndn::NetDeviceFace> ndFace = ndn1->GetFace (faceId)->GetObject<ndn::NetDeviceFace> ();
      if (ndFace == 0) continue;

      Ptr<PointToPointNetDevice> nd1 = ndFace->GetNetDevice ()->GetObject<PointToPointNetDevice> ();
      if (nd1 == 0) continue;

      Ptr<Channel> channel = nd1->GetChannel ();
      if (channel == 0) continue;

      Ptr<PointToPointChannel> ppChannel = DynamicCast<PointToPointChannel> (channel);

      Ptr<NetDevice> nd2 = ppChannel->GetDevice (0);
      if (nd2->GetNode () == node1)
        nd2 = ppChannel->GetDevice (1);

      if (nd2->GetNode () == node2)
        {
          Ptr<ndn::Face> face1 = ndn1->GetFaceByNetDevice (nd1);
          Ptr<ndn::Face> face2 = ndn2->GetFaceByNetDevice (nd2);

          Simulator::Schedule(Seconds(5.0), disableLink, face1, face2);
          Simulator::Schedule(Seconds(15.0), enableLink, face1, face2);
          cout<<"disable the link"<<endl;
          break;
        }
    }


  Simulator::Stop (Seconds (25.0));

  Simulator::Run ();
  Simulator::Destroy ();

  return 0;
}
