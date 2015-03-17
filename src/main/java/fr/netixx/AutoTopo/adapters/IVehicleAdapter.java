package fr.netixx.AutoTopo.adapters;

public interface IVehicleAdapter {

	public double getLong();

	public double getLat();

	public double getSpeed();

	public double getAcceleration();

	public double getSize();

	public void setScopeId(int scopeId);

	public void setIsLeader(boolean isLeader);

	public int getLane();

	public void changeRoute(String routeName);

	public String getRouteName();

	public double getLength();

	public IDirection getDirection();

}
