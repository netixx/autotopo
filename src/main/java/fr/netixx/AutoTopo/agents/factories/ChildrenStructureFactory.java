package fr.netixx.AutoTopo.agents.factories;

import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.Map;

import fr.netixx.AutoTopo.agents.Agent;
import fr.netixx.AutoTopo.agents.RoadSegmentCoordinator;

public class ChildrenStructureFactory {

	public static Collection<Agent> newChildrenLeader() {
		return new LinkedList<>();
	}

	public static Collection<Agent> newChildrenRoadSegmentCoordinator() {
		return new LinkedList<>();
	}

	public static Map<Integer, RoadSegmentCoordinator> newChildrenRoadCoordinator() {
		return new HashMap<>();
	}
}
