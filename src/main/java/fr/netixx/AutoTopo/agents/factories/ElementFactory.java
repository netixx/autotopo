package fr.netixx.AutoTopo.agents.factories;

import java.util.Collection;

import fr.netixx.AutoTopo.Settings;
import fr.netixx.AutoTopo.adapters.IClock;
import fr.netixx.AutoTopo.adapters.IVehicleAdapter;
import fr.netixx.AutoTopo.adapters.io.IEntryPoint;
import fr.netixx.AutoTopo.agents.Agent;
import fr.netixx.AutoTopo.agents.IEventsCounter;
import fr.netixx.AutoTopo.agents.Resolver;
import fr.netixx.AutoTopo.agents.RoadCoordinator;
import fr.netixx.AutoTopo.agents.RoadSegmentCoordinator;
import fr.netixx.AutoTopo.agents.schedulers.EventScheduler;
import fr.netixx.AutoTopo.agents.schedulers.IScheduler;
import fr.netixx.AutoTopo.agents.schedulers.TimeScheduler;

public class ElementFactory {
	public static final double SCHEDULER_AGENTS_TIME_INTERVAL = Settings.getDouble(Settings.SCHEDULER_AGENTS_TIME_INTERVAL);
	public static final int SCHEDULER_AGENTS_EVENTS_NUMBER = Settings.getInt(Settings.SCHEDULER_AGENTS_EVENTS_NUMBER);
	public static final double SCHEDULER_ROADSEGMENTS_TIME_INTERVAL = Settings.getDouble(Settings.SCHEDULER_ROADSEGMENTS_TIME_INTERVAL);
	public static final int SCHEDULER_ROADSEGMENTS_EVENTS_NUMBER = Settings.getInt(Settings.SCHEDULER_ROADSEGMENTS_EVENTS_NUMBER);
	public static final double SCHEDULER_ROADS_TIME_INTERVAL = Settings.getDouble(Settings.SCHEDULER_ROADS_TIME_INTERVAL);
	public static final int SCHEDULER_ROADS_EVENTS_NUMBER = Settings.getInt(Settings.SCHEDULER_ROADS_EVENTS_NUMBER);

	public static Agent newAgent(final IEntryPoint<Agent> roadSegCoordinator, final IVehicleAdapter vehicle, IClock clock) {
		Agent a = new Agent((RoadSegmentCoordinator) roadSegCoordinator, vehicle, clock);

		addSchedulers(a.getSchedulers(), SCHEDULER_AGENTS_TIME_INTERVAL, SCHEDULER_AGENTS_EVENTS_NUMBER, clock, a.getEventsCounter());
		Resolver.put(a, a.getConnectionManager());
		return a;

	}

	public static RoadCoordinator newRoadCoordinator(IClock clock) {
		RoadCoordinator r = new RoadCoordinator(clock);
		r.getSchedulers().add(new TimeScheduler(SCHEDULER_ROADS_TIME_INTERVAL, clock));
		addSchedulers(r.getSchedulers(), SCHEDULER_ROADSEGMENTS_TIME_INTERVAL, SCHEDULER_ROADS_EVENTS_NUMBER, clock, r.getEventsCounter());
		Resolver.put(r, r.getConnectionManager());
		return r;
	}

	public static RoadSegmentCoordinator newRoadSegmentCoordinator(RoadCoordinator parent, int id, int nextid, double endOfSegment, IClock clock) {
		RoadSegmentCoordinator r = new RoadSegmentCoordinator(parent, id, nextid, endOfSegment, clock);
		addSchedulers(r.getSchedulers(), SCHEDULER_ROADSEGMENTS_TIME_INTERVAL, SCHEDULER_ROADSEGMENTS_EVENTS_NUMBER, clock, r.getEventsCounter());
		Resolver.put(r, r.getConnectionManager());
		return r;
	}

	private static void addSchedulers(Collection<IScheduler> schedulers, double timeInterval, int eventsTrigger, IClock clock, IEventsCounter counter) {
		if (timeInterval >= 0) {
			schedulers.add(new TimeScheduler(timeInterval, clock));
		}
		if (eventsTrigger >= 0) {
			schedulers.add(new EventScheduler(eventsTrigger, counter));
		}
	}

}
