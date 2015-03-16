package fr.netixx.AutoTopo.notifications.aggregation;

import fr.netixx.AutoTopo.adapters.IDirection;

public class DirectionHelper {

	/**
	 * returns d1 - d2
	 *
	 * @param d1
	 * @param d2
	 * @return
	 */
	public static IDirection difference(IDirection d1, IDirection d2) {
		double cosx = d1.cosTheta()*d2.cosTheta() + d1.sinTheta()*d2.sinTheta();
		double sinx = d1.sinTheta() * d2.cosTheta() - d2.sinTheta() * d1.cosTheta();
		return new Direction(cosx, sinx);
	}

	public static IDirection absDifference(IDirection d1, IDirection d2) {
		double cosx = d1.cosTheta() * d2.cosTheta() + d1.sinTheta() * d2.sinTheta();
		double sinx = d1.sinTheta() * d2.cosTheta() - d2.sinTheta() * d1.cosTheta();
		return new Direction(cosx, Math.abs(sinx));
	}
}
