package fr.netixx.AutoTopo.notifications.conditions;

import fr.netixx.AutoTopo.agents.IElement;



/**
 * A condition to stop propagating a notification
 * 
 * @author francois
 *
 */
public interface IStopCondition {

	public boolean stop(IElement input);
}
