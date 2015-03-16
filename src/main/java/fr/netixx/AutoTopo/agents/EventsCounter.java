package fr.netixx.AutoTopo.agents;

public class EventsCounter implements IEventsCounter {

	private int counter;

	public EventsCounter() {
		counter = 0;
	}

	@Override
	public int getEvents() {
		return counter;
	}

	@Override
	public void increment() {
		counter++;

	}

	@Override
	public void increment(int k) {
		counter += k;

	}

}
