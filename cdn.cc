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


//static void P2PDropPacket(uint32_t chid,/* channel ID */
//							Ptr<const Packet> pkt, /*Packet being transmitted*/
//							Ptr<NetDevice> outdev,    /*Transmitting NetDevice*/
//							Ptr<NetDevice> indev,    /* Receiving NetDevice */
//							Time outT,              /* Amount of time to transmit the pkt */
//							Time inT              /* Last bit receive time (relative to now) */)
//{
//	cout<<"Drop Packet: channel="<<chid<<" pkt="<<pkt;
//}
		 //TracedCallback<Ptr<const Packet> > m_macRxDropTrace;
static void P2PDropPacket(Ptr<const Packet> pkt )
{
	cout<<"trace: Drop Packet: pkt="<<pkt<<endl;
}

static void TimeoutRequest(Ptr<App> app, uint32_t seq)
{
	cout<<"trace: seq="<<seq<<" is timeout"<<endl;
	NS_LOG_INFO("seq="<<seq<<" is timeout");
}

//Ptr<const InterestHeader> header, Ptr<App> app, Ptr<Face> face
static void NackBack(Ptr<const InterestHeader> interest, Ptr<App> app, Ptr<Face> face)
{
	uint32_t seq = boost::lexical_cast<uint32_t> (interest->GetName ().GetComponents ().back ());
	cout<<"trace: seq="<<seq<<" is nack back"<<endl;
	//NS_LOG_INFO("seq="<<seq<<" is nack back");
}

static void ChangeProducer(Ptr<App> app, Ptr<ndn::fib::Entry> cur, Ptr<ndn::fib::Entry> tmp)
{
	stringstream msg ;
	if (cur == 0)
		msg << "trace: app=" <<app->GetId() << " change prefix to " << tmp->GetPrefix() <<" from 0" ;
	else
		msg << "trace: app=" <<app->GetId() <<  " change prefix to " << tmp->GetPrefix() << " from " << cur->GetPrefix() ;
	cout<<msg.str()<<endl;
}

// ----------------------------------------------------------------------
// -- main
// ----------------------------------------------
int main (int argc, char *argv[])
{

	LogComponentEnable("ndn.App", LOG_LEVEL_INFO);
	//LogComponentEnable("ndn.Producer", LOG_LEVEL_FUNCTION);
	//LogComponentEnable("InetTopologyReader", LOG_LEVEL_INFO);
	//LogComponentEnable("AnnotatedTopologyReader", LOG_LEVEL_INFO);
	//LogComponentEnable("ndn.fw.Nacks", LOG_LEVEL_DEBUG);
	//LogComponentEnable("ndn.cs.Lru", LOG_LEVEL_INFO);
	//LogComponentEnable("ndn.GlobalRoutingHelper", LOG_LEVEL_DEBUG);
	//LogComponentEnable("ndn.ConsumerZipfMandelbrot", LOG_LEVEL_INFO);
	//LogComponentEnable("PointToPointChannel", LOG_LEVEL_FUNCTION); //PointToPointNetDevice
	LogComponentEnable("PointToPointNetDevice", LOG_LEVEL_INFO); //PointToPointNetDevice
	//LogComponentEnable("ndn.CDNConsumer", LOG_LEVEL_FUNCTION);
	//LogComponentEnable("ndn.Consumer", LOG_LEVEL_FUNCTION);
	LogComponentEnable("ShockExperiment", LOG_LEVEL_INFO); //all-logic,function, info, debug, warn, error, uncond
	//LogComponentEnable("ndn.fib.Entry", LOG_LEVEL_FUNCTION);
	LogComponentEnable("ndn.CDNIPConsumer", LOG_LEVEL_INFO);

	stringstream  settings;




  std::string consumerClass="CDNConsumer";//consumerCbr
  std::string csSize = "0";
  std::string debug = "false";
  double duration =  1.5;
  std::string freq = "100";
  /*
   * freq = 100, perfect
   * freq = 140, 0
   * freq = 150, 2 unsatisfied requests
   * freq = 160, 16
   * freq = 170
   */
  std::string multicast = "true";
  std::string nack = "true";
  int producerN = 2;
  //int seed = 3;
  std::string tracefile = "trace";
  std::string zipfs = "1.2";


  CommandLine cmd;

  cmd.AddValue("consumerClass", "class type of consumer", consumerClass);
  cmd.AddValue("csSize", "size of CS", csSize);
  cmd.AddValue("debug", "simulation time", debug);
  cmd.AddValue("duration", "simulation time", duration);
  cmd.AddValue("freq", "Interest Freqence of consumer", freq);
  cmd.AddValue("multicast", "enable Nack or not", multicast);
  cmd.AddValue("nack", "enable Nack or not", nack);
  cmd.AddValue("producerN", "number of producers", producerN);
  //cmd.AddValue("RngRun", "seed of RNG", seed);
  cmd.AddValue("trace", "trace file", tracefile);
  cmd.AddValue("zipfs", "S of zipf", zipfs);

  cmd.Parse (argc, argv);

  UniformVariable rng = UniformVariable();
        //SeedManager::SetSeed (seed);
  if (tracefile == "trace")
  {
	  tracefile = consumerClass+"-csSize"+csSize+"-duration"+boost::lexical_cast<std::string>(duration)+
			  "-freq"+freq+"-multicast"+multicast+"-nack"+nack+"-producerN"+boost::lexical_cast<std::string>(producerN)+
			  "-RngRun"+boost::lexical_cast<std::string>(SeedManager::GetRun())+"-zipfs"+zipfs;
  }

  //Config::SetDefault ("ns3::PointToPointNetDevice::DataRate", StringValue ("1Mbps"));
  //Config::SetDefault ("ns3::PointToPointChannel::Delay", StringValue ("10ms"));
  //Config::SetDefault ("ns3::DropTailQueue::MaxPackets", StringValue("5"));
  Config::SetDefault("ns3::ndn::fw::Nacks::EnableNACKs", StringValue(nack));


    AnnotatedTopologyReader topologyReader ("", 10);

    topologyReader.SetFileName ("examples/shock/input/7018.r0-conv-annotated.txt");
    if (debug == "true")
    {
    topologyReader.SetFileName ("examples/shock/input/topo-6-node.txt");
    }
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
//    std::list<TopologyReader::Link> links = topologyReader.GetLinks();
//    TopologyReader::Link::iterator iter = links.begin();
//    while (iter != links.end())
//    {
//    	TopologyReader::Link lk = *iter;
//    	//TraceConnectWithoutContext("DropPointToPoint", MakeCallback(&P2PDropPacket));
//    }

    cout<<"backboneN="<<bb.GetN()<<" gatewayN="<<gw.GetN()<<" leafN="<<leaves.GetN()<<endl;
    NodeContainer producerNodes;
    NodeContainer consumerNodes;



    uint32_t gwN = gw.GetN();
    int *flag = new int[gwN];
    for (uint32_t i=0; i<gwN; i++){
  	  flag[i] = 0;
    }



    stringstream oss;
    oss.str ("");
    oss << "/NodeList/*/DeviceList/*/$ns3::PointToPointNetDevice/TxQueue/Drop";
    //Config::Connect (oss.str (), MakeBoundCallback (&AsciiTraceHelper::DefaultDequeueSinkWithContext, stream));
    Config::ConnectWithoutContext(oss.str(), MakeCallback(&P2PDropPacket));
    for (int i =0; i<producerN; i++)
    {
    	int j = rng.GetInteger(0, gwN-1); //[0, totnodes-1]
    	Ptr<Node> pn = gw.Get(j);


    	if (flag[j] == 0)
    	{
    		flag[j] = 1;
    		producerNodes.Add(pn);
    	} else {
    		i--;
    	}

    }

  ndn::StackHelper ccnxHelper;
  ccnxHelper.SetForwardingStrategy ("ns3::ndn::fw::SmartFlooding");

  if (csSize == "0")
	  ccnxHelper.SetContentStore ("ns3::ndn::cs::Nocache");
  else
  {
	  ccnxHelper.SetContentStore ("ns3::ndn::cs::Lru", "MaxSize", csSize);
  }
  ccnxHelper.InstallAll ();

  ndn::GlobalRoutingHelper ccnxGlobalRoutingHelper;
  ccnxGlobalRoutingHelper.InstallAll ();


  consumerNodes.Add(leaves);

  string prefix = "/cdn";

  ndn::AppHelper consumerHelper ("ns3::ndn::"+consumerClass);
  consumerHelper.SetAttribute ("q", StringValue ("0")); // 100 interests a second
  consumerHelper.SetAttribute ("s", StringValue (zipfs)); // 100 interests a second
  consumerHelper.SetAttribute ("NumberOfContents", StringValue ("2000")); // 100 interests a second
  consumerHelper.SetAttribute ("Frequency", StringValue (freq)); // 100 interests a second


  for (NodeContainer::Iterator node = consumerNodes.Begin (); node != consumerNodes.End (); node++)
     {
	  	  string aPrefix = prefix;
 	  	Ptr<Node> pn = *node;

 	  	if (multicast == "false")
 	  	{
 	  		aPrefix = prefix + "/" + Names::FindName(pn);
 	  	}
		   consumerHelper.SetPrefix (aPrefix);


	   if (consumerClass == "CDNIPConsumer")
	   {
		   consumerHelper.SetAttribute("EnableMulticast", StringValue(multicast));
	   }

	   consumerHelper.Install (pn);

	   if (consumerClass == "CDNIPConsumer")
	   	{
	   		   pn->GetApplication(0)->TraceConnectWithoutContext("ChangeProducer", MakeCallback(&ChangeProducer));
	   	}
       pn->GetApplication(0)->TraceConnectWithoutContext("ReceivedNacks", MakeCallback(&NackBack));
       pn->GetApplication(0)->TraceConnectWithoutContext("TimeoutRequest", MakeCallback(&TimeoutRequest));
     }


  ndn::AppHelper producerHelper ("ns3::ndn::Producer");

  producerHelper.SetAttribute ("PayloadSize", StringValue("1024"));

  if (consumerClass == "CDNConsumer")
	{
	  producerHelper.SetPrefix (prefix);
	  producerHelper.Install (producerNodes);
	  ccnxGlobalRoutingHelper.AddOrigins (prefix, producerNodes);
	} else if (consumerClass == "CDNIPConsumer"){
		for (NodeContainer::Iterator node = producerNodes.Begin(); node != producerNodes.End(); node ++)
		{
			Ptr<Node> pn = *node;
			string aPrefix = prefix + "/" + Names::FindName(pn);
			NS_LOG_DEBUG("prefix = "<<aPrefix);
			producerHelper.SetPrefix(aPrefix);
			producerHelper.Install(pn);
			ccnxGlobalRoutingHelper.AddOrigins (aPrefix, pn);
		}

	}

  topologyReader.ApplyOspfMetric ();
  ndn::GlobalRoutingHelper::CalculateRoutes ();

  NS_LOG_INFO(tracefile);

  NS_LOG_INFO ("Run Simulation.");
  Simulator::Stop(Seconds(duration));
    
    if (debug == "true") 
    {
        boost::tuple< boost::shared_ptr<std::ostream>, std::list<Ptr<ndn::AppDelayTracer> > >
        tracers = ndn::AppDelayTracer::InstallAll ("examples/shock/output/cdn-over-ip/Case/app-"+tracefile+".txt");
    }


  Simulator::Run ();
  Simulator::Destroy ();
  NS_LOG_INFO ("Done.");
  return 0;
}
