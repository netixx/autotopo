package fr.netixx.AutoTopo.statistics;

abstract class AbstractStatistic implements IStatistic {

	protected String name;
	protected String[] header;

	protected AbstractStatistic(String name, String[] header) {
		this.name = name;
		this.header = header;
	}

	@Override
	public String getName() {
		return this.name;
	}

	@Override
	public String[] getHeader() {
		return header;
	}

}
