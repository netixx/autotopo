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
import fr.netixx.AutoTopo.agents.IEventsCounter;

public class TotalConnections extends AbstractStatistic {

	private Map<IElement, IEventsCounter> connectionMap = new HashMap<>();

	private static boolean enabled = true;

	public TotalConnections(String name) {
		super(name, new String[] { "id", "connect" });
		// TODO Auto-generated constructor stub
	}

	public void record(IElement a, IEventsCounter counter) {
		if (enabled)
			connectionMap.put(a, counter);
	}

	public void toCsv(Path csv) {
		OpenOption[] opts = new OpenOption[] {
				// StandardOpenOption.WRITE, StandardOpenOption.CREATE
		};
		try (BufferedWriter writer = Files.newBufferedWriter(csv, Charset.forName("UTF-8"), opts)) {
			CSVWriter csvW = new CSVWriter(writer, ';');

			csvW.writeNext(this.getHeader());
			for (Entry<IElement, IEventsCounter> entry : connectionMap.entrySet()) {
				csvW.writeNext(new String[] { "" + entry.getKey().getId(), "" + entry.getValue().getEvents() });
			}
			csvW.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

}
