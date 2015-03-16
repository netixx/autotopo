package fr.netixx.AutoTopo.statistics;

import java.nio.file.Path;

public interface IStatistic {
	public String getName();

	public String[] getHeader();

	public void toCsv(Path csv);
}
