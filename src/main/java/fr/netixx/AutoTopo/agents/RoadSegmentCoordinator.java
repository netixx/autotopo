package fr.netixx.AutoTopo.agents;

import java.util.Collection;
import java.util.LinkedList;
import java.util.List;
import java.util.SortedMap;
import java.util.SortedSet;
import java.util.TreeMap;
import java.util.TreeSet;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import fr.netixx.AutoTopo.Settings;
import fr.netixx.AutoTopo.adapters.IClock;
import fr.netixx.AutoTopo.adapters.io.IEntryPoint;
import fr.netixx.AutoTopo.adapters.io.IExitPoint;
import fr.netixx.AutoTopo.agents.clustering.Clustering;
import fr.netixx.AutoTopo.agents.factories.ChildrenStructureFactory;
import fr.netixx.AutoTopo.agents.factories.ConnectionManagerFactory;
import fr.netixx.AutoTopo.helpers.ClockCachedObject;
import fr.netixx.AutoTopo.notifications.IPullNotification;
import fr.netixx.AutoTopo.notifications.IPushNotification;
import fr.netixx.AutoTopo.notifications.TrafficJam;
import fr.netixx.AutoTopo.notifications.TrafficJams;
import fr.netixx.AutoTopo.notifications.aggregation.Aggregation;
import fr.netixx.AutoTopo.notifications.aggregation.AggregationHelper;
import fr.netixx.AutoTopo.notifications.conditions.StopAtLevel;
import fr.netixx.AutoTopo.notifications.goals.SpeedGoal;



public class RoadSegmentCoordinator extends AbstractElement<Agent> implements IElement, IEntryPoint<Agent>, IExitPoint<Agent> {

	private static int MAX_CONNECTIONS = Settings.getInt(Settings.MAX_ROAD_SEGMENT_COORDINATOR_CONNECTIONS);

	private static final double TRAFFICJAM_INTERDISTANCE = Settings.getDouble(Settings.ROADSEGMENTS_TRAFFICJAM_INTERDISTANCE);
	private static final boolean TRAFFICJAM_ENABLED = Settings.getBoolean(Settings.ROADSEGMENTS_TRAFFICJAM_ENABLED);
	private static final double TRAFFICJAM_JAM_SPEED_FACTOR = Settings.getDouble(Settings.ROADSEGMENTS_TRAFFICJAM_JAMFACTOR);

	private static final double TRAFFICJAM_SPEED_FACTOR = Settings.getDouble(Settings.ROADSEGMENTS_TRAFFICJAM_SPEED_FACTOR);

	private static Logger logger = LogManager.getLogger();

	private final double endOfSegment;
	private final int nextCoordinatorId;

	ClockCachedObject<SortedSet<TrafficJam>> curJams;

	public RoadSegmentCoordinator(RoadCoordinator parent, int id, int nextId, double endOfSegment, IClock clock) {
		super(ETopoElement.RoadSegementCoordinator, parent, clock);
		this.id = id;
		this.nextCoordinatorId = nextId;
		this.endOfSegment = endOfSegment;
		this.connectionManager = ConnectionManagerFactory.newRoadSegmentConnectionManager(this,
				ChildrenStructureFactory.newChildrenRoadSegmentCoordinator(), getEventsCounter());

		curJams = new ClockCachedObject<SortedSet<TrafficJam>>(clock) {

			@Override
			public SortedSet<TrafficJam> renew() {
				return detectTrafficJams();
			}

		};
	}

	@Override
	public void manageTopology() {
		// aggregate();
		// not the last coordinator in road
		if (nextCoordinatorId != 0) {

			// Collection<Agent> toChange = new LinkedList<>();
			RoadSegmentCoordinator next = ((RoadCoordinator) getParent()).getNextSegmentCoordinator(nextCoordinatorId);
			for (Agent a : new LinkedList<>(getConnectionManager().getConnectedChildren())) {
				// handoff if agent has reached boundary of this coordinator
				if (AggregationHelper.curvDistance(a.getAggregate()) >= endOfSegment) {
					// toChange.add(a);
					a.changeCoordinator(next);
				}
			}
			// if (!toChange.isEmpty()) {
			// RoadSegmentCoordinator next = ((RoadCoordinator)
			// parent).getNextSegmentCoordinator(nextCoordinatorId);
			// for (Agent a : toChange) {
			// a.changeParent(next);
			// }
			// }
		}

		// avoid concurrent modification
		for (Agent a : new LinkedList<>(getConnectionManager().getConnectedChildren())) {
			a.manageTopology();
		}

		for (Agent a : new LinkedList<>(getConnectionManager().getConnectedChildren())) {
			a.aggregate.reset();
		}

		// checkInsertions();
		//update goals
		// if (toManyConnections()) {
		// broadCast(new ScopeSizeGoal(children.size() / MAX_CONNECTIONS), new
		// StopAtLevel(ETopoElement.Leader));
		// }

		optimizeTopology();
		for (Agent a : new LinkedList<>(getConnectionManager().getConnectedChildren())) {
			a.aggregate.reset();
		}
		// //old code
		// // else elect the (new) leaders (from all current leaders)
		// ArrayList<Agent> followers = getNewFollowers(children.size() -
		// MAX_CONNECTIONS);
		// ArrayList<Agent> leaders = new ArrayList<>();
		//
		// for (Agent c : children) {
		// if (!followers.contains((Agent) c)) {
		// leaders.add((Agent) c);
		// }
		// }
		//
		// for (Agent f : followers) {
		// Agent l = (Agent) getBestLeader(f, leaders);
		// l.attachChild(f);
		// }
		manageTrafic();

	}

	private static final double DEFAULT_SPEED_LIMIT = Settings.getDouble(Settings.SPEED_LIMIT_DEFAULT);
	private SpeedGoal jamSpeed = new SpeedGoal(DEFAULT_SPEED_LIMIT * TRAFFICJAM_SPEED_FACTOR);

	public void manageTrafic() {
		// IStopCondition stopAtLevel = new StopAtLevel(ETopoElement.Agent);
		// global reset (easier to code, doesn't make a difference) !
		// broadCast(defaultSpeed, stopAtLevel);
		if (TRAFFICJAM_ENABLED) {
			// TODO: request jams from next coordinator and treat them based on
			// distance to segment end
			RoadSegmentCoordinator next = ((RoadCoordinator) getParent()).getNextSegmentCoordinator(nextCoordinatorId);
			if (next != null)
				next.getTrafficJams();
			SortedSet<TrafficJam> jams = getTrafficJams();
			broadCast(new TrafficJams(jams), new StopAtLevel(ETopoElement.Agent));
			if (jams.size() > 0)
				logger.info("Got {} jams : {}, target speed is {}", jams.size(), jams, jamSpeed);
			//					// TODO : use size of jam
			//					// TODO : remember state to smooth speed changes
			//				}
			//			}
		}
	}

	private SortedSet<TrafficJam> getTrafficJams() {
		return curJams.get();
	}


	private SortedSet<TrafficJam> detectTrafficJams() {
		// TODO : look at absDistance etc...
		Aggregation avg = getAggregate();
		Collection<Aggregation> stopped = new LinkedList<>();
		for (Agent a : getConnectionManager().getConnectedChildren()) {
			Aggregation newStop = a.getAggregate();
			if (newStop.getSpeed() <= avg.getSpeed() * TRAFFICJAM_JAM_SPEED_FACTOR) {
				for (Aggregation agg : new LinkedList<>(stopped)) {
					//this aggregation is too close to one previous agg
					if (AggregationHelper.minRoadDistance(newStop, agg) <= TRAFFICJAM_INTERDISTANCE) {
						//merge
						newStop = Aggregation.aggregate(newStop, agg);
						stopped.remove(agg);
						break;
					}
				}
				stopped.add(newStop);
			}
		}
		// TODO : abscisse curviligne pour new TrafficJam
		SortedSet<TrafficJam> jams = new TreeSet<>(TrafficJam.createComparator());
		for (Aggregation stop : stopped) {
			double start = AggregationHelper.minCurvDistance(stop);
			double end = AggregationHelper.maxCurvDistance(stop);
			jams.add(new TrafficJam(start, end, stop.getAggregationSize(), jamSpeed));
		}
		return jams;
	}

	// private void selectiveBroadCast(IPushNotification notification,
	// IStopCondition stopCondition, double minLongitude, double maxLongitude) {
	// for (Agent a : getConnectionManager().getConnectedChildren()) {
	// double longitude = AggregationHelper.longDistance(a.getAggregate());
	// if (longitude >= minLongitude && longitude <= maxLongitude) {
	// a.broadCast(notification, stopCondition);
	// }
	// }
	// }
	public Collection<Agent> getAvailableAgentsFor(Agent a) {
		Collection<Agent> r = new LinkedList<>();
		for (Agent agent : this.getConnectionManager().getConnectedChildren()) {
			if (isAvailable(agent, a)) {
				r.add(a);
			}
		}
		return r;
	}

	private boolean isAvailable(Agent host, Agent candidate) {
		return !host.maxSizeReached() && host.isInCommunicationRange(candidate);
	}

	private Agent findBestLeader(List<Agent> leaders) {
		LinkedList<Aggregation> aggs = new LinkedList<>();

		for (Agent l : leaders) {
			aggs.add(l.getAggregate());
		}
		Aggregation mean = Aggregation.aggregate(aggs);
		SortedMap<Aggregation, Agent> map = new TreeMap<>(AggregationHelper.createDistanceAggregationComparator());
		for (Agent l : leaders) {
			map.put(l.getAggregate().absDistance(mean), l);
		}
		return map.get(map.firstKey());

	}
	@Override
	public void optimizeTopology() {
		List<List<Agent>> mergesTry = new Clustering().merge(this.getConnectionManager().getConnectedChildren());
		for (List<Agent> merges : mergesTry) {
			Agent leader = findBestLeader(merges);
			for (Agent a : merges) {
				if (!a.equals(leader)) {
					int ida = a.getId();
					boolean res = a.tryMergeWith(leader);
					logger.debug("Merge from scope {} and {} {}", ida, leader.getScope().getId(), res ? "succeeded" : "failed");
				}
			}

		}
	}

	// private Set<IElement> matchAgents(Collection<Agent> bachelor,
	// Collection<Agent> candidates) {
	// Set<IElement> except = new HashSet<>();
	// for (Agent a : bachelor) {
	// // make sure a has no children (otherwise chain of leader occurs)
	// if (a.hasChildren())
	// continue;
	// Agent newLeader = findBestAttachPoint(a, candidates, except);
	// if (newLeader != null) {
	// logger.debug("Found match for single leader {} : {}", a.getId(),
	// newLeader.getId());
	// a.toSubordinate(newLeader);
	// except.add(a);
	// }
	// }
	// return except;
	// }

	// private Set<IElement> matchSingleAgents(Collection<Agent> candidates) {
	// if (INTELLIGENT_SINGLE_MATCH_ENABLED) {
	// // first pass, provisional matches
	// Map<Agent, LinkedList<Agent>> provMatches = new HashMap<>();
	// Set<IElement> except = new HashSet<>();
	// for (Agent a : candidates) {
	// // make sure a has no children (otherwise chain of leader occurs)
	// if (provMatches.containsKey(a))
	// continue;
	// Agent newLeader = findBestAttachPoint(a, candidates, except);
	// if (newLeader != null) {
	// if (provMatches.containsKey(newLeader)) {
	// provMatches.get(newLeader).add(a);
	// } else {
	// LinkedList<Agent> l = new LinkedList<>();
	// l.add(a);
	// provMatches.put(newLeader, l);
	// }
	// except.add(a);
	// }
	// }
	// // find best leader for each group
	// for (Entry<Agent, LinkedList<Agent>> entry : provMatches.entrySet()) {
	// Map<Agent, Aggregation> aggs = new HashMap<>();
	// aggs.put(entry.getKey(), entry.getKey().getAggregate());
	// for (Agent a : entry.getValue()) {
	// aggs.put(a, a.getAggregate());
	// }
	// // compute would-be center of gravity
	// Aggregation mean = Aggregation.aggregate(aggs.values());
	// SortedMap<Aggregation, Agent> sorted = new
	// TreeMap<>(AggregationHelper.createDistanceAggregationComparator());
	// for (Entry<Agent, Aggregation> ent : aggs.entrySet()) {
	// sorted.put(ent.getValue().absDistance(mean), ent.getKey());
	// }
	//
	// Agent newLeader = sorted.get(sorted.firstKey());
	// for (Agent a : sorted.values()) {
	// if (!a.equals(newLeader)) {
	// a.toSubordinate(newLeader);
	// }
	// }
	// }
	// return except;
	// } else {
	// return matchAgents(candidates, candidates);
	// }
	// }


	// private ArrayList<Agent> getNewFollowers(int nFollowers) {
	// // TODO : elect and select!!
	//
	// ArrayList<Agent> res = new ArrayList<>();
	//
	// // criteria used to make followers is the number of children they have
	// int nChildren = 0;
	// while (res.size() < nFollowers) {
	// fillFollowers(res, nFollowers - res.size(), nChildren++);
	// }
	//
	// return res;
	// }
	//
	// private void fillFollowers(ArrayList<Agent> list, int nFill, int
	// nChildren) {
	// int count = 0;
	// for (Agent e : children) {
	// if (e.getChildrenSize() <= nChildren) {
	// list.add(e);
	// list.addAll(e.getChildren());
	// }
	//
	// if (++count >= nFill) {
	// return;
	// }
	// }
	// }


	@Override
	public void insertElement(Agent e) {
		this.getConnectionManager().connect(e);
	}

	@Override
	protected void treatNotification(IPullNotification notification) {
		// TODO Auto-generated method stub

	}

	@Override
	protected void treatNotification(IPushNotification notification) {
		// TODO Auto-generated method stub

	}

	@Override
	public void removeChild(Agent child) {
		this.getConnectionManager().disconnect(child);

	}

}
