package fr.netixx.AutoTopo.statistics;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Path;
import java.util.Map.Entry;
import java.util.SortedMap;
import java.util.TreeMap;

import au.com.bytecode.opencsv.CSVWriter;

public class TimeInstantConnections extends AbstractStatistic {

	private static boolean enabled = true;

	private SortedMap<Double, ConnectionsRecorder> connectionMap = new TreeMap<>();

	public TimeInstantConnections(String name) {
		super(name, new String[] { "time", "avg", "std", "max", "min" });
	}

	public void record(Double time, int nConnections) {
		if (enabled && nConnections > 0) {
			if (!connectionMap.containsKey(time)) {
				connectionMap.put(time, new ConnectionsRecorder(nConnections));
			} else {
				connectionMap.get(time).recordConnectionNumber(nConnections);
			}
		}

		// el.getConnectionManager().getConnectedChildren().size();
	}

	@Override
	public void toCsv(Path csv) {
		OpenOption[] opts = new OpenOption[] {
				// StandardOpenOption .WRITE, StandardOpenOption.CREATE
		};
		try (BufferedWriter writer = Files.newBufferedWriter(csv, Charset.forName("UTF-8"), opts)) {
			CSVWriter csvW = new CSVWriter(writer, ';');

			csvW.writeNext(this.getHeader());
			for (Entry<Double, ConnectionsRecorder> entry : connectionMap.entrySet()) {
				csvW.writeNext(new String[] { "" + entry.getKey(), "" + entry.getValue().getAvg(), "" + entry.getValue().getStd(),
						"" + entry.getValue().getMax(), "" + entry.getValue().getMin() });
			}
			csvW.close();
		} catch (IOException e) {
			e.printStackTrace();
		}

	}

	private class ConnectionsRecorder {
		int n = 0;
		int max = 0;
		int min = 0;
		double m = 0;
		double s = 0;

		ConnectionsRecorder(int nConnections) {
			n = 1;
			max = nConnections;
			min = nConnections;
			recordConnectionNumber(nConnections);
		}

		void recordConnectionNumber(int nConnections) {
			max = Math.max(nConnections, max);
			min = Math.min(nConnections, min);
			double tmpM = m;
			m += (nConnections - tmpM) / n;
			s += (nConnections - tmpM) * (nConnections - m);
			n++;
		}

		double getAvg() {
			return m;
		}

		double getVariance() {
			return s / (n - 1);
		}

		double getStd() {
			return Math.sqrt(getVariance());
		}

		int getMax() {
			return max;
		}

		int getMin() {
			return min;
		}

	}

}
