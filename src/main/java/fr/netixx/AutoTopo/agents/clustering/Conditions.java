package fr.netixx.AutoTopo.agents.clustering;

import fr.netixx.AutoTopo.Settings;

/**
 * Created by francois on 16/06/15.
 */
public class Conditions {

    private static final double SPEED_CLUSTERING_FACTOR = Settings.getDouble(Settings.OPTIMIZE_ROADSEGMENT_SPEED_CLUSTERING_FACTOR);
    private static final double AGENTS_MAX_DISTANCE = Settings.getDouble(Settings.MAX_VEHICLE_CONNECTIONS_DISTANCE);

    private static final double SPEED_CLUSTERING_THRESHOLD = AGENTS_MAX_DISTANCE * SPEED_CLUSTERING_FACTOR;

    public static boolean speed(double speed1, double speed2) {
        return (Math.abs(speed1 - speed2) <= SPEED_CLUSTERING_THRESHOLD);
    }

}
