package fr.netixx.AutoTopo.agents;

import java.util.Map;

public class IdMappedConnectionManager<Child extends IElement> extends ConnectionManager<Child> {

	private Map<Integer, Child> map;

	IdMappedConnectionManager(Map<Integer, Child> map, IEventsCounter connectionsCounter) {
		super(map.values(), connectionsCounter);
		this.map = map;

	}

	@Override
	public void connect(Child child) {
		this.connectionsCounter.increment();
		map.put(child.getId(), child);
	}

	@Override
	public void disconnect(Child child) {
		this.connectionsCounter.increment();
		map.remove(child);
	}
}
