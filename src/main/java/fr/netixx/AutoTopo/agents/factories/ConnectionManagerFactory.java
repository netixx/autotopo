package fr.netixx.AutoTopo.agents.factories;

import java.util.Collection;

import fr.netixx.AutoTopo.agents.Agent;
import fr.netixx.AutoTopo.agents.ConnectionManager;
import fr.netixx.AutoTopo.agents.IEventsCounter;
import fr.netixx.AutoTopo.agents.RoadSegmentCoordinator;
import fr.netixx.AutoTopo.statistics.TotalConnections;

public class ConnectionManagerFactory {

	public static TotalConnections agentConnections = new TotalConnections("agentConnections");
	public static TotalConnections roadSegmentConnections = new TotalConnections("roadSegmentConnections");

	public static ConnectionManager<Agent> newAgentConnectionManager(Agent a, Collection<Agent> children, IEventsCounter eventsCounter) {
		ConnectionManager<Agent> conn = new ConnectionManager<Agent>(children, eventsCounter);
		agentConnections.record(a, eventsCounter);
		return conn;
	}

	public static ConnectionManager<Agent> newRoadSegmentConnectionManager(RoadSegmentCoordinator el, Collection<Agent> children,
			IEventsCounter eventsCounter) {

		ConnectionManager<Agent> conn = new ConnectionManager<Agent>(children, eventsCounter);

		roadSegmentConnections.record(el, eventsCounter);
		return conn;
	}
}
