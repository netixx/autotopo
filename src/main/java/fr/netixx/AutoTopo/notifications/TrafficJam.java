package fr.netixx.AutoTopo.notifications;

import java.util.Comparator;

import fr.netixx.AutoTopo.notifications.goals.SpeedGoal;

public class TrafficJam implements IPushNotification, IPullNotification {

	public final double start;
	public final double end;
	public final int size;
	public SpeedGoal recommendedSpeed;

	public TrafficJam(double start, double end, int size, SpeedGoal recommendedSpeed) {
		this.start = start;
		this.end = end;
		this.size = size;
		this.recommendedSpeed = recommendedSpeed;
	}


	public static Comparator<TrafficJam> createComparator() {
		return new Comparator<TrafficJam>() {

			@Override
			public int compare(TrafficJam o1, TrafficJam o2) {
				if (o1 == null || o2 == null)
					throw new NullPointerException();

				return Double.compare(o1.start, o2.start);
			}

		};
	}

	@Override
	public String toString() {
		return String.format("n:%s from %.0f to %.0f", size, start, end);
	}

}
