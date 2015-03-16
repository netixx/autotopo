package fr.netixx.AutoTopo.agents;

import java.util.Collection;

public class ConnectionManager<Child extends IElement> {
	protected Collection<Child> children;
	protected IEventsCounter connectionsCounter;

	public ConnectionManager(Collection<Child> children, IEventsCounter connectionsCounter) {
		this.children = children;
		this.connectionsCounter = connectionsCounter;
	}

	public Collection<Child> getConnectedChildren() {
		return children;
	}

	public void connect(Child child) {
		this.connectionsCounter.increment();
		children.add(child);
	}

	public void disconnect(Child child) {
		this.connectionsCounter.increment();
		children.remove(child);
	}
}
