package fr.netixx.AutoTopo.notifications.goals;

import fr.netixx.AutoTopo.helpers.Units;
import fr.netixx.AutoTopo.notifications.IPushNotification;

public class SpeedGoal implements IPushNotification {

	private final double targetSpeed;

	public SpeedGoal(double targetSpeed) {
		this.targetSpeed = targetSpeed;
	}

	public double getSpeed() {
		return targetSpeed;
	}

	public static AccelerationGoal speedToAcc(double currentSpeed, SpeedGoal goalSpeed) {
		if (currentSpeed > goalSpeed.getSpeed()) {
			return AccelerationGoal.SLOWER;
		} else if (currentSpeed < goalSpeed.getSpeed()) {
			return AccelerationGoal.FASTER;
		}
		return AccelerationGoal.FREE;
	}

	@Override
	public String toString() {
		return String.format("%.4f km/h", targetSpeed * Units.MS_TO_KMH);
	}
}
