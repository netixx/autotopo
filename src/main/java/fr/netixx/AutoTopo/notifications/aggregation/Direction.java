package fr.netixx.AutoTopo.notifications.aggregation;

import fr.netixx.AutoTopo.adapters.IDirection;

public class Direction implements IDirection {

	double cosTheta;
	double sinTheta;

	public Direction(double cosTheta, double sinTheta) {
		this.cosTheta = cosTheta;
		this.sinTheta = sinTheta;
	}

	@Override
	public double cosTheta() {
		return cosTheta;
	}

	@Override
	public double sinTheta() {
		return sinTheta;
	}

	@Override
	public double getLongitudeProjection(double value) {
		return value * cosTheta;
	}

	@Override
	public double getLatitudeProjection(double value) {
		return value * sinTheta;
	}


}
