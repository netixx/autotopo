package fr.netixx.AutoTopo.notifications.aggregation;

import java.util.Arrays;

import fr.netixx.AutoTopo.adapters.IDirection;
import fr.netixx.AutoTopo.helpers.Units;
import fr.netixx.AutoTopo.notifications.IPullNotification;

public class Aggregation implements IPullNotification {

	final double speed;
	final double acc;
	public final IDirection direction;
	final double totalArea;
	final double latitude, longitude;
	final double maxlatitude, maxlongitude, minlatitude, minlongitude;
	final double barycentricLatitude, barycentricLongitude;
	final int aggregationSize;
	final double time;

	/**
	 * Constructor for single Agent
	 *
	 * @param speed
	 * @param xSpeed
	 * @param ySpeed
	 * @param totalArea
	 * @param latitude
	 * @param longitude
	 * @param barycentricLatitude
	 * @param barycentricLongitude
	 * @param aggregationSize
	 * @param time
	 */
	public Aggregation(double speed,
			double acc,
			IDirection direction,
			double totalArea,
			double latitude, double longitude,
			double barycentricLatitude,
			double barycentricLongitude,
			int aggregationSize, double time) {

		this.speed = speed;
		this.acc = acc;
		this.direction = direction;
		this.totalArea = totalArea;
		this.latitude = latitude;
		this.longitude = longitude;
		this.minlatitude = latitude;
		this.maxlatitude = latitude;
		this.minlongitude = longitude;
		this.maxlongitude = longitude;
		this.barycentricLatitude = barycentricLatitude;
		this.barycentricLongitude = barycentricLongitude;
		this.aggregationSize = aggregationSize;
		this.time = time;
	}

	/**
	 * Constructor for aggregated results
	 *
	 * @param speed
	 * @param xSpeed
	 * @param ySpeed
	 * @param totalArea
	 * @param latitude
	 * @param longitude
	 * @param minlatitude
	 * @param minlongitude
	 * @param maxlatitude
	 * @param maxlongitude
	 * @param barycentricLatitude
	 * @param barycentricLongitude
	 * @param aggregationSize
	 * @param time
	 */
	public Aggregation(double speed,
			double acc,
			IDirection direction,
			double totalArea,
			double latitude, double longitude, double minlatitude,
			double minlongitude, double maxlatitude, double maxlongitude,
			double barycentricLatitude, double barycentricLongitude,
			int aggregationSize, double time) {

		this.speed = speed;
		this.acc = acc;
		this.direction = direction;
		this.totalArea = totalArea;
		this.latitude = latitude;
		this.longitude = longitude;
		this.minlatitude = minlatitude;
		this.minlongitude = minlongitude;
		this.maxlatitude = maxlatitude;
		this.maxlongitude = maxlongitude;
		this.barycentricLatitude = barycentricLatitude;
		this.barycentricLongitude = barycentricLongitude;
		this.aggregationSize = aggregationSize;
		this.time = time;
	}

	public Aggregation() {
		this.direction = null;
		this.speed = 0;
		this.acc = 0;
		this.totalArea = 0;
		this.latitude = 0;
		this.longitude = 0;
		this.minlatitude = 0;
		this.maxlatitude = 0;
		this.minlongitude = 0;
		this.maxlongitude = 0;
		this.barycentricLatitude = 0;
		this.barycentricLongitude = 0;
		this.aggregationSize = 0;
		this.time = 0;
	}

	public static Aggregation aggregate(Iterable<Aggregation> aggregates) {
		double speed = 0;
		double acc = 0;
		double totalArea = 0;
		double latitude = 0;
		double longitude = 0;
		double minlatitude = Double.MAX_VALUE;
		double minlongitude = Double.MAX_VALUE;
		double maxlatitude = Double.MIN_VALUE;
		double maxlongitude = Double.MIN_VALUE;
		double barycentricLatitude = 0;
		double barycentricLongitude = 0;
		int aggregationSize = 0;
		double time = 0;

		double totalcos = 0;
		double totalsin = 0;

		for (Aggregation agg : aggregates) {
			speed += agg.speed * agg.aggregationSize;
			acc += agg.acc*aggregationSize;
			totalArea += agg.totalArea * agg.aggregationSize;
			latitude += agg.latitude * agg.aggregationSize;
			longitude += agg.longitude * agg.aggregationSize;
			barycentricLatitude += agg.barycentricLatitude * agg.totalArea;
			barycentricLongitude += agg.barycentricLongitude * agg.totalArea;
			aggregationSize += agg.aggregationSize;
			time += agg.time;
			minlatitude = Math.min(minlatitude, agg.minlatitude);
			minlongitude = Math.min(minlongitude, agg.minlongitude);
			maxlatitude = Math.max(maxlatitude, agg.maxlatitude);
			maxlongitude = Math.max(maxlongitude, agg.maxlongitude);
			if (agg.direction != null) {
				totalcos += agg.direction.cosTheta();
				totalsin += agg.direction.sinTheta();
			}
		}
		if (aggregationSize <= 0) {
			return new Aggregation();
		}
		speed /= aggregationSize;
		acc /= aggregationSize;
		latitude /= aggregationSize;
		longitude /= aggregationSize;
		time /= aggregationSize;

		barycentricLatitude /= totalArea;
		barycentricLongitude /= totalArea;
		double cosx = 0, sinx = 0;
		if (totalsin == 0) {
			cosx = totalcos /= aggregationSize;
			sinx = 0;
		} else {
			final double x = totalcos / totalsin;
			cosx = 1 / Math.sqrt(1 + x * x);
			sinx = x / Math.sqrt(1 + x * x);
		}
		Direction d = new Direction(cosx, sinx);

		return new Aggregation(speed,
				acc,
				d,
				totalArea,
				latitude, longitude,
				minlatitude, minlongitude, maxlatitude, maxlongitude,
				barycentricLatitude, barycentricLongitude,
				aggregationSize,
				time);
	}

	public static Aggregation aggregate(Aggregation... aggs) {
		return aggregate(Arrays.asList(aggs));
	}

	public Aggregation absDistance(Aggregation target) {
		return AggregationHelper.absDistance(this, target);
	}

	public Aggregation difference(Aggregation target) {
		return AggregationHelper.difference(this, target);
	}

	@Override
	public String toString() {
		return String.format("Lat: %.4f, Long: %.4f\n"
				+ "Speed:\t%.4f (km/h)\n"
				+ "Area:\t%.4f\n"
				+ "Size:\t%d",
				this.latitude, this.longitude,
				this.speed * Units.MS_TO_KMH,
				this.totalArea,
				this.aggregationSize);
	}

	public String printLongLat() {
		return String.format("long: %.4f, lat: %.4f", this.longitude, this.latitude);
	}
	public int getAggregationSize() {
		return aggregationSize;
	}

	public double getTime() {
		return this.time;
	}

	public double getSpeed() {
		return this.speed;
	}

}
