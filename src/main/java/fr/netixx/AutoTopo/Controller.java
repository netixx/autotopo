package fr.netixx.AutoTopo;

import java.nio.file.Paths;
import java.util.Properties;

import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;
import org.kohsuke.args4j.Option;

import fr.netixx.AutoTopo.adapters.IClock;
import fr.netixx.AutoTopo.adapters.IController;
import fr.netixx.AutoTopo.adapters.io.IEntryPoint;
import fr.netixx.AutoTopo.agents.Agent;
import fr.netixx.AutoTopo.agents.Resolver;
import fr.netixx.AutoTopo.agents.RoadCoordinator;
import fr.netixx.AutoTopo.agents.RoadSegmentCoordinator;
import fr.netixx.AutoTopo.agents.factories.ConnectionManagerFactory;
import fr.netixx.AutoTopo.agents.factories.ElementFactory;
import fr.netixx.AutoTopo.statistics.IStatistic;

public class Controller implements IController {

	private final static CmdParser parser = new CmdParser();
	final private static String logConfigFile = "log4j2.xml";

	public static void initialize(String[] args) {
		if (args == null)
			args = new String[] {};
		parser.doParse(args);
		initLogs();
		initSettings();

	}

	private static void initSettings() {
		if (parser.propertiesFilePath != null)
			Settings.load(Paths.get(parser.propertiesFilePath));
	}

	private static void initLogs() {
		final Properties props = System.getProperties();
		props.setProperty("log4j.configurationFile", logConfigFile);
	}

	private static class CmdParser {

		@Option(name = "--config", aliases = "-c", usage = "Path to the properties file", metaVar = "PROPS_FILE", required = false)
		private final String propertiesFilePath = "autotopo-config.properties";

		@Option(name = "--csv", usage = "Path to the csv output dir", metaVar = "CSV_FILE", required = false)
		private final String csvDirPath = "output";

		public void doParse(final String[] args) {
			final CmdLineParser parser = new CmdLineParser(this);

			try {
				parser.parseArgument(args);
			} catch (final CmdLineException e) {
				e.printStackTrace();
			}
		}

	}

	public static RoadCoordinator readCoordinators(IClock clock) {
		return ElementFactory.newRoadCoordinator(clock);
	}

	public static IEntryPoint<Agent> readSegments(RoadCoordinator root, IClock clock) {
		// int controllerId = root.getId();
		IEntryPoint<Agent> p = null;
		int entrypoint = Settings.getInt(Settings.ROADSEGMENTS_INSTANCES_START);
		int cur = entrypoint;
		do {
			int next = Settings.getInt(Settings.ROADSEGMENTS_INSTANCES_PREFIX + cur + Settings.ROADSEGMENTS_INSTANCES_NEXT);
			double end = 0;
			if (next != 0) {
				end = Settings.getDouble(Settings.ROADSEGMENTS_INSTANCES_PREFIX + cur + Settings.ROADSEGMENTS_INSTANCES_END);
			}
			RoadSegmentCoordinator roadSegment = ElementFactory.newRoadSegmentCoordinator(root, cur, next, end, clock);
			Resolver.getRoadCoordinator(root).connect(roadSegment);
			if (cur == entrypoint) {
				p = roadSegment;
			}
			cur = next;
		} while (cur != 0);

		return p;
	}

	public static void writeDefaultCsvs() {
		writeCsv(ConnectionManagerFactory.agentConnections);
		writeCsv(ConnectionManagerFactory.roadSegmentConnections);
	}

	public static void writeCsv(IStatistic stat) {
		stat.toCsv(Paths.get(parser.csvDirPath, stat.getName() + ".csv"));
	}
}
