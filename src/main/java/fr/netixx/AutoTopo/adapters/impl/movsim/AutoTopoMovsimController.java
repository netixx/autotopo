package fr.netixx.AutoTopo.adapters.impl.movsim;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.LinkedList;
import java.util.Map;

import fr.netixx.AutoTopo.statistics.TimeScope;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import fr.netixx.AutoTopo.Controller;
import fr.netixx.AutoTopo.adapters.IAgent;
import fr.netixx.AutoTopo.adapters.IController;
import fr.netixx.AutoTopo.adapters.IVehicleAdapter;
import fr.netixx.AutoTopo.adapters.io.IEntryPoint;
import fr.netixx.AutoTopo.agents.Agent;
import fr.netixx.AutoTopo.agents.IElement;
import fr.netixx.AutoTopo.agents.IScope;
import fr.netixx.AutoTopo.agents.RoadCoordinator;
import fr.netixx.AutoTopo.agents.RoadSegmentCoordinator;
import fr.netixx.AutoTopo.agents.factories.ElementFactory;
import fr.netixx.AutoTopo.notifications.aggregation.Aggregation;
import fr.netixx.AutoTopo.notifications.goals.AccelerationGoal;
import fr.netixx.AutoTopo.notifications.goals.LaneChangeGoal;
import fr.netixx.AutoTopo.statistics.MergedInstantConnections;
import fr.netixx.AutoTopo.statistics.RecordFilter;
import fr.netixx.AutoTopo.statistics.TimeInstantConnections;

public class AutoTopoMovsimController implements IController {

	private IElement root;
	private IEntryPoint<Agent> entryPoint;
	private Hashtable<IVehicleAdapter, Agent> linktable = new Hashtable<>();

	private LinkedList<RoadSegmentCoordinator> roadSegments;

	private Clock movsimClock = new Clock();

	public AutoTopoMovsimController(String[] opts) {
		Controller.initialize(opts);
		RoadCoordinator rootRoad = Controller.readCoordinators(movsimClock);
		entryPoint = Controller.readSegments(rootRoad, movsimClock);
		root = rootRoad;
		roadSegments = new LinkedList<>(((RoadCoordinator) root).getConnectionManager().getConnectedChildren());
	}


	public IAgent addVehicle(IVehicleAdapter vh) {
		Agent e = ElementFactory.newAgent(entryPoint, vh, movsimClock);
		entryPoint.insertElement(e);
		linktable.put(vh, e);
		return e;
	}

	public void removeVehicle(IVehicleAdapter vh) {
		Agent a = linktable.get(vh);
		if (a != null) {
			a.quit();
			linktable.remove(vh);
		}

	}

	public void aggregate() {
		Logger logger = LogManager.getLogger();
		logger.info("Collected data :\n{}", root.aggregate());
	}

	Logger logger = LogManager.getLogger();

	public void timeStep(double simulationTime) {
		monitorStatistics();
		movsimClock.setClock(simulationTime);
		// TODO : call checkManageTopo on each element individually ?
		root.checkManageTopology();
	}

	public boolean checkTopo() {
		boolean ret = true;
		// check for aggregation size wrt linktable size
		Aggregation agg = root.aggregate();
		if (linktable.size() != agg.getAggregationSize()) {
			ret = false;
			logger.info("Aggregation size is {}, linktable size is {}", linktable.size(), agg.getAggregationSize());
		}
		// check for missing vehicles
		for (Agent a : linktable.values()) {
			if (a.isActive() && !isAttached(a)) {
				logger.info("Agent {} is not attached to topology", a.getId());
				ret = false;
			}
		}
		// check for leaderless scopes
		// first pass, make scope table
		Map<IScope, LinkedList<Agent>> scopeTable = new HashMap<>();
		for (Agent a : linktable.values()) {
			IScope s = a.getScope();

			if (scopeTable.containsKey(s)) {
				scopeTable.get(s).add(a);
			} else {
				scopeTable.put(s, new LinkedList<>(Arrays.asList(a)));
			}
		}
		// check table for unicity of leader per scope
		for (Map.Entry<IScope, LinkedList<Agent>> scope : scopeTable.entrySet()) {
			int leaderCount = 0;
			for (Agent a : scope.getValue()) {
				if (a.isLeader()) {
					leaderCount++;
				}
			}
			if (leaderCount < 1) {
				logger.info("Scope {} has no leader", scope.getKey().getId());
				ret = false;
			}
			if (leaderCount > 1) {
				logger.info("Scope {} has {} leaders", scope.getKey().getId(), leaderCount);
				ret = false;
			}

		}

		return ret;
	}

	private boolean isAttached(Agent a) {
		IElement parent = a.getParent();

		while (parent != root && parent != null) {
			parent = parent.getParent();
		}

		return parent == root;
	}

	static RecordFilter<Agent> agentFilter = new RecordFilter<Agent>() {

		@Override
		public boolean filter(Agent el) {
			return !el.isLeader();
		}

	};

	static RecordFilter<RoadSegmentCoordinator> roadSegmentFilter = new RecordFilter<RoadSegmentCoordinator>() {

		@Override
		public boolean filter(RoadSegmentCoordinator el) {
			return !Controller.shouldLogRoadSegment(el.getId());
		}
	};

	private MergedInstantConnections<Agent> agentInstConnections = new MergedInstantConnections<>("agentsInstantConnections", agentFilter);
	private MergedInstantConnections<RoadSegmentCoordinator> coordInstConnections = new MergedInstantConnections<>("roadSegmentInstantConnections",
			roadSegmentFilter);

	private TimeInstantConnections<Agent> timeAgentInstConnections = new TimeInstantConnections<>("timeAgentsInstantConnections", agentFilter);
	private TimeInstantConnections<RoadSegmentCoordinator> timeSegmentInstConnections = new TimeInstantConnections<>("timeSegmentInstantConnections",
			roadSegmentFilter);

	private TimeScope timeScope = new TimeScope("timeScope");

	public void monitorStatistics() {
		double time = movsimClock.getTime();
		for (Agent a : linktable.values()) {
			timeScope.record(time, a.getScope());
			if (a.isLeader()) {
				agentInstConnections.record(a, a.getChildrenSize());
				timeAgentInstConnections.record(time, a, a.getChildrenSize());
			}
		}
		for (RoadSegmentCoordinator r : roadSegments) {
			coordInstConnections.record(r, r.getChildrenSize());
			timeSegmentInstConnections.record(time, r, r.getChildrenSize());
		}
	}

	public LaneChangeGoal getLaneChangeGoal(IVehicleAdapter me) {
		Agent agent = linktable.get(me);
		if (agent == null) {
			return LaneChangeGoal.FREE;
		}
		return agent.getGoalLaneChange();
	}

	public AccelerationGoal getAccelerationGoal(IVehicleAdapter me) {
		Agent agent = linktable.get(me);
		if (agent == null) {
			return AccelerationGoal.FREE;
		}
		return agent.getGoalAcceleration();
	}

	// public SpeedGoal getSpeedGoal(IVehicleAdapter me) {
	// Agent agent = linktable.get(me);
	// if (agent == null) {
	// return null;
	// }
	// return agent.getGoalSpeed();
	// }

	public void writeStats(String path) {
		Controller.writeDefaultCsvs(path);
		Controller.writeCsv(path, agentInstConnections);
		Controller.writeCsv(path, coordInstConnections);

		Controller.writeCsv(path, timeAgentInstConnections);
		Controller.writeCsv(path, timeSegmentInstConnections);
		Controller.writeCsv(path, timeScope);
	}
	// public static void initialize(IRoadAdapter road) {
	// int segmentNumber = 1;
	// LinkedList<IVehicleAdapter> vehicles = new LinkedList<>();
	//
	// RoadCoordinator rootRoad = ElementFactory.newRoadCoordinator();
	// for (int i = 0; i < segmentNumber; i++) {
	// RoadSegmentCoordinator rdsc =
	// ElementFactory.newRoadSegmentCoordinator(rootRoad);
	// for (IVehicleAdapter ivh : vehicles) {
	// ElementFactory.newAgent(rdsc, ivh);
	// }
	// }
	//
	// }

}
