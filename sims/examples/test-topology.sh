#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

RUN_SIM="$DIR/core.sh"

CONFIG_FILE="topo-autotopo-config.properties"
CONFIG_TPLS="topo-autotopo-config.properties.tpl"
 #topo-autotopo-config-large10.properties.tpl"

RUN="$DIR/run.sh"

SCENARIOS_DIR="$DIR/scenarios/batch-tests"

if [[ -z $1 ]]
then
OUTPUT_DIR="$DIR/output"
else
OUTPUT_DIR="$1"
fi

REPS_FILE="$DIR/repeats"

RECORD_RESULT="$DIR/makeResults.py"

makeConfig() {
sed \
-e s/%%recenterenabled%%/"$2"/g \
-e s/%%recenterperiod%%/"$3"/g \
-e s/%%recenterbias%%/"$4"/g \
-e s/%%speedclusteringenabled%%/"$5"/g \
-e s/%%speedclusteringfact%%/"$6"/g \
-e s/%%posanticipation%%/"$7"/g \
"$config_tpl" > "$1"
}

jobs="2"

database="$DIR/sims.db"
scenarios="$SCENARIOS_DIR/large-10.xprj $SCENARIOS_DIR/speed-diff.xprj"

defaultRecenterEnabled="false"
defaultRecenterPeriod="0"
defaultRecenterBias="0"
defaultSpeedClusteringEnabled="false"
defaultSpeedClusteringFact="0"
defaultPosAnticipation="0"


testedRecenterPeriod=""
testedRecenterBias=""
testedSpeedClusteringFacts=""
testedAnticipations=""

testedRecenterPeriod="0 1 5 10"
testedRecenterBias="0 0.1 1 5"
testedSpeedClusteringFacts="0.0001 0.001 0.01 0.05 0.1"
#testedAnticipations=""

repeat="1 2 3 4 5 6 7 8 9 10"
#repeat="1 2 3 4 5 6"


n=0

echo -n "" > "$REPS_FILE"

# create dir or clean existing dir
mkdir "$OUTPUT_DIR" || rm -rf "$OUTPUT_DIR"/*

queueSim() {
    root_dir="$OUTPUT_DIR/$n"
    mkdir "$root_dir"
    conf="$root_dir/$CONFIG_FILE"
    makeConfig "$conf" "$@"

    echo "$root_dir $conf $scenario $RUN_SIM $RECORD_RESULT $database" >> "$REPS_FILE"
    n=$((n+1))
}


echo "Queueing sims"
for config_tpl in ${CONFIG_TPLS}
do
for scenario in ${scenarios}
do

### prepare sim files
for rep in ${repeat}
do

queueSim "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation"

for recenterperiod in ${testedRecenterPeriod}
do
        queueSim "true" "$recenterperiod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation"
done

for recenterbias in ${testedRecenterBias}
do
        queueSim "true" "$defaultRecenterPeriod" "$recenterbias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation"
done

for clustfact in ${testedSpeedClusteringFacts}
do
        queueSim "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "true" "$clustfact" "$defaultPosAnticipation"
done

#topology related tests
for anticipation in ${testedAnticipations}
do
        queueSim "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$anticipation"
done

done
done
done

#### run the sims
export TIMEFORMAT="$n simulations done in : %E s"

echo "Running $n sims with $jobs jobs.... "

time {
parallel --bar --colsep ' ' -j "$jobs" -a "$REPS_FILE" "$RUN" {} {} {} {} {}
}


### clean
echo -n "Cleaning... "
rm "$REPS_FILE"


echo "Done"
