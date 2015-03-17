package fr.netixx.AutoTopo.agents;


import java.util.Collection;
import java.util.LinkedList;

import fr.netixx.AutoTopo.adapters.IClock;
import fr.netixx.AutoTopo.agents.schedulers.IScheduler;
import fr.netixx.AutoTopo.helpers.ClockCachedObject;
import fr.netixx.AutoTopo.notifications.IPullNotification;
import fr.netixx.AutoTopo.notifications.IPushNotification;
import fr.netixx.AutoTopo.notifications.aggregation.Aggregation;
import fr.netixx.AutoTopo.notifications.conditions.IStopCondition;

public abstract class AbstractElement<Child extends IElement> implements IElement {

	protected ETopoElement level;
	protected IElement parent;
	protected int id;
	protected IClock clock;

	protected ConnectionManager<Child> connectionManager;
	protected Collection<IScheduler> schedulers = new LinkedList<>();
	protected IEventsCounter eventsCounter = new EventsCounter();

	public AbstractElement(ETopoElement level, IElement parent, IClock clock) {
		this.level = level;
		this.parent = parent;
		this.clock = clock;
		aggregate = new ClockCachedObject<Aggregation>(clock) {

			@Override
			public Aggregation renew() {
				return aggregate();
			}

		};
	}

	@Override
	public IElement getParent() {
		return parent;
	}

	public Collection<IScheduler> getSchedulers() {
		return schedulers;
	}

	public IEventsCounter getEventsCounter() {
		return eventsCounter;
	}

	@Override
	public void broadCast(IPushNotification o, IStopCondition stopCondition) {
		this.treatNotification(o);
		if (! stopCondition.stop(this))
			for (Child c : this.getConnectionManager().getConnectedChildren())
				c.broadCast(o, stopCondition);
	}

	@Override
	public void collect(IPullNotification o, IStopCondition stopCondition) {
		this.treatNotification(o);
		if (! stopCondition.stop(this))
			this.getParent().collect(o, stopCondition);
	}

	@Override
	public ETopoElement getLevel() {
		return this.level;
	}

	// public void moveChild(Child child, AbstractElement<Child> to) {
	// this.getConnectionManager().disconnect(child);
	// to.getConnectionManager().connect(child);
	// ((AbstractElement<?>) child).parent = to;
	// }

	abstract protected void treatNotification(IPullNotification notification);

	abstract protected void treatNotification(IPushNotification notification);

	@Override
	public Aggregation aggregate() {
		LinkedList<Aggregation> aggs = new LinkedList<>();

		for (final Child child : getConnectionManager().getConnectedChildren()) {
			aggs.add(child.aggregate());
		}

		return Aggregation.aggregate(aggs);

		// final Iterator<IElement> ite = getChildren().iterator();
		// Iterable<Aggregation> it = new Iterable<Aggregation>() {
		//
		// @Override
		// public Iterator<Aggregation> iterator() {
		// return new Iterator<Aggregation>() {
		//
		// @Override
		// public boolean hasNext() {
		// return ite.hasNext();
		// }
		//
		// @Override
		// public Aggregation next() {
		// return ite.next().aggregate();
		// }
		//
		// @Override
		// public void remove() {
		// ite.remove();
		//
		// }
		//
		// };
		// }
		//
		// };
		// return Aggregation.aggregate(it);


	}
	@Override
	public void applyConstraints() {
		// TODO: stub = no constraints unless told otherwise
	}

	@Override
	public void checkManageTopology() {
		boolean ran = false;

		// propagate
		for (Child c : new LinkedList<>(getConnectionManager().getConnectedChildren())) {
			c.checkManageTopology();
		}

		for (IScheduler sched : getSchedulers()) {
			// take the min of schedulers
			if (!ran && sched.shouldRun()) {
				manageTopology();
				ran = true;
			}
		}
		// reset to take next min once action has been performed
		if (ran) {
			for (IScheduler sched : getSchedulers()) {
				sched.reset();
			}
		}
	}

	@Override
	public abstract void manageTopology();

	@Override
	public boolean hasChildren() {
		return this.getChildrenSize() > 0;
	}

	@Override
	public int getChildrenSize() {
		return connectionManager.getConnectedChildren().size();
	}

	@Override
	public int getId() {
		return this.id;
	}

	@Override
	public String toString() {
		return "" + this.getId();
	}

	// public Collection<IElement> getSiblings() {
	// return connectionManager.getParent().
	// }

	public ConnectionManager<Child> getConnectionManager() {
		return connectionManager;
	}

	protected ClockCachedObject<Aggregation> aggregate;

	public Aggregation getAggregate() {
		return aggregate.get();
	}

}
