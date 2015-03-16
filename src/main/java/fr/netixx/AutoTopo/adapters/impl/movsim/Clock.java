package fr.netixx.AutoTopo.adapters.impl.movsim;

import java.util.Random;

import fr.netixx.AutoTopo.Settings;
import fr.netixx.AutoTopo.adapters.IClock;

public class Clock implements IClock {

	private double clockValue;

	/**
	 * Skew replicates imperfect synchronization happening in real life This
	 * way, clocks are not triggered all at the same time
	 */
	private static final double variance = Settings.getDouble(Settings.CLOCK_SKEW_VARIANCE);

	private Random generator = new Random();

	public Clock() {
		clockValue = 0;
	}

	@Override
	public double getTime() {
		return clockValue + generator.nextGaussian() * variance;
	}

	void setClock(double time) {
		clockValue = time;
	}

}
