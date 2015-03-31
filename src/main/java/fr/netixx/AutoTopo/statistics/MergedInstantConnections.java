package fr.netixx.AutoTopo.statistics;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;

import au.com.bytecode.opencsv.CSVWriter;
import fr.netixx.AutoTopo.agents.IElement;

public class MergedInstantConnections<X extends IElement> extends AbstractStatistic {

	private static final String[] headers = new String[] { "id", "avg", "std", "max", "min" };

	private static boolean enabled = true;

	private Map<IElement, ConnectionsRecorder> connectionMap = new HashMap<>();
	private RecordFilter<X> filter = null;

	public MergedInstantConnections(String name) {
		super(name, headers);
	}

	public MergedInstantConnections(String name, RecordFilter<X> filter) {
		super(name, headers);
		this.filter = filter;
	}

	public void record(X el, int nConnections) {
		if (enabled) {
			if (filter != null && filter.filter(el))
				return;
			if (!connectionMap.containsKey(el)) {
				connectionMap.put(el, new ConnectionsRecorder(nConnections));
			} else {
				connectionMap.get(el).recordConnectionNumber(nConnections);
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
			for (Entry<IElement, ConnectionsRecorder> entry : connectionMap.entrySet()) {
				csvW.writeNext(new String[] { "" + entry.getKey().getId(), "" + entry.getValue().getAvg(), "" + entry.getValue().getStd(),
						"" + entry.getValue().getMax(), "" + entry.getValue().getMin() });
			}
			csvW.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
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
