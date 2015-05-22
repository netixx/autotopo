scheduler.agents.events.number=-1
scheduler.roadsegments.time.interval=2

####
agent.scope.number.max=20
agent.scope.number.threshold=-1
agent.connections.distance.max=70
agent.connections.distance.threshold=-5


##### Traffic jams
roadsegments.trafficjam.enabled=false

##### Topology optimizations
optimize.agent.recenter-leader.enabled=%%enabled%%
optimize.agent.recenter-leader.period=%%period%%
optimize.agent.recenter-leader.bias=%%bias%%

optimize.roadsegment.speed-clustering.enabled=false

#use 0 to deactivate
optimize.anticipation.position.seconds=0


speed.limit.default=15
