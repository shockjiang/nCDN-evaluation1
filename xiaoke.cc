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

#include <boost/lexical_cast.hpp>
#include "ns3/topology-read-module.h"

#include "ns3/inet-topology-reader.h"
#include <list>

using namespace std;
using namespace ns3;
NS_LOG_COMPONENT_DEFINE ("ShockExperiment");


//static std::list<unsigned int> data;
//typedef ns3::ndn::InterestHeader InterestHeader;

//static void SinkRx (const Ptr<const InterestHeader> &interest, Ptr<Packet> packet)
//{
//
//	//InterestHeader ist;
//	//p->PeekHeader (ist);
//	NS_LOG_DEBUG("TTL: " << interest->GetName() << std::endl);
//}
//

// ----------------------------------------------------------------------
// -- main
// ----------------------------------------------
int main (int argc, char *argv[])
{

	LogComponentEnable("ndn.App", LOG_LEVEL_INFO);
	LogComponentEnable("ndn.Producer", LOG_LEVEL_FUNCTION);
	//LogComponentEnable("InetTopologyReader", LOG_LEVEL_INFO);
	//LogComponentEnable("ndn.Consumer", LOG_LEVEL_INFO);
	//LogComponentEnable("ndn.cs.Lru", LOG_LEVEL_INFO);
	LogComponentEnable("ndn.GlobalRoutingHelper", LOG_LEVEL_DEBUG);
	LogComponentEnable("ndn.ConsumerZipfMandelbrot", LOG_LEVEL_INFO);
	LogComponentEnable("ndn.Consumer", LOG_LEVEL_INFO);
	LogComponentEnable("ShockExperiment", LOG_LEVEL_INFO); //all-logic,function, info, debug, warn, error, uncond
	LogComponentEnable("ndn.fib.Entry", LOG_LEVEL_FUNCTION);

	std::string format ("Inet");
	std::string input ("src/topology-read/examples/sprint-topology.txt");

	stringstream  settings;


  int seed = 3;
  double duration =  1.0;
  int producerNum = 2;
  std::string csSize = "ZERO";
  std::string consumerClass="ConsumerCbr";//consumerCbr
  CommandLine cmd;
  cmd.AddValue ("format", "Format to use for data input [Orbis|Inet|Rocketfuel].", format);
  cmd.AddValue ("input", "Name of the input file.", input);
  cmd.AddValue("seed", "seed of RNG", seed);
  cmd.AddValue("duration", "simulation time", duration);
  cmd.AddValue("producerNum", "number of producers", producerNum);
  cmd.AddValue("consumerClass", "class type of consumer", consumerClass);
  cmd.AddValue("csSize", "size of CS", csSize);
  string ZERO = boost::lexical_cast<string>(std::numeric_limits<uint32_t>::max ());
  if (csSize == "Zero" || csSize == "ZERO" ||csSize=="-1") {
	  csSize = ZERO;
	  NS_LOG_INFO("2csSize="<<csSize);
  }else{
	  NS_LOG_INFO("csSize="<<csSize);
  }


  cmd.Parse (argc, argv);
  settings<<"#seed="<<seed<<" duration="<<duration<<" producerNum="<<producerNum<<" csSize="<<csSize<<" consumerClass="<<consumerClass;


  Config::SetDefault ("ns3::PointToPointNetDevice::DataRate", StringValue ("10Mbps"));
  Config::SetDefault ("ns3::PointToPointChannel::Delay", StringValue ("10ms"));
  Config::SetDefault ("ns3::DropTailQueue::MaxPackets", StringValue("20"));
  Config::SetDefault("ns3::ndn::fw::Nacks::EnableNACKs", StringValue("true"));

  Ptr<TopologyReader> inFile = 0;
  TopologyReaderHelper topoHelp;

  NodeContainer nodes;

  topoHelp.SetFileName (input);
  topoHelp.SetFileType (format);
  inFile = topoHelp.GetTopologyReader ();

  if (inFile != 0)
    {
      nodes = inFile->Read ();
    }

  if (inFile->LinksSize () == 0)
    {
      NS_LOG_ERROR ("Problems reading the topology file. Failing.");
      return -1;
    }
   int totlinks = inFile->LinksSize ();
   int totnodes = nodes.GetN();

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
  ccnxHelper.SetForwardingStrategy ("ns3::ndn::fw::BestRoute");

  ccnxHelper.SetContentStore ("ns3::ndn::cs::Lru", "MaxSize", csSize);
  ccnxHelper.InstallAll ();

  SeedManager::SetSeed (seed);

  ndn::GlobalRoutingHelper ccnxGlobalRoutingHelper;
  ccnxGlobalRoutingHelper.InstallAll ();

  UniformVariable rng = UniformVariable();
  int *nodesFlag = new int[totnodes];
  for (int i=0; i<totnodes; i++) {
	  nodesFlag[i] = 0;
  }
  int *producersID = new int[producerNum];
  for (int i=0; i<producerNum; i++){
	  producersID[i] = -1;

  }
  for (int i=0; i<producerNum; i++){
	  //SeedManager::SetSeed (seed+seed*i);  // Changes seed from default of 1 to 3
	  int pdc = rng.GetInteger(0, totnodes-1); //[0, totnodes-1]
	  if (nodesFlag[pdc] >0){
		  i--;
		  continue;
	  }
	  nodesFlag[pdc] = 1;
	  producersID[i] = pdc;
	  settings<<"\n #producer"<<i<<"="<<pdc;
	  NS_LOG_LOGIC("add a producer node id="<<pdc);
  }//for i

  std::string prefix = "/prefix";
  Ptr<Node> node;
  ndn::AppHelper producerHelper("ns3::ndn::Producer");
  ndn::AppHelper consumerHelper("ns3::ndn::"+consumerClass);
  std::string aPrefix;



  for (int i=0; i<totnodes; i++){
	  stringstream strStream;
	  node = nodes.Get(i);
	  if (nodesFlag[i] ==0){
		  int pdc = i % producerNum;
		  pdc = producersID[pdc];

		  strStream << pdc;
		  aPrefix = prefix + "/"+strStream.str();
		  NS_LOG_LOGIC("prefix="<<aPrefix<<" attached to node "<<i);
		  consumerHelper.SetPrefix(aPrefix);
		  consumerHelper.SetAttribute("Frequency", StringValue("50"));
		  consumerHelper.SetAttribute ("Randomize", StringValue ("exponential"));
		  consumerHelper.Install(node);
	  } else if (nodesFlag[i] == 1){
		  strStream <<i;
		  aPrefix = prefix + "/"+strStream.str();
		  producerHelper.SetPrefix(aPrefix);
		  producerHelper.SetAttribute ("PayloadSize", StringValue("100"));
		  producerHelper.Install(node);
		  ccnxGlobalRoutingHelper.AddOrigin(prefix, node);
	  }
  }


  ccnxGlobalRoutingHelper.CalculateRoutes ();

  NS_LOG_INFO(settings.str());



  NS_LOG_INFO ("Run Simulation.");
  Simulator::Stop(Seconds(duration));
  Simulator::Run ();
  Simulator::Destroy ();

  delete[] producersID;
  delete[] nodesFlag;

  NS_LOG_INFO ("Done.");

  return 0;

  // end main
}
