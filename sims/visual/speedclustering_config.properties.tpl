agent.connections.distance.max=150
agent.connections.distance.threshold=-5

#run topology management every 0.5s
scheduler.agents.time.interval=0.5

scheduler.agents.events.number=-1
scheduler.roadsegments.time.interval=3

#run topo management every 10 events (connect/disconnect)
scheduler.roadsegments.events.number=10
scheduler.roads.time.interval=30
scheduler.roads.events.number=-1


optimize.roadsegment.speed-clustering.enabled=%%enabled%%
optimize.roadsegment.speed-clustering.factor=%%factor%%


decoration.scope.hue.step=51f