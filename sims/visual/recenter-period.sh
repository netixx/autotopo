#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

RUN="$DIR/../viewer.sh"

AT_CONFIG_TPL="$DIR/recenter_config.properties.tpl"

AT_CONFIG_NAME_TPL="at_recenter_period_%%i%%.properties"

VIEW_CONFIG_TPL="$DIR/../scenarios/visual-tests/large-10.properties.tpl"

VIEW_CONFIG_NAME_TPL="view_recenter_period_%%i%%.properties"

SCENARIO="$DIR/../scenarios/visual-tests/large-10.xprj"

OUTPUT="$DIR/output"
mkdir "$OUTPUT"

makeAtConfig() {
sed \
-e s/%%enabled%%/"$2"/g \
-e s/%%period%%/"$3"/g \
-e s/%%bias%%/"$4"/g \
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

defaultRecenterBias="0"
#defaultRecenterPeriod="0"

#testedRecenterBias="0 1 3 5"
#testedRecenterPeriod="0 1 3 5 10 20"
#testedRecenterPeriod="0 5"
testedRecenterPeriod="10 1 0"
ya=220
y=20


def_at_config="$DIR/$(echo "$AT_CONFIG_NAME_TPL" | sed "s/%%i%%/default/g")"
makeAtConfig "$def_at_config" "false" "0" "0"
def_view_config="$DIR/$(echo "$VIEW_CONFIG_NAME_TPL" | sed "s/%%i%%/default/g")"
makeViewerConfig "$def_view_config" "$y"
runOne "-a $def_at_config" "-e $def_view_config"

for recenterperiod in ${testedRecenterPeriod}
do
    y=$(($y+$ya))
    at_config="$DIR/$(echo "$AT_CONFIG_NAME_TPL" | sed "s/%%i%%/$recenterperiod/g")"
    view_config="$DIR/$(echo "$VIEW_CONFIG_NAME_TPL" | sed "s/%%i%%/$recenterperiod/g")"
    makeAtConfig "$at_config" "true" "$recenterperiod" "$defaultRecenterBias"
    makeViewerConfig "$view_config" "$y"
    runOne "-a $at_config" "-e $view_config"
#    rm "$config"
done

#while true
#do
#read blob
#if [[ "$blob" == "e" ]]
#then
#exit 0
#fi

#done
