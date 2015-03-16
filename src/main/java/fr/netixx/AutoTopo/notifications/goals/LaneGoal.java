package fr.netixx.AutoTopo.notifications.goals;

import fr.netixx.AutoTopo.notifications.IPushNotification;

public class LaneGoal implements IPushNotification {

	public final int maxLane;
	public final int minLane;

	public LaneGoal(int maxLane, int minLane) {
		this.maxLane = maxLane;
		this.minLane = minLane;
	}

	public static LaneChangeGoal toLaneChange(int currentLane, LaneGoal goalLane) {
		if (currentLane <= goalLane.maxLane && currentLane >= goalLane.minLane) {
			return LaneChangeGoal.STAY;
		} else if (currentLane > goalLane.maxLane) {
			return LaneChangeGoal.RIGHT;
		} else if (currentLane < goalLane.minLane) {
			return LaneChangeGoal.LEFT;
		} else {
			return LaneChangeGoal.FREE;
		}
	}
}
