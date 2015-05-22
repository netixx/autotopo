#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

RUN="$DIR/../viewer.sh"

AT_CONFIG_TPL="$DIR/speedclustering_config.properties.tpl"

AT_CONFIG_NAME_TPL="at_speed_clustering_%%i%%.properties"

VIEW_CONFIG_TPL="$DIR/../scenarios/visual-tests/speed-diff.properties.tpl"

VIEW_CONFIG_NAME_TPL="view_speed_clustering_%%i%%.properties"

#SCENARIO="$DIR/../scenarios/visual-tests/speed-diff.xprj"
SCENARIO="$DIR/../scenarios/visual-tests/speed-diff-extreme.xprj"

OUTPUT="$DIR/output"
mkdir "$OUTPUT"

makeAtConfig() {
sed \
-e s/%%enabled%%/"$2"/g \
-e s/%%factor%%/"$3"/g \
"$AT_CONFIG_TPL" > "$1"
}

makeViewerConfig() {
sed \
-e s/%%yPos%%/"$2"/g \
"$VIEW_CONFIG_TPL" > "$1"
}


runOne() {
    eval ${RUN} -f "$SCENARIO" "$1" "$2" -o "$OUTPUT" > /dev/null &
}

testedSpeedFact="0.5 0.2 0"

ya=200
y=20

def_at_config="$DIR/$(echo "$AT_CONFIG_NAME_TPL" | sed "s/%%i%%/default/g")"
makeAtConfig "$def_at_config" "false" "0"
def_view_config="$DIR/$(echo "$VIEW_CONFIG_NAME_TPL" | sed "s/%%i%%/default/g")"
makeViewerConfig "$def_view_config" "$y"
runOne "-a $def_at_config" "-e $def_view_config"


for speedfact in ${testedSpeedFact}
do
    y=$(($y+$ya))
    at_config="$DIR/$(echo "$AT_CONFIG_NAME_TPL" | sed "s/%%i%%/$speedfact/g")"
    view_config="$DIR/$(echo "$VIEW_CONFIG_NAME_TPL" | sed "s/%%i%%/$speedfact/g")"
    makeAtConfig "$at_config" "true" "$speedfact"
    makeViewerConfig "$view_config" "$y"
    runOne "-a $at_config" "-e $view_config"
#    rm "$at_config" "$view_config"
done

#while true
#do
#read blob
#if [[ "$blob" == "e" ]]
#then
#exit 0
#fi

#done