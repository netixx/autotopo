package fr.netixx.AutoTopo.agents;


import fr.netixx.AutoTopo.notifications.IPullNotification;
import fr.netixx.AutoTopo.notifications.IPushNotification;
import fr.netixx.AutoTopo.notifications.aggregation.Aggregation;
import fr.netixx.AutoTopo.notifications.conditions.IStopCondition;

public interface IElement {

	public void broadCast(IPushNotification o, IStopCondition stopCondition);

	public void collect(IPullNotification o, IStopCondition stopCondition);

	public ETopoElement getLevel();

	public Aggregation aggregate();

	public boolean hasChildren();

	public int getChildrenSize();

	public void manageTopology();

	public void applyConstraints();

	public void optimizeTopology();

	public void checkManageTopology();

	public IElement getParent();

	public int getId();
}
