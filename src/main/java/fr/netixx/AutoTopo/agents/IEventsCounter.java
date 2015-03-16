package fr.netixx.AutoTopo.agents;

public interface IEventsCounter {
	public int getEvents();

	public void increment();

	public void increment(int k);
}
