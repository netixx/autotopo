package fr.netixx.AutoTopo.agents.clustering;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedList;
import java.util.List;

import fr.netixx.AutoTopo.Settings;
import fr.netixx.AutoTopo.agents.Agent;
import fr.netixx.AutoTopo.notifications.aggregation.AggregationHelper;

public class Clustering {

	private static final int MAX_SCOPE_NUMBER = Settings.getInt(Settings.MAX_SCOPE_NUMBER);
	private static final int MAX_SCOPE_NUMBER_THRESHOLD = MAX_SCOPE_NUMBER + Settings.getInt(Settings.MAX_SCOPE_NUMBER_THRESHOLD);
	private static final boolean SPEED_CLUSTERING_ENABLED = Settings.getBoolean(Settings.OPTIMIZE_ROADSEGMENT_SPEED_CLUSTERING_ENABLED);

	private Comparator<Merge> mergeComparator = createMergeComparator();

	public List<List<Agent>> merge(Collection<Agent> leaders) {
		// convert to better object
		ArrayList<Merge> merges = new ArrayList<>();
		for (Agent leader : leaders) {
			Merge m = new Merge(leader);
			merges.add(m);
		}
		Collections.sort(merges, mergeComparator);
		merges = checkAndMerge(merges, 0);
		List<List<Agent>> ret = new LinkedList<>();

		for (Merge m : merges) {
			// a merge might be performed (there are two leader who might be
			// able to merge)
			if (m.getMergesNumber() >= 1) {
				ret.add(m.leaders);
			}
		}

		return ret;
	}

	private ArrayList<Merge> checkAndMerge(ArrayList<Merge> merges, int takeIndex) {
		if (takeIndex >= merges.size()) {
			return merges;
		}
		Merge c = merges.get(takeIndex);
		for (Merge m : merges) {
			if (!c.equals(m) && m.canMerge(c) && m.shouldMerge(c)) {
				m.merge(c);
				merges.remove(takeIndex);
				Collections.sort(merges, mergeComparator);
				return checkAndMerge(merges, takeIndex);
			}
		}
		return checkAndMerge(merges, ++takeIndex);
	}

	private class Merge {
		LinkedList<Agent> leaders = new LinkedList<>();

		private int n = 0;

		Merge(Agent leader) {
			addLeader(leader);
		}

		private void merge(Merge merge) {
			for (Agent leader : merge.leaders) {
				addLeader(leader);
			}
		}

		private void addLeader(Agent leader) {
			leaders.add(leader);
			n += leader.getAggregate().getAggregationSize();
		}

		public int getN() {
			return n;
		}

		public int getMergesNumber() {
			return leaders.size() - 1;
		}

		private boolean inRange(Agent leader) {
			for (Agent l : leaders) {
				// check for range (best we can do)
				if (!leader.isInCommunicationRange(l)) {
					return false;
				}
			}
			return true;
		}

		public boolean canMerge(Merge merge) {
			if (merge.getN() + this.getN() > MAX_SCOPE_NUMBER_THRESHOLD)
				return false;
			for (Agent a : leaders) {
				if (!merge.inRange(a)) {
					return false;
				}
			}
			return true;
		}

		private boolean shouldMerge(Merge merge) {
			if (SPEED_CLUSTERING_ENABLED) {
				double meanSpeed1 = AggregationHelper.getMean(leaders).getSpeed();
				double meanSpeed2 = AggregationHelper.getMean(merge.leaders).getSpeed();
				Conditions.speed(meanSpeed1, meanSpeed2);
			}

			return true;
		}
	}

	private static Comparator<Merge> createMergeComparator() {
		return new Comparator<Merge>() {

			@Override
			public int compare(Merge o1, Merge o2) {
				if (o1 == null || o2 == null)
					throw new NullPointerException();
				// TODO : minus here ??
				return -Integer.compare(o1.getN(), o2.getN());
			}

		};
	}

}
