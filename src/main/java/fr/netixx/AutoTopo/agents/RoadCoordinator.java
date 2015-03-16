package fr.netixx.AutoTopo.agents;

import java.util.Map;

import fr.netixx.AutoTopo.adapters.IClock;
import fr.netixx.AutoTopo.agents.factories.ChildrenStructureFactory;
import fr.netixx.AutoTopo.notifications.IPullNotification;
import fr.netixx.AutoTopo.notifications.IPushNotification;


public class RoadCoordinator extends AbstractElement<RoadSegmentCoordinator> implements IElement {

	private Map<Integer, RoadSegmentCoordinator> childrenMap = ChildrenStructureFactory.newChildrenRoadCoordinator();

	public RoadCoordinator(IClock clock) {
		super(ETopoElement.RoadCoordinator, null, clock);
		// this.childrenMap = new HashMap<>();
		this.id = 1;
		this.connectionManager = new IdMappedConnectionManager<RoadSegmentCoordinator>(this.childrenMap, getEventsCounter());
	}

	@Override
	public void manageTopology() {

	}

	@Override
	public void optimizeTopology() {

	}



	// @Override
	// public void public void removeChild(RoadSegmentCoordinator child) {
	// this.childrenMap.
	// };

	@Override
	protected void treatNotification(IPullNotification notification) {
		// TODO Auto-generated method stub

	}

	@Override
	protected void treatNotification(IPushNotification notification) {
		// TODO Auto-generated method stub

	}

	protected RoadSegmentCoordinator getNextSegmentCoordinator(int id) {
		return this.childrenMap.get(id);
	}

}
