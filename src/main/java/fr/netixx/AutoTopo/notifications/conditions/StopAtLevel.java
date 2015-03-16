package fr.netixx.AutoTopo.notifications.conditions;

import fr.netixx.AutoTopo.agents.ETopoElement;
import fr.netixx.AutoTopo.agents.IElement;


public class StopAtLevel implements IStopCondition {
	
	private final ETopoElement input;
	
	public StopAtLevel(final ETopoElement input) {
		this.input = input;
	}
	public boolean stop(final IElement input) {
		return (input != null && this.input == input.getLevel());
	}
	
	
}
