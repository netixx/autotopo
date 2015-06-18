#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

RUN_SIM="$DIR/core.sh"

CONFIG_FILE="autotopo-config.properties"
CONFIG_TPL="autotopo-config.properties.tpl"

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
-e s/%%tjenabled%%/"$2"/g \
-e s/%%tjjamfactor%%/"$3"/g \
-e s/%%tjspeedfact%%/"$4"/g \
-e s/%%tjdistance%%/"$5"/g \
-e s/%%recenterenabled%%/"$6"/g \
-e s/%%recenterperiod%%/"$7"/g \
-e s/%%recenterbias%%/"$8"/g \
-e s/%%speedclusteringenabled%%/"$9"/g \
-e s/%%speedclusteringfact%%/"${10}"/g \
-e s/%%posanticipation%%/"${11}"/g \
-e s/%%defspeed%%/"${12}"/g \
"$CONFIG_TPL" > "$1"
}

jobs="2"

database="$DIR/sims.db"
scenarios="$SCENARIOS_DIR/large-10.xprj $SCENARIOS_DIR/speed-diff.xprj"

defaultTJEnabled="false"
defaultTJJamFactor="0.1"
defaultTJSpeedFact="0.8"
defaultTJDistance="1000"
defaultRecenterEnabled="false"
defaultRecenterPeriod="3"
defaultRecenterBias="2"
defaultSpeedClusteringEnabled="false"
defaultSpeedClusteringFact="0"
defaultPosAnticipation="0"
defaultDefSpeed="25"


testedSpeedFacts=""
testedJamFactors=""
testedDistances=""
testedAnticipations=""
testedRecenterPeriod=""
testedRecenterBias=""
testedSpeedClusteringFacts=""


#testedSpeedFacts="1.4 1.2 1.0 0.9 0.85 0.8 0.75 0.7 0.6"
#testedJamFactors="0.1 0.15 0.2 0.3"
#testedDistances="0 500 1000 2000 3000 5000"
#testedAnticipations="0 0.5 0.75 1 1.5 2 4"
#testedRecenterPeriod="0 1 3 5"
#testedRecenterBias="0 1 3 5"
#testedSpeedClusteringFacts="0.01 0.05 0.1 0.5"
testedSpeedClusteringFacts="1"

repeat="1 2 3 4 5 6 7 8 9 10"


n=0

echo -n "" > "$REPS_FILE"

# create dir or clean existing dir
mkdir "$OUTPUT_DIR" || rm -rf "$OUTPUT_DIR"/*

queueSim() {
    root_dir="$OUTPUT_DIR/$n"
    mkdir "$root_dir"
    conf="$root_dir/$CONFIG_FILE"
    makeConfig "$conf" "$@"
    echo "$root_dir $root_dir $conf $scenario $RUN_SIM $RECORD_RESULT $database" >> "$REPS_FILE"
    n=$((n+1))
}


echo "Queueing sims"
for scenario in ${scenarios}
do

### prepare sim files
for rep in ${repeat}
do

# Jam related tests
for speedFact in ${testedSpeedFacts}
do
        queueSim "true" "$defaultTJJamFactor" "$speedFact" "$defaultTJDistance" "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

for jamFactor in ${testedJamFactors}
do
        queueSim "true" "$jamFactor" "$defaultTJSpeedFact" "$defaultTJDistance" "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

for distance in ${testedDistances}
do
        queueSim "true" "$defaultTJJamFactor" "$defaultTJSpeedFact" "$distance" "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

#topology related tests
for anticipation in ${testedAnticipations}
do
        queueSim "$defaultTJEnabled" "$defaultTJJamFactor" "$defaultTJSpeedFact" "$defaultTJDistance" "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$anticipation" "$defaultDefSpeed"
done

for recenterperiod in ${testedRecenterPeriod}
do
        queueSim "$defaultTJEnabled" "$defaultTJJamFactor" "$defaultTJSpeedFact" "$defaultTJDistance" "true" "$recenterperiod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

for recenterbias in ${testedRecenterBias}
do
        queueSim "$defaultTJEnabled" "$defaultTJJamFactor" "$defaultTJSpeedFact" "$defaultTJDistance" "true" "$defaultRecenterPeriod" "$recenterbias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

for clustfact in ${testedSpeedClusteringFacts}
do
        queueSim "$defaultTJEnabled" "$defaultTJJamFactor" "$defaultTJSpeedFact" "$defaultTJDistance" "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "true" "$clustfact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

done
done

#### run the sims

export TIMEFORMAT="$n simulations done in : %lU"

echo "Running $n sims with $jobs jobs.... "

time {
parallel --bar --colsep ' ' -j "$jobs" -a "$REPS_FILE" "$RUN" {} {} {} {} {} {}
}


### clean
echo -n "Cleaning... "
rm "$REPS_FILE"

echo "Done"
