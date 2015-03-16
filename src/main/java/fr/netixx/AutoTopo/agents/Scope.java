package fr.netixx.AutoTopo.agents;


public class Scope implements IScope {

	private static int curId = 0;

	private int score = 0;

	private final int id;

	public Scope() {
		id = ++curId;
	}

	@Override
	public int getId() {
		return id;
	}


	@Override
	public int getScore() {
		return score;
	}

	@Override
	public void setScore(int sc) {
		score = sc;
	}

	@Override
	public String toString() {
		return String.format("Scope id: %d score: %d", id, score);
	}
}
