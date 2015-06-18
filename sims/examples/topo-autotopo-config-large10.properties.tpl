#scheduler.agents.events.number=-1
#scheduler.roadsegments.time.interval=2

####
agent.scope.number.max=20
agent.scope.number.threshold=-1
agent.connections.distance.max=70
agent.connections.distance.threshold=-5

##### Traffic jams
roadsegments.trafficjam.enabled=false

##### Topology optimizations
optimize.agent.recenter-leader.enabled=%%recenterenabled%%
optimize.agent.recenter-leader.period=%%recenterperiod%%
optimize.agent.recenter-leader.bias=%%recenterbias%%

optimize.roadsegment.speed-clustering.enabled=%%speedclusteringenabled%%
optimize.roadsegment.speed-clustering.factor=%%speedclusteringfact%%

#use 0 to deactivate
optimize.anticipation.position.seconds=%%posanticipation%%

#### RoadSegments instances
roadsegments.instances.start=1
roadsegments.instances.1.next=2
roadsegments.instances.1.end=1000
roadsegments.instances.2.next=3
roadsegments.instances.2.end=9000
roadsegments.instances.3.next=0

statistics.roadsegments.2.log=true
