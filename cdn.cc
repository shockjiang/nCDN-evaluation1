/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
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
 * Author: Tommaso Pecorella <tommaso.pecorella@unifi.it>
 * Author: Valerio Sartini <valesar@gmail.com>
 *
 * This program conducts a simple experiment: It builds up a topology based on
 * either Inet or Orbis trace files. A random node is then chosen, and all the
 * other nodes will send a packet to it. The TTL is measured and reported as an histogram.
 *
 */

#include <ctime>

#include <sstream>
//#include <sstream>
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

#include "ns3/ndn-app-face.h"
#include "ns3/ndn-interest.h"
#include "ns3/ndn-content-object.h"
#include "ns3/ndnSIM-module.h"
#include "ns3/ndn-app.h"
#include "../src/ndnSIM/apps/cdn-ip-app.h"
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



using namespace std;
using namespace ns3;
using namespace ndn;
NS_LOG_COMPONENT_DEFINE ("ShockExperiment");


//static std::list<unsigned int> data;
//typedef ns3::ndn::InterestHeader InterestHeader;
//static void TraceStatus(fib::FaceMetric::Status old, fib::FaceMetric::Status now) {
//	NS_LOG_INFO("- Change Status from "<<old<<" to "<<now);
//}
//
//static void SinkIst(Ptr<const InterestHeader> header, Ptr<App> app, Ptr<Face> face)
//{
//	NS_LOG_INFO("+ Respodning with ContentObject "<< boost::cref(*header));
//}
//static void SinkRx (const Ptr<const InterestHeader> &interest, Ptr<Packet> packet)
//{
//
//	//InterestHeader ist;
//	//p->PeekHeader (ist);
//	NS_LOG_DEBUG("TTL: " << interest->GetName() << std::endl);
//}
//
//static void IstRtt(RttEstimator old_rtt, RttEstimator new_rtt){
//	cout<<old_rtt<<new_rtt<<endl;
//}
// ----------------------------------------------------------------------
// -- main
// ----------------------------------------------
int main (int argc, char *argv[])
{

	LogComponentEnable("ndn.App", LOG_LEVEL_INFO);
	LogComponentEnable("ndn.Producer", LOG_LEVEL_FUNCTION);
	LogComponentEnable("InetTopologyReader", LOG_LEVEL_INFO);
	LogComponentEnable("AnnotatedTopologyReader", LOG_LEVEL_INFO);
	LogComponentEnable("ndn.fw.Nacks", LOG_LEVEL_DEBUG);
	//LogComponentEnable("ndn.cs.Lru", LOG_LEVEL_INFO);
	LogComponentEnable("ndn.GlobalRoutingHelper", LOG_LEVEL_DEBUG);
	LogComponentEnable("ndn.ConsumerZipfMandelbrot", LOG_LEVEL_INFO);
	LogComponentEnable("ndn.Consumer", LOG_LEVEL_INFO);
	LogComponentEnable("ShockExperiment", LOG_LEVEL_INFO); //all-logic,function, info, debug, warn, error, uncond
	LogComponentEnable("ndn.fib.Entry", LOG_LEVEL_FUNCTION);
	LogComponentEnable("ndn.CDNIPApp", LOG_LEVEL_INFO);

	stringstream  settings;


  int seed = 3;
  double duration =  3.0;
  int producerNum = 2;
  std::string csSize = "1";
  std::string consumerClass="ConsumerCbr";//consumerCbr
  std::string nack = "true";
  std::string tracefile = "";

  CommandLine cmd;
  cmd.AddValue ("format", "Format to use for data input [Orbis|Inet|Rocketfuel].", format);
  cmd.AddValue ("input", "Name of the input file.", input);
  cmd.AddValue("seed", "seed of RNG", seed);
  cmd.AddValue("duration", "simulation time", duration);
  cmd.AddValue("producerNum", "number of producers", producerNum);
  cmd.AddValue("consumerClass", "class type of consumer", consumerClass);
  cmd.AddValue("csSize", "size of CS", csSize);
  cmd.AddValue("nack", "enable Nack or not", nack);
  cmd.AddValue("trace", "trace file", tracefile);
  cmd.Parse (argc, argv);

  settings<<"#seed="<<seed<<" duration="<<duration<<" producerNum="<<producerNum<<" csSize="<<csSize<<" consumerClass="<<consumerClass;
  settings<<" nack="<<nack<<" trace="<<tracefile;


  Config::SetDefault ("ns3::PointToPointNetDevice::DataRate", StringValue ("1Mbps"));
  //Config::SetDefault ("ns3::PointToPointChannel::Delay", StringValue ("10ms"));
  //Config::SetDefault ("ns3::DropTailQueue::MaxPackets", StringValue("5"));
  Config::SetDefault("ns3::ndn::fw::Nacks::EnableNACKs", StringValue(nack));

    AnnotatedTopologyReader topologyReader ("", 1);
    topologyReader.SetFileName ("examples/shock/input/7018.r0-conv-annotated.txt");
    topologyReader.Read ();
    NodeContainer nodes = topologyReader.GetNodes();
    std::list<Link> links = topologyReader.GetLinks();
    
   NS_LOG_INFO("NodesSize="<<totnodes<<", LinksSize="<<totlinks);
   settings<<"\nnodesSize="<<totnodes<<" linksSize="<<totlinks;

  //NodeContainer nodes;
  TopologyReader::ConstLinksIterator iter;
  int i = 0;

  PointToPointHelper p2p;
  for ( iter = inFile->LinksBegin (); iter != inFile->LinksEnd (); iter++, i++ )
    {
      p2p.Install(iter->GetFromNode(), iter->GetToNode());
      NS_LOG_LOGIC("p2p link "<<i<<" : from "<<iter->GetFromNode()->GetId()<<" to "<<iter->GetToNode()->GetId());
    }
  ndn::StackHelper ccnxHelper;
  ccnxHelper.SetForwardingStrategy ("ns3::ndn::fw::BestRoute::PerOutFaceLimits",
  									  "Limit", "ns3::ndn::Limits::Rate");
//  ccnxHelper.EnableLimits(true, Seconds(0.1), 1100, 50);

//  ccnxHelper.SetForwardingStrategy ("ns3::ndn::fw::BestRoute");
//  if (nack == "false") {
//	  ccnxHelper.SetForwardingStrategy ("ns3::ndn::fw::BestRoute");
//  } else {
//	  ccnxHelper.SetForwardingStrategy ("ns3::ndn::fw::BestRoute::PerOutFaceLimits",
//									  "Limit", "ns3::ndn::Limits::Rate");
//	  ccnxHelper.EnableLimits(true, Seconds(0.1), 1100, 50);
//  }
  ccnxHelper.SetContentStore ("ns3::ndn::cs::Lru", "MaxSize", csSize);
  ccnxHelper.InstallAll ();

  SeedManager::SetSeed (seed);

  ndn::GlobalRoutingHelper ccnxGlobalRoutingHelper;
  ccnxGlobalRoutingHelper.InstallAll ();


  NS_LOG_INFO(settings.str());

  NS_LOG_INFO ("Run Simulation.");
  Simulator::Stop(Seconds(duration));

  boost::tuple< boost::shared_ptr<std::ostream>, std::list<Ptr<ndn::AppDelayTracer> > >
  tracers = ndn::AppDelayTracer::InstallAll (tracefile);


  Simulator::Run ();
  Simulator::Destroy ();

  NS_LOG_INFO(settings.str());
  NS_LOG_INFO ("Done.");

  return 0;

  // end main
}
