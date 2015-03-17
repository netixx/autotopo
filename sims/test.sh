#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

RESULT="$DIR/result"

RUN="$DIR/core.sh"

CONFIG="autotopo-config.properties"
CONFIG_TPL="autotopo-config.properties.tpl"

#shopt -s extglob

if [[ -z $1 ]]
then
OUTPUT_DIR="output"
else
OUTPUT_DIR="$1"
fi

makeRun() {
${RUN} -o "$2" -f "$1"
#exec ${RUN} -o "$2" -f "$1"
#exit 0
#2>"$RESULT"
}

makeConfig() {
sed \
-e s/%%tjenabled%%/"$1"/g \
-e s/%%tjjamfactor%%/"$2"/g \
-e s/%%tjspeedfact%%/"$3"/g \
-e s/%%tjdistance%%/"$4"/g \
-e s/%%recenterenabled%%/"$5"/g \
-e s/%%recenterperiod%%/"$6"/g \
-e s/%%recenterbias%%/"$7"/g \
-e s/%%speedclusteringenabled%%/"$8"/g \
-e s/%%speedclusteringfact%%/"$9"/g \
-e s/%%posanticipation%%/"${10}"/g \
-e s/%%defspeed%%/"${11}"/g \
"$CONFIG_TPL" > ${CONFIG}
}

repeat="1 2 3 4 5 6"

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
defaultDefSpeed="15"

#testedSpeedFacts=""
#testedJamFactors=""
#testedDistances=""
#testedAnticipations="4 10"

testedSpeedFacts="1.4 1.2 1.0 0.9 0.85 0.8 0.75 0.7 0.6"
testedJamFactors="0.1 0.15 0.2 0.3"
testedDistances="0 500 1000 2000 3000 5000"
testedAnticipations="0 0.5 0.75 1 1.5 2 4"
testedRecenterPeriod="0 1 3 5"
testedRecenterBias="0 1 2 5 10"
testedSpeedClusteringFacts="0.01 0.1 0.5"

#echo "#$FORMAT" > $OUTPUT_FILE
mkdir "$OUTPUT_DIR"
scenario="scenarios/laneclosure-no-speed-limits-long/laneclosure.xprj"

#OUTPUT_FILE="sim.csv"
#FORMAT="Speedfact;TravelTime(s);FTravelDistance(km);FuelLiters(l);PlusAcc;MinusAcc"
RECORD_RESULT="$DIR/makeResults.py write --parameters \"$CONFIG\" --output-dir \"$OUTPUT_DIR\" --scenario $scenario"
n=0


makeSim() {
    n=$((n+1))
	echo "Making simulation with speed=$1, jamfactor=$2, distance=$3, anticipation=$4"
	makeConfig "$@"
	makeRun "$scenario" "$OUTPUT_DIR"
	eval "$RECORD_RESULT"
	rm "$OUTPUT_DIR"/*.csv
}

TIMEFORMAT="$n simulations done in : %lU"
time {

for rep in ${repeat}
do

echo "Repetition $rep"
# Jam related tests
for speedFact in ${testedSpeedFacts}
do
		makeSim "true" "$defaultTJJamFactor" "$speedFact" "$defaultTJDistance" "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

for jamFactor in ${testedJamFactors}
do
		makeSim "true" "$jamFactor" "$defaultTJSpeedFact" "$defaultTJDistance" "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

for distance in ${testedDistances}
do
		makeSim "true" "$defaultTJJamFactor" "$defaultTJSpeedFact" "$distance" "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

#topology related tests
for anticipation in ${testedAnticipations}
do
		makeSim "$defaultTJEnabled" "$defaultTJJamFactor" "$defaultTJSpeedFact" "$defaultTJDistance" "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$anticipation" "$defaultDefSpeed"
done

for recenterperiod in ${testedRecenterPeriod}
do
		makeSim "$defaultTJEnabled" "$defaultTJJamFactor" "$defaultTJSpeedFact" "$defaultTJDistance" "true" "$recenterperiod" "$defaultRecenterBias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

for recenterbias in ${testedRecenterBias}
do
		makeSim "$defaultTJEnabled" "$defaultTJJamFactor" "$defaultTJSpeedFact" "$defaultTJDistance" "true" "$defaultRecenterPeriod" "$recenterbias" "$defaultSpeedClusteringEnabled" "$defaultSpeedClusteringFact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

for clustfact in ${testedSpeedClusteringFacts}
do
		makeSim "$defaultTJEnabled" "$defaultTJJamFactor" "$defaultTJSpeedFact" "$defaultTJDistance" "$defaultRecenterEnabled" "$defaultRecenterPeriod" "$recenterbias" "true" "$clustfact" "$defaultPosAnticipation" "$defaultDefSpeed"
done

echo ""
done

}
