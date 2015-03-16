package fr.netixx.AutoTopo.notifications.conditions;

import fr.netixx.AutoTopo.agents.IElement;



public class StopAfterN implements IStopCondition {
	
	private int N;
	
	public StopAfterN(final int n) {
		N = n;
	}
	public boolean stop(final IElement input) {
		return --N <= 0;
	}
	
	
}
