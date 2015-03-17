package fr.netixx.AutoTopo.adapters;

import fr.netixx.AutoTopo.notifications.goals.LaneChangeGoal;
import fr.netixx.AutoTopo.notifications.goals.SpeedGoal;

public interface IVehicleRevAdapter {
	public int getScopeId();

	public int getAutoTopoId();

	public SpeedGoal getAutoTopoSpeedGoal();

	public LaneChangeGoal getAutoTopoLaneChangeGoal();

}
