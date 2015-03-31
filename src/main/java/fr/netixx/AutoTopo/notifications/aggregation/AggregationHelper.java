package fr.netixx.AutoTopo.notifications.aggregation;

import java.util.Comparator;
import java.util.Iterator;

import fr.netixx.AutoTopo.Settings;
import fr.netixx.AutoTopo.agents.Agent;

public class AggregationHelper {
	private final static double ANTICIPATION_SECONDS = Settings.getDouble(Settings.OPTIMIZE_ANTICIPATION_POSITION_SECONDS);

	public static boolean closerPositionEuler(Aggregation agg1, Aggregation agg2) {
		return (square(agg1.latitude) + square(agg1.longitude)) < (square(agg2.longitude) + square(agg2.latitude));
	}

	public static double eulerDistance(Aggregation agg) {
		return eulerDistance(agg.latitude, agg.longitude);
	}

	public static double minEulerDistance(Aggregation agg1, Aggregation agg2) {
		return Math.min(eulerDistance(agg1.minlatitude - agg2.maxlatitude, agg1.minlongitude - agg2.maxlongitude),
				eulerDistance(agg2.minlatitude - agg1.maxlatitude, agg2.minlongitude - agg1.maxlongitude));
	}

	public static double minRoadDistance(Aggregation agg1, Aggregation agg2) {
		return Math.min(Math.abs(agg1.minCurvAbsc - agg2.maxCurvAbsc), Math.abs(agg2.minCurvAbsc - agg1.maxCurvAbsc));
	}

	private static double eulerDistance(double latitude, double longitude) {
		return Math.sqrt(square(latitude) + square(longitude));
	}

	private static double square(double num) {
		return num * num;
	}

	public static Aggregation absDistance(Aggregation agg1, Aggregation agg2) {
		return new Aggregation(Math.abs(agg1.speed - agg2.speed),
				Math.abs(agg1.acc - agg2.acc),
				DirectionHelper.absDifference(agg1.direction, agg2.direction),
				Math.abs(agg1.totalArea - agg2.totalArea),
				Math.abs(agg1.latitude - agg2.latitude), Math.abs(agg1.longitude - agg2.longitude),
				Math.abs(agg1.minlatitude - agg2.minlatitude), Math.abs(agg1.minlongitude - agg2.minlongitude),
				Math.abs(agg1.maxlatitude - agg2.maxlatitude), Math.abs(agg1.maxlongitude - agg2.maxlongitude),
				Math.abs(agg1.barycentricLatitude
						- agg2.barycentricLatitude),
						Math.abs(agg1.barycentricLongitude - agg2.barycentricLongitude),
						Math.abs(agg1.curvAbsc - agg2.curvAbsc), Math.abs(agg1.minCurvAbsc - agg2.minCurvAbsc),
						Math.abs(agg1.maxCurvAbsc - agg2.maxCurvAbsc),
						Math.abs(agg1.aggregationSize - agg2.aggregationSize),
						Math.abs(agg1.time - agg2.time));
	}

	public static Aggregation difference(Aggregation agg1, Aggregation agg2) {
		return new Aggregation(agg1.speed - agg2.speed,
				agg1.acc - agg2.acc,
				DirectionHelper.difference(agg1.direction, agg2.direction),
				agg1.totalArea - agg2.totalArea,
				agg1.latitude - agg2.latitude, agg1.longitude - agg2.longitude,
				agg1.minlatitude - agg2.minlatitude, agg1.minlongitude - agg2.minlongitude,
				agg1.maxlatitude - agg2.maxlatitude, agg1.maxlongitude - agg2.maxlongitude,
				agg1.barycentricLatitude - agg2.barycentricLatitude, agg1.barycentricLongitude - agg2.barycentricLongitude,
				agg1.curvAbsc - agg2.curvAbsc, agg1.minCurvAbsc - agg2.minCurvAbsc, agg1.maxCurvAbsc - agg2.maxCurvAbsc,
				agg1.aggregationSize - agg2.aggregationSize,
				agg1.time - agg2.time);
	}

	public static double longDistance(Aggregation agg) {
		return Math.abs(agg.longitude);
	}

	public static double curvDistance(Aggregation agg) {
		return Math.abs(agg.curvAbsc);
	}

	public static double minCurvDistance(Aggregation agg) {
		return Math.abs(agg.minCurvAbsc);
	}

	public static double maxCurvDistance(Aggregation agg) {
		return Math.abs(agg.maxCurvAbsc);
	}

	public static double minLongDistance(Aggregation agg) {
		return Math.abs(agg.minlongitude);
	}

	public static double maxLongDistance(Aggregation agg) {
		return Math.abs(agg.maxlongitude);
	}

	public static Comparator<Aggregation> createDistanceAggregationComparator() {
		return new Comparator<Aggregation>() {

			@Override
			public int compare(Aggregation o1, Aggregation o2) {
				if (o1 == null || o2 == null)
					throw new NullPointerException();

				return Double.compare(eulerDistance(o1), eulerDistance(o2));
			}

		};
	}

	public static Comparator<Aggregation> createReverseDistanceAggregationComparator() {
		return new Comparator<Aggregation>() {

			@Override
			public int compare(Aggregation o1, Aggregation o2) {
				if (o1 == null || o2 == null)
					throw new NullPointerException();

				return -Double.compare(eulerDistance(o1), eulerDistance(o2));
			}

		};
	}

	public static Comparator<Aggregation> createDistanceAndSpeedAggregationComparator() {
		/*
		 * Take into account speed in closeness evaluation
		 * Idea : if a vehicle is close but its speed is very different, it will
		 * be far in the next seconds
		 *
		 * Thus : compare pos + speed * anticipation
		 */
		return new Comparator<Aggregation>() {

			@Override
			public int compare(Aggregation o1, Aggregation o2) {
				if (o1 == null || o2 == null)
					throw new NullPointerException();
				double d1 = eulerDistance(o1.latitude + o1.direction.getLatitudeProjection(o1.speed) * ANTICIPATION_SECONDS, o1.longitude
						+ o1.direction.getLongitudeProjection(o1.speed) * ANTICIPATION_SECONDS);
				double d2 = eulerDistance(o2.latitude + o2.direction.getLatitudeProjection(o2.speed) * ANTICIPATION_SECONDS, o2.longitude
						+ o2.direction.getLongitudeProjection(o2.speed) * ANTICIPATION_SECONDS);
				return Double.compare(d1, d2);
			}

		};
	}

	public static Comparator<Aggregation> createDistanceAndSpeedAndAccelerationAggregationComparator() {
		/*
		 * Take into account speed in closeness evaluation
		 * Idea : if a vehicle is close but its speed is very different, it will
		 * be far in the next seconds
		 *
		 * Thus : add speed differential * anticipation time to distance
		 */
		return new Comparator<Aggregation>() {

			@Override
			public int compare(Aggregation o1, Aggregation o2) {
				if (o1 == null || o2 == null)
					throw new NullPointerException();
				double d1 = eulerDistance(
						o1.latitude + o1.direction.getLatitudeProjection(o1.speed) * ANTICIPATION_SECONDS
						+ o1.direction.getLatitudeProjection(o1.acc) / 2.0 * ANTICIPATION_SECONDS * ANTICIPATION_SECONDS,
						o1.longitude + o1.direction.getLongitudeProjection(o1.speed) * ANTICIPATION_SECONDS
						+ o1.direction.getLongitudeProjection(o1.acc) / 2.0 * ANTICIPATION_SECONDS * ANTICIPATION_SECONDS);
				double d2 = eulerDistance(
						o2.latitude + o2.direction.getLatitudeProjection(o2.speed) * ANTICIPATION_SECONDS
						+ o2.direction.getLatitudeProjection(o2.acc) / 2.0 * ANTICIPATION_SECONDS * ANTICIPATION_SECONDS,
						o2.longitude + o2.direction.getLongitudeProjection(o2.speed) * ANTICIPATION_SECONDS
						+ o2.direction.getLongitudeProjection(o2.acc) / 2.0 * ANTICIPATION_SECONDS * ANTICIPATION_SECONDS);
				return Double.compare(d1, d2);
			}

		};
	}

	public static Aggregation getMean(Iterable<Agent> agents) {
		final Iterator<Agent> it = agents.iterator();
		return Aggregation.aggregate(new Iterable<Aggregation>() {

			@Override
			public Iterator<Aggregation> iterator() {
				return new Iterator<Aggregation>() {

					@Override
					public boolean hasNext() {
						return it.hasNext();
					}

					@Override
					public Aggregation next() {
						return it.next().getAggregate();
					}

					@Override
					public void remove() {
						it.remove();

					}

				};
			}

		});
	}
}
