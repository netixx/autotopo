package fr.netixx.AutoTopo;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Properties;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import fr.netixx.AutoTopo.helpers.ResourcesHelper;

public class Settings {

	/**
	 * Constants for keys in properties file
	 */
	public static final String MAX_SCOPE_NUMBER = "agent.scope.number.max";
	public static final String MAX_VEHICLE_CONNECTIONS_DISTANCE = "agent.connections.distance.max";
	public static final String MAX_SCOPE_NUMBER_THRESHOLD = "agent.scope.number.threshold";
	public static final String MAX_VEHICLE_CONNECTIONS_DISTANCE_THRESHOLD = "agent.connections.distance.threshold";
	public static final String MAX_ROAD_SEGMENT_COORDINATOR_CONNECTIONS = "roadsegments.max_connections";

	public static final String ROADSEGMENTS_INSTANCES_PREFIX = "roadsegments.instances.";
	// TODO : remove start ?
	public static final String ROADSEGMENTS_INSTANCES_START = ROADSEGMENTS_INSTANCES_PREFIX + "start";
	public static final String ROADSEGMENTS_INSTANCES_END = ".end";
	public static final String ROADSEGMENTS_INSTANCES_NEXT = ".next";

	public static final String SCHEDULER_AGENTS_TIME_INTERVAL = "scheduler.agents.time.interval";
	public static final String SCHEDULER_AGENTS_EVENTS_NUMBER = "scheduler.agents.events.number";
	public static final String SCHEDULER_ROADSEGMENTS_TIME_INTERVAL = "scheduler.roadsegments.time.interval";
	public static final String SCHEDULER_ROADSEGMENTS_EVENTS_NUMBER = "scheduler.roadsegments.events.number";
	public static final String SCHEDULER_ROADS_TIME_INTERVAL = "scheduler.roads.time.interval";
	public static final String SCHEDULER_ROADS_EVENTS_NUMBER = "scheduler.roads.events.number";

	public static final String CLOCK_SKEW_VARIANCE = "clock.skew.variance";

	public static final String ROADSEGMENTS_TRAFFICJAM_INTERDISTANCE = "roadsegments.trafficjam.interjamdistance";
	public static final String ROADSEGMENTS_TRAFFICJAM_ENABLED = "roadsegments.trafficjam.enabled";
	public static final String ROADSEGMENTS_TRAFFICJAM_JAMFACTOR = "roadsegments.trafficjam.jamfactor";
	public static final String ROADSEGMENTS_TRAFFICJAM_SPEED_FACTOR = "roadsegments.trafficjam.speed-limit.factor";
	public static final String AGENT_TRAFFICJAM_SPEED_DISTANCE = "agent.trafficjam.speed-limit.distance";

	public static final String OPTIMIZE_AGENT_RECENTER_LEADER_ENABLED = "optimize.agent.recenter-leader.enabled";
	public static final String OPTIMIZE_AGENT_RECENTER_LEADER_BIAS = "optimize.agent.recenter-leader.bias";
	public static final String OPTIMIZE_AGENT_RECENTER_LEADER_PERIOD = "optimize.agent.recenter-leader.period";
	public static final String OPTIMIZE_ROADSEGMENT_SPEED_CLUSTERING_ENABLED = "optimize.roadsegment.speed-clustering.enabled";
	public static final String OPTIMIZE_ROADSEGMENT_SPEED_CLUSTERING_FACTOR = "optimize.roadsegment.speed-clustering.factor";

	public static final String OPTIMIZE_ANTICIPATION_POSITION_SECONDS = "optimize.anticipation.position.seconds";

	public static final String SPEED_LIMIT_DEFAULT = "speed.limit.default";

	private static String defaultConfigFile = "default-config.properties";

	private final static Logger logger = LogManager.getLogger();

	private static Properties defaults;
	private static Properties props;

	static {
		defaults = new Properties();
		try {
			defaults.load(ResourcesHelper.getResourceStream(defaultConfigFile));
		} catch (final IOException e) {
			logger.error("Could not read default properties file at " + defaultConfigFile, e);
		}
		props = new Properties(defaults);
	}



	static void load(final Path propsPath) {
		final OpenOption options = StandardOpenOption.READ;
		try {
			props.load(Files.newInputStream(propsPath, options));
			logger.info("Load properties from {}", propsPath);
		} catch (final IOException e) {
			logger.error("Could not read properties file at '{}', using only default properties.", propsPath);
		}
	}

	public static int getInt(final String key) {
		return Integer.parseInt(props.getProperty(key));
	}

	public static float getFloat(final String key) {
		return Float.parseFloat(props.getProperty(key));
	}

	public static double getDouble(final String key) {
		return Double.parseDouble(props.getProperty(key));
	}

	public static String getString(final String key) {
		return props.getProperty(key);
	}

	public static boolean getBoolean(final String key) {
		return Boolean.parseBoolean(props.getProperty(key));
	}

}
