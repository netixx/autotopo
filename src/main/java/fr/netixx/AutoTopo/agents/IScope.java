package fr.netixx.AutoTopo.agents;


/**
 * Agents belong to scopes
 * @author francois
 *
 */
public interface IScope {

	public int getId();

	public int getScore();

	public void setScore(int score);
}
