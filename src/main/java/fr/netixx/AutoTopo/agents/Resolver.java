package fr.netixx.AutoTopo.agents;

import java.util.HashMap;
import java.util.Map;

public class Resolver {
	private static Map<IElement, ConnectionManager<?>> resolver = new HashMap<>();

	public static ConnectionManager<?> get(IElement search) {
		return resolver.get(search);
	}

	@SuppressWarnings("unchecked")
	public static ConnectionManager<Agent> getAgent(IElement search) {
		ConnectionManager<?> res = resolver.get(search);
		return (ConnectionManager<Agent>) res;
	}

	@SuppressWarnings("unchecked")
	public static ConnectionManager<Agent> getRoadSegmentCoordinator(IElement search) {
		ConnectionManager<?> res = resolver.get(search);
		return (ConnectionManager<Agent>) res;
	}

	@SuppressWarnings("unchecked")
	public static ConnectionManager<RoadSegmentCoordinator> getRoadCoordinator(IElement search) {
		ConnectionManager<?> res = resolver.get(search);
		return (ConnectionManager<RoadSegmentCoordinator>) res;
	}

	public static void put(IElement element, ConnectionManager<?> manager) {
		resolver.put(element, manager);
	}
}
