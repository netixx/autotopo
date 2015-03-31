package fr.netixx.AutoTopo.agents;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.Set;
import java.util.SortedMap;
import java.util.TreeMap;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import fr.netixx.AutoTopo.Settings;
import fr.netixx.AutoTopo.adapters.IAgent;
import fr.netixx.AutoTopo.adapters.IClock;
import fr.netixx.AutoTopo.adapters.IVehicleAdapter;
import fr.netixx.AutoTopo.adapters.io.IExitPoint;
import fr.netixx.AutoTopo.agents.factories.ChildrenStructureFactory;
import fr.netixx.AutoTopo.agents.factories.ConnectionManagerFactory;
import fr.netixx.AutoTopo.agents.schedulers.TimeScheduler;
import fr.netixx.AutoTopo.helpers.ClockCachedObject;
import fr.netixx.AutoTopo.notifications.IPullNotification;
import fr.netixx.AutoTopo.notifications.IPushNotification;
import fr.netixx.AutoTopo.notifications.TrafficJam;
import fr.netixx.AutoTopo.notifications.TrafficJams;
import fr.netixx.AutoTopo.notifications.aggregation.Aggregation;
import fr.netixx.AutoTopo.notifications.aggregation.AggregationHelper;
import fr.netixx.AutoTopo.notifications.goals.AccelerationGoal;
import fr.netixx.AutoTopo.notifications.goals.LaneChangeGoal;
import fr.netixx.AutoTopo.notifications.goals.SpeedGoal;


public class Agent extends AbstractElement<Agent> implements IElement, IExitPoint<Agent>, IAgent {

	private static final int MAX_LINK_DISTANCE = Settings.getInt(Settings.MAX_VEHICLE_CONNECTIONS_DISTANCE);
	private static final int MAX_LINK_DISTANCE_THRESHOLD = MAX_LINK_DISTANCE + Settings.getInt(Settings.MAX_VEHICLE_CONNECTIONS_DISTANCE_THRESHOLD);
	private static final int MAX_SCOPE_NUMBER = Settings.getInt(Settings.MAX_SCOPE_NUMBER);
	private static final int MAX_SCOPE_NUMBER_THRESHOLD = MAX_SCOPE_NUMBER + Settings.getInt(Settings.MAX_SCOPE_NUMBER_THRESHOLD);
	private static final boolean RECENTER_LEADER = Settings.getBoolean(Settings.OPTIMIZE_AGENT_RECENTER_LEADER_ENABLED);
	private static final double RECENTER_LEADER_BIAS = Settings.getDouble(Settings.OPTIMIZE_AGENT_RECENTER_LEADER_BIAS);
	private static final double RECENTER_LEADER_PERIOD = Settings.getDouble(Settings.OPTIMIZE_AGENT_RECENTER_LEADER_PERIOD);

	private static final double TRAFFICJAM_DISTANCE_WARN = Settings.getDouble(Settings.AGENT_TRAFFICJAM_SPEED_DISTANCE);

	private static final double DEFAULT_SPEED_LIMIT = Settings.getDouble(Settings.SPEED_LIMIT_DEFAULT);

	private static final boolean SPEED_CLUSTERING_ENABLED = Settings.getBoolean(Settings.OPTIMIZE_ROADSEGMENT_SPEED_CLUSTERING_ENABLED);
	private static final double SPEED_CLUSTERING_FACTOR = Settings.getDouble(Settings.OPTIMIZE_ROADSEGMENT_SPEED_CLUSTERING_FACTOR);

	private static Logger logger = LogManager.getLogger();

	private IScope scope = null;
	private final IVehicleAdapter vh;
	private ClockCachedObject<Aggregation> selfAggregate;
	private TimeScheduler recenterScheduler;


	private static int nextId = 0;

	/**
	 * TODO:..!
	 *
	 * // cout trop élevé => détachement // comparaison/renormalisation du cout
	 * par rapport à ceux du tronçon // listes contraintes (distance, nombre),
	 * buts ? => contraintes : en dur
	 *
	 * // + contrainte de nombre maximal // cout affine d'être leader ?
	 * (mutualisation des ressources) // contraintes vs goal ??
	 *
	 * // distance coordinateur variable ? vs nombre de connexions max // score
	 * += distance au centre de gravité du scope
	 *
	 * // karma ?
	 *
	 * // comparaison paralelle, essayer d'autres modèles d'acceleration
	 *
	 * // scenario routage (load balancing) // scenario insertion (alignement
	 * vitesse) // stat: acceleration cummulée (+ mean travel time)
	 *
	 * - see in related work papers
	 * the manner in which they collect data from cars and compare
	 *
	 *
	 *
	 * // metrique framework vs paramètres (taille scope)
	 *
	 *
	 * "loi" vitesse bouchon wrt densité
	 * distance application vitesse
	 *
	 *
	 * bottleneck : distribution vitesse + ration km/h/l
	 *
	 * routing : travel time + ?
	 *
	 * on ramp ?
	 *
	 *
	 *
	 * clustering vitesse
	 * Recuperer taille scope au niveau des coordinateurs
	 * Scenario centrage leader
	 *
	 *
	 * Optimisation conditionnelle : appliquer les politiques en fonction de la
	 * situation
	 *
	 * agg nconnection only for leaders
	 *
	 *
	 * cas recentrage : injection burst 2*distance connection
	 *
	 */
	public Agent(final RoadSegmentCoordinator parent, final IVehicleAdapter vehicle, IClock clock) {
		super(ETopoElement.Leader, parent, clock);
		vh = vehicle;
		this.id = ++nextId;
		setScope(new Scope());
		setLeader(true);
		// TODO : change
		this.connectionManager = ConnectionManagerFactory.newAgentConnectionManager(this, ChildrenStructureFactory.newChildrenLeader(),
				getEventsCounter());
		selfAggregate = new ClockCachedObject<Aggregation>(clock) {

			@Override
			public Aggregation renew() {
				return rawAggregate(false);
			}

		};

		recenterScheduler = new TimeScheduler(RECENTER_LEADER_PERIOD, clock);

	}

	@Override
	public Aggregation aggregate() {
		return rawAggregate(isLeader());
	}

	private Aggregation rawAggregate(boolean isLeader) {
		Aggregation res = new Aggregation(vh.getSpeed(), vh.getAcceleration(), vh.getDirection(), vh.getSize(), vh.getLat(),
				vh.getLong(), vh.getLat()
				* vh.getSize(), vh.getLong()
				* vh.getSize(), vh.getCurvAbsc(), 1, clock.getTime());
		if (isLeader) {
			LinkedList<Aggregation> aggs = new LinkedList<>();
			aggs.add(res);
			for (Agent child : getConnectionManager().getConnectedChildren()) {
				aggs.add(child.aggregate());
			}
			res = Aggregation.aggregate(aggs);
		}
		return res;
	}

	public IVehicleAdapter getVehicle() {
		return vh;
	}



	/**
	 * Make subordinate a leader, attaching it to given parent
	 *
	 * @param parent
	 */
	protected void toLeader(IElement parent) {
		if (this.isLeader()) {
			logger.error("Agent {} is already leader.", this.getId());
			return;
		}
		this.move(parent);
		// this.parent.moveChild(this, parent);
		setScope(new Scope());
		setLeader(true);
		// this.children = ChildrenStructureFactory.newChildrenLeader();
		logger.debug("Agent {} moved to leader, new scope : {}", this.id, this.scope.getId());
	}

	protected void changeLeader(Agent newLeader) {
		if (this.isLeader()) {
			logger.error("Cannot change Leader of current leader {}", this.getId());
			return;
		}
		this.move(newLeader);
		// this.parent.moveChild(this, newLeader);
		setScope(newLeader.scope);
		logger.debug("Changed leader of {} to {}, scope {}", this.getId(), newLeader.getId(), newLeader.getScope().getId());
	}

	/**
	 * Make a leader subordinate of another leader
	 *
	 * @param newLeader
	 */
	public void toSubordinate(final Agent newLeader) {
		// TODO : move to coordinator ?
		if (!newLeader.isLeader()) {
			logger.error("Cannot move agent {} to non-leader {}", this.getId(), newLeader.getId());
			return;
		}
		if (!this.isLeader()) {
			logger.error("Cannot move non-leader {} to subordinate of {}", this.getId(), newLeader.getId());
			return;
		}
		if (this == newLeader) {
			logger.error("Tried to move leader {} to subordinate of itself", this.getId());
			return;
		}
		this.move(newLeader);
		// this.parent.moveChild(this, newLeader);
		setScope(newLeader.scope);
		setLeader(false);
		logger.debug("Agent {} moved to subordinate of {}, scope : {}", this.id, newLeader.getId(), this.scope.getId());
	}

	/**
	 * Move yourself to someone else
	 *
	 * @param to
	 */
	public void move(IElement to) {
		Resolver.getAgent(parent).disconnect(this);
		Resolver.getAgent(to).connect(this);
		parent = to;
	}

	public void changeCoordinator(RoadSegmentCoordinator newParent) {
		// TODO : move to coordinator ??
		if (!this.isLeader()) {
			logger.error("Cannot change coordinator of non-leader {}", this.getId());
			return;
		}
		this.move(newParent);
		// this.parent.moveChild(this, newParent);
		logger.debug("Leader {}, scope {}, moved to coordinator {}", this.getId(), this.getScope().getId(), newParent);
	}

	public void quit() {
		// just leave
		if (!isLeader() || !hasChildren()) {
			((IExitPoint<Agent>) this.parent).removeChild(this);
			logger.debug("Agent {}, simple leave", this.getId());
			return;
		}
		// elect new leader among children
		// TODO : elect
		Agent newLeader = null;

		for (Agent a : new ArrayList<>(getConnectionManager().getConnectedChildren())) {
			if (newLeader == null) {
				newLeader = a;
				newLeader.toLeader(this.parent);
			} else {
				a.changeLeader(newLeader);
				// a.parent.moveChild(a, newLeader);
			}
		}
		// then leave
		((IExitPoint<Agent>) this.parent).removeChild(this);
		logger.debug("Agent {} (leader) left, new leader for scope is {}", this.getId(), newLeader.getId());

	}

	public boolean isLeader() {
		return level == ETopoElement.Leader;
	}

	private void setLeader(boolean isLeader) {
		if (isLeader) {
			level = ETopoElement.Leader;
		} else {
			level = ETopoElement.Agent;
		}
		this.vh.setIsLeader(isLeader);
	}

	public IScope getScope() {
		return scope;
	}

	public void setScope(IScope scope) {
		this.scope = scope;
		this.vh.setScopeId(this.scope.getId());
	}

	@Override
	public void manageTopology() {
		if (!isLeader()) {
			return;
		}
		optimizeTopology();
		this.aggregate.reset();
		// remove children that (would) be to far
		applyConstraints();
		this.aggregate.reset();
		// // sort by reverse distance, first element is the furthest one
		// SortedMap<Aggregation, Agent> leavingAgents = new
		// TreeMap<>(AggregationHelper.createReverseAggregationComparator());
		//
		// Aggregation leaderAgg = this.getAggregate();
		// for (Agent a : children) {
		// // detach children who are to far
		// Aggregation dist = a.getAggregate().distance(leaderAgg);
		// if (AggregationHelper.eulerDistance(dist) >= MAX_LINK_DISTANCE) {
		// leavingAgents.put(dist, a);
		// }
		// }
		// for (Agent a : leavingAgents.values()) {
		// a.toLeader(this.parent);
		//

		// optimizeTopology();
		manageTraffic();
	}

	private static final SpeedGoal defaultSpeed = new SpeedGoal(DEFAULT_SPEED_LIMIT);

	private void manageTraffic() {
		double dist = AggregationHelper.curvDistance(this.selfAggregate());
		if (jams != null) {
			for (TrafficJam jam : jams.getJams()) {
				if (dist >= jam.start - TRAFFICJAM_DISTANCE_WARN && dist <= jam.end) {
					this.targetSpeed = jam.recommendedSpeed;
					return;
				}
			}
		}
		this.targetSpeed = defaultSpeed;

	}

	@Override
	public void applyConstraints() {
		/* Constraints for Leaders :
		 * - maintain distance to members lower than MAX_LINK_DISTANCE
		 * - maintain number of members to less that MAX_LINK_NUMBER
		 * TODO: - if local destination is different, split
		 */
		int grpSize = 1;
		int grp = (this.getId() / grpSize) % 4;
		if (grp == 0) {
			this.vh.changeRoute("exit_right");
		} else if (grp == 1) {
			this.vh.changeRoute("main_right");
		} else {
			this.vh.changeRoute("main");
		}

		if (isLeader()) {

			// don't reattach to this!
			Collection<Agent> tooFar = this.getTooFarChildren();
			for (Agent a : tooFar) {
				// TODO : findAndAttach : leader ou a ?
				findAndAttach(a);
			}
			if (this.getChildrenSize() > MAX_SCOPE_NUMBER_THRESHOLD) {
				Collection<Agent> toRemove = this.getFurthestFromPack(MAX_SCOPE_NUMBER - this.getChildrenSize());
				for (Agent a : toRemove) {
					// TODO : findAndAttach : leader ou a ?
					findAndAttach(a);
				}
			}
		}
	}

	@Override
	public void optimizeTopology() {
		// here move leader closer to center of gravity if possible
		if (RECENTER_LEADER && recenterScheduler.shouldRun() && isLeader() && hasChildren()) {
			Aggregation mean = getAggregate();
			SortedMap<Aggregation, Agent> candidates = new TreeMap<>(AggregationHelper.createDistanceAndSpeedAggregationComparator());
			for (Agent a : getConnectionManager().getConnectedChildren()) {
				candidates.put(a.getAggregate().difference(mean), a);
			}
			double cdDist = AggregationHelper.eulerDistance(candidates.firstKey());
			double curDist = AggregationHelper.eulerDistance(mean.absDistance(selfAggregate()));
			// new leader is closer (by a factor) to center of gravity
			if ((1 + RECENTER_LEADER_BIAS) * cdDist - curDist < 0) {
				Agent newLeader = candidates.get(candidates.firstKey());
				this.swapLeader(newLeader);
			}
			recenterScheduler.reset();
		}

	}

	/**
	 * Swap leader inside scope, initiated by current scope leader :
	 * -attach new leader to current leader's parent
	 * -attach children to the new leader
	 * -detach yourself from parent
	 * -attach to new leader
	 *
	 * @param newLeader
	 */
	private void swapLeader(Agent newLeader) {
		if (!isLeader()) {
			logger.error("Cannot swap leader if non-leader");
			return;
		}

		newLeader.move(parent);
		newLeader.setScope(this.getScope());
		// this.parent.moveChild(this, parent);
		// setScope(new Scope());
		newLeader.setLeader(true);
		for (Agent a : new LinkedList<>(getConnectionManager().getConnectedChildren())) {
			// move other to newLeader
			// if (!a.isLeader()) {//should never happen...
			a.changeLeader(newLeader);
			// }
		}

		this.toSubordinate(newLeader);
	}

	private void findAndAttach(Agent a) {
		// All agents here are subordinates
		Agent attachPoint = this.findBestAttachPoint(a, new HashSet<IElement>(Arrays.asList(this)));
		logger.debug("Agent {} is too far, re-attaching to {}", a, attachPoint);
		if (attachPoint == null) {
			a.toLeader(this.parent);
		} else {
			a.changeLeader(attachPoint);
		}
	}


	/**
	 * @deprecated
	 * @return
	 */
	@Deprecated
	public boolean isActive() {
		return (this.vh.getLat() >= 0 && this.vh.getLong() >= 0);
	}

	@Override
	protected void treatNotification(IPullNotification notification) {
		// TODO Auto-generated method stub

	}

	@Override
	protected void treatNotification(IPushNotification notification) {
		// if (notification instanceof ScopeSizeGoal) {
		// this.goalScopeSize = ((ScopeSizeGoal) notification).getGoal();
		// }
		if (notification instanceof SpeedGoal) {
			this.targetSpeed = (SpeedGoal) notification;
		}
		else if (notification instanceof TrafficJams) {
			this.jams = (TrafficJams) notification;
		}
	}

	private TrafficJams jams;

	public Collection<Agent> getFurthestFromPack(int n) {
		Aggregation pack = getAggregate();
		// put the furthest elements first
		TreeMap<Aggregation, Agent> order = new TreeMap<>(AggregationHelper.createReverseDistanceAggregationComparator());
		for (Agent a : getConnectionManager().getConnectedChildren()) {
			order.put(a.getAggregate().absDistance(pack), a);
		}
		// also add the leader himself, because he might also be very far from
		// the pack
		order.put(this.rawAggregate(false).absDistance(pack), this);

		// get the nth first candidates
		return new ArrayList<>(order.values()).subList(0, n);
	}

	public boolean maxSizeReached() {
		return this.getChildrenSize() >= MAX_SCOPE_NUMBER_THRESHOLD;
	}

	public boolean isInCommunicationRange(Agent a) {
		return AggregationHelper.eulerDistance(a.getAggregate().absDistance(this.selfAggregate())) < MAX_LINK_DISTANCE;
	}

	public Collection<Agent> getTooFarChildren() {
		// TODO : add agent with different direction
		Collection<Agent> ret = new LinkedList<>();
		for (Agent a : getConnectionManager().getConnectedChildren()) {
			if (AggregationHelper.eulerDistance(a.getAggregate().absDistance(this.selfAggregate())) > MAX_LINK_DISTANCE_THRESHOLD) {
				logger.debug("Too far : Agent {} ({}) from leader {} ({}): distance : {}", a.getId(), a.getAggregate().printLongLat(), this.getId(),
						this.selfAggregate().printLongLat(), AggregationHelper.eulerDistance(a.getAggregate().absDistance(this.selfAggregate())));
				ret.add(a);
			}
		}

		return ret;
	}

	@Override
	public void removeChild(Agent child) {
		if (!this.isLeader()) {
			logger.error("Current non-leader Agent cannot remove elements (is not an exit point)");
			return;
		}
		this.getConnectionManager().disconnect(child);

	}

	@Override
	public LaneChangeGoal getGoalLaneChange() {
		return LaneChangeGoal.FREE;
		// TODO: decide wrt goals
		// double d = AggregationHelper.longDistance(selfAggregate());
		// if (d < 1000 && d > 20) {
		// // give 200 of free roam
		// if (this.vh.getLane() > 1 && d - lastorder > 200) {
		// lastorder = d;
		// return LaneChangeGoal.RIGHT;
		// }
		// // return LaneChangeGoal.RIGHT;
		// }
		// return LaneChangeGoal.FREE;
	}

	private Aggregation selfAggregate() {
		return selfAggregate.get();
	}

	private SpeedGoal targetSpeed = null;
	public AccelerationGoal getGoalAcceleration() {
		if (targetSpeed != null) {
			return SpeedGoal.speedToAcc(this.vh.getSpeed(), targetSpeed);
		}
		return AccelerationGoal.FREE;
	}

	@Override
	public SpeedGoal getGoalSpeed() {
		return targetSpeed;
	}

	public String getRoute() {
		return this.vh.getRouteName();
	}

	public boolean tryMergeWith(Agent leader) {
		if (!this.isLeader()) {
			logger.error("Cannot merge if not leader");
			return false;
		}
		// check for indivudual range
		if (!this.isInCommunicationRange(leader)) {
			return false;
		}

		// check for range of children
		for (Agent a : getConnectionManager().getConnectedChildren()) {
			if (!a.isInCommunicationRange(leader)) {
				return false;
			}
		}
		logger.debug("Leader {} merging with {}", this.getId(), leader.getId());
		// if ok, move children
		for (Agent a : new LinkedList<>(getConnectionManager().getConnectedChildren())) {
			a.changeLeader(leader);
		}
		// then go to subordinate
		this.toSubordinate(leader);

		return true;

	}

	public Agent findBestAttachPoint(Agent agent) {
		return findBestAttachPoint(agent, new HashSet<IElement>());
	}

	public Agent findBestAttachPoint(Agent agent, Set<IElement> except) {
		return findBestAttachPoint(agent, ((RoadSegmentCoordinator) this.parent).getAvailableAgentsFor(agent), except);
	}

	public Agent findBestAttachPoint(Agent agent, Collection<Agent> haystack, Set<IElement> except) {
		SortedMap<Aggregation, Agent> candidates = new TreeMap<>(AggregationHelper.createDistanceAndSpeedAndAccelerationAggregationComparator());
		// find potential candidates
		for (Agent a : haystack) {
			if (isAvailable(a, agent) && isOnSameRoute(a, agent) && !a.equals(agent) && !except.contains(a) && isSpeedCloseEnough(a, agent)) {
				// candidates.add(a);
				candidates.put(a.getAggregate().difference(agent.getAggregate()), a);
			}
		}
		// if no candidate available, make it a Leader (attach to this
		// coordinator)
		if (candidates.isEmpty()) {
			logger.debug("No candidate available for reattachment of agent {}", agent.getId());
			return null;
		}
		for (Agent c : candidates.values()) {
			logger.debug("Candidates for {} : Agent {}, distance {}", agent.getId(), c.getId(),
					AggregationHelper.eulerDistance(c.getAggregate().absDistance(agent.getAggregate())));
		}
		return candidates.get(candidates.firstKey());

	}

	private boolean isSpeedCloseEnough(Agent host, Agent candidate) {
		if (!SPEED_CLUSTERING_ENABLED)
			return true;
		final double hs = host.getAggregate().getSpeed();
		final double cs = candidate.getAggregate().getSpeed();
		return Math.abs(hs - cs) < SPEED_CLUSTERING_FACTOR * (hs + cs) / 2;
	}

	private boolean isAvailable(Agent host, Agent candidate) {
		return !host.maxSizeReached() && host.isInCommunicationRange(candidate);
	}

	private boolean isOnSameRoute(Agent host, Agent candidate) {
		// TODO : do better if routes have common segments
		return (host.getRoute() == null && candidate.getRoute() == null)
				|| (host.getRoute() != null && host.getRoute().equals(candidate.getRoute()));
	}

	@Override
	public int getScopeId() {
		return this.getScope().getId();
	}
}
