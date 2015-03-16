package fr.netixx.AutoTopo.helpers;

import fr.netixx.AutoTopo.adapters.IClock;

public abstract class ClockCachedObject<Obj> {

	private Obj o;

	private double modifiedTime;

	private final IClock clock;

	public ClockCachedObject(IClock clock) {
		this.clock = clock;
	}

	public Obj get() {
		return get(clock.getTime());
	}

	private Obj get(double accessTime) {
		if (o == null || modifiedTime < accessTime) {
			o = renew();
			modifiedTime = accessTime;
		}
		return o;
	}

	public void reset() {
		o = null;
	}

	public abstract Obj renew();

}
