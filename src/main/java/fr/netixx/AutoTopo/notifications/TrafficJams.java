package fr.netixx.AutoTopo.notifications;

import java.util.Set;

public class TrafficJams implements IPushNotification {

	private Set<TrafficJam> jams;

	public TrafficJams(Set<TrafficJam> jams) {
		this.jams = jams;
	}

	public Set<TrafficJam> getJams() {
		return jams;
	}

}
