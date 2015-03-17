package fr.netixx.AutoTopo.adapters;

import fr.netixx.AutoTopo.notifications.goals.LaneChangeGoal;
import fr.netixx.AutoTopo.notifications.goals.SpeedGoal;

public interface IAgent {
	public int getId();

	public int getScopeId();

	public SpeedGoal getGoalSpeed();

	public LaneChangeGoal getGoalLaneChange();
}
