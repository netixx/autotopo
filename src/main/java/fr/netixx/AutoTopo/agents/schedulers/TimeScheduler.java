package fr.netixx.AutoTopo.agents.schedulers;

import fr.netixx.AutoTopo.adapters.IClock;



public class TimeScheduler implements IScheduler {

	private final double timeInterval;
	private IClock clock;
	private double lastTick;

	public TimeScheduler(double timeInterval, IClock clock) {
		this.timeInterval = timeInterval;
		this.clock = clock;
		lastTick = clock.getTime();
	}

	@Override
	public boolean shouldRun() {
		if ((clock.getTime() - lastTick) > timeInterval) {

			return true;
		}
		return false;
	}

	@Override
	public void reset() {
		this.lastTick = clock.getTime();
	}


}
