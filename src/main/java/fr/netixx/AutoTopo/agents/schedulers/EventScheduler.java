package fr.netixx.AutoTopo.agents.schedulers;

import fr.netixx.AutoTopo.agents.IEventsCounter;


public class EventScheduler implements IScheduler {

	private IEventsCounter counter;
	private int lastCounter;
	private final int nEventsTrigger;

	public EventScheduler(int nEventsTrigger, IEventsCounter counter) {
		this.nEventsTrigger = nEventsTrigger;
		this.counter = counter;
		lastCounter = counter.getEvents();

	}

	@Override
	public boolean shouldRun() {
		if ((counter.getEvents() - lastCounter >= nEventsTrigger)) {
			return true;
		}
		return false;
	}

	@Override
	public void reset() {
		lastCounter = counter.getEvents();
	}

}
