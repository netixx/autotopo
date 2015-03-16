package fr.netixx.AutoTopo.adapters;

public interface IDirection {

	public double cosTheta();

	public double sinTheta();

	public double getLongitudeProjection(double value);

	public double getLatitudeProjection(double value);
}
