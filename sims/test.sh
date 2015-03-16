#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

RESULT="$DIR/result"

RUN="$DIR/core.sh"

CONFIG="autotopo-config.properties"
CONFIG_TPL="autotopo-config.properties.tpl"


if [[ -z $1 ]]
then
OUTPUT_DIR="output"
else
OUTPUT_DIR="$1"
fi

makeRun() {
${RUN} -o "$2" -f "$1"
#2>"$RESULT"
}

makeConfig() {
sed -e s/%%speedfact%%/"$1"/g -e s/%%jamfactor%%/"$2"/g -e s/%%distance%%/"$3"/g -e s/%%anticipation%%/"$4"/g -e s/%%defspeed%%/"$5"/g "$CONFIG_TPL" > ${CONFIG}
}

repeat="1 2 3 4 5"

defaultSpeedFact="0.8"
defaultJamFactor="0.1"
defaultDistance="1000"
defaultAnticipation="1"
defaultDefaultSpeed="15"

#testedSpeedFacts="1.4 1.2 1.0 0.9 0.85 0.8 0.75 0.7 0.6"
#testedJamFactors="0.1 0.15 0.2 0.3"
#testedDistances="0 500 1000 2000 3000 5000"
#testedAnticipations="0 0.5 0.75 1 1.5 2"

testedSpeedFacts=""
testedJamFactors=""
testedDistances=""
testedAnticipations="0 0.5 0.75 1 1.5 2"


#echo "#$FORMAT" > $OUTPUT_FILE
mkdir "$OUTPUT_DIR"
scenario="scenarios/laneclosure-no-speed-limits-long/laneclosure.xprj"

#OUTPUT_FILE="sim.csv"
#FORMAT="Speedfact;TravelTime(s);FTravelDistance(km);FuelLiters(l);PlusAcc;MinusAcc"
RECORD_RESULT="$DIR/makeResults.py write --parameters \"$CONFIG\" --output-dir \"$OUTPUT_DIR\" --scenario $scenario"



makeSim() {
	echo "Making simulation with speed=$1, jamfactor=$2, distance=$3, anticipation=$4"
	makeConfig "$@"
	makeRun "$scenario" "$OUTPUT_DIR"
	eval "$RECORD_RESULT"
	rm "$OUTPUT_DIR/*.csv"
}

for rep in ${repeat}
do

for speedFact in ${testedSpeedFacts}
do
		makeSim "$speedFact" "$defaultJamFactor" "$defaultDistance" "$defaultAnticipation" "$defaultDefaultSpeed"
done

for jamFactor in ${testedJamFactors}
do
		makeSim "$defaultSpeedFact" "$jamFactor" "$defaultDistance" "$defaultAnticipation" "$defaultDefaultSpeed"
done

for distance in ${testedDistances}
do
		makeSim "$defaultSpeedFact" "$defaultJamFactor" "$distance" "$defaultAnticipation" "$defaultDefaultSpeed"
done

for anticipation in ${testedAnticipations}
do
		makeSim "$defaultSpeedFact" "$defaultJamFactor" "$defaultDistance" "$anticipation" "$defaultDefaultSpeed"
done

done
