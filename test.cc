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


using namespace std;
using namespace ns3;
using namespace ndn;
NS_LOG_COMPONENT_DEFINE ("ShockTestExperiment");


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
	//LogComponentEnable("ShockExperiment", LOG_LEVEL_INFO); //all-logic,function, info, debug, warn, error, uncond
	//LogComponentEnable("ndn.fib.Entry", LOG_LEVEL_FUNCTION);
	LogComponentEnable("ndn.CDNIPConsumer", LOG_LEVEL_INFO);

	stringstream  settings;




  std::string consumerClass="CDNConsumer";//consumerCbr
  std::string csSize = "0";
  std::string debug = "false";
  double duration =  1;
  std::string freq = "70";
  /*
   * freq = 100, perfect
   * freq = 140, 0
   * freq = 150, 2 unsatisfied requests
   * freq = 160, 16
   * freq = 170
   */
  string id = "id";
  string item = "reliability";//"reliability";
  std::string multicast = "true";
  std::string nack = "true";
  int producerN = 3;
  //int seed = 3;
  std::string trace = "trace";
  std::string zipfs = "1.2";
  uint32_t retxN = 0;

  CommandLine cmd;

  cmd.AddValue("consumerClass", "class type of consumer", consumerClass);
  cmd.AddValue("csSize", "size of CS", csSize);
  cmd.AddValue("debug", "simulation time", debug);
  cmd.AddValue("duration", "simulation time", duration);
  cmd.AddValue("freq", "Interest Freqence of consumer", freq);
  cmd.AddValue("id", "id of the case", id);
  cmd.AddValue("item", "Case Item: throughput|reliability", item);
  cmd.AddValue("multicast", "enable Nack or not", multicast);
  cmd.AddValue("nack", "enable Nack or not", nack);
  cmd.AddValue("producerN", "number of producers", producerN);
  //cmd.AddValue("RngRun", "seed of RNG", seed);
  cmd.AddValue("trace", "trace file", trace);
  cmd.AddValue("zipfs", "S of zipf", zipfs);
  cmd.AddValue("retxN", "max number trials of retransmission ", retxN);
  cmd.Parse (argc, argv);

  if (consumerClass.find("IP") != std::string::npos)
  {
	  SeedManager::SetSeed (producerN* boost::lexical_cast<int>(freq));
	  printf("set seed\n");
  }
  UniformVariable rng = UniformVariable();

  string root = "examples/shock/output-debug/cdn-over-ip//Case/";
  string fp = root + id + "-latency" + ".txt";

  ofstream fo;
  ofstream latencyf;

  latencyf.open(fp.c_str());
/*
  Time	Node	AppId	SeqNo	Type	DelayS	DelayUS	RetxCount	HopCount
  0.0704256	leaf-1	1	725	LastDelay	0.0704256	70425.6	1	8
  0.0704256	leaf-1	1	725	FullDelay	0.0704256	70425.6	1	8
  0.0789072	leaf-2	1	49764	LastDelay	0.0789072	78907.2	1	8
  0.0789072	leaf-2	1	49764	FullDelay	0.0789072	78907.2	1	8
*/



  latencyf<<"Time\tNode\tAppId\tSeqNo\tType\tDelayS\tDelayUS\tRetxCount\tHopCount"<<endl;
  double tt;
  for (uint32_t i=0; i<10; i++)
  {
	  tt = rng.GetValue(0, 1);
	  latencyf<<"0.0704256\tleaf-1\t1\t725\tLastDelay\t"<<tt<<"\t"<<tt*1000000<<"\t1\t"<<rng.GetInteger(1, 10)<<endl;
	  tt = rng.GetValue(0, 1);
	  latencyf<<"0.0704256\tleaf-1\t1\t725\tFullDelay\t"<<tt<<"\t"<<tt*1000000<<"\t"<<rng.GetInteger(1,3)<<"\t"<<rng.GetInteger(1,10)<<endl;
  }

  return 0;
}
