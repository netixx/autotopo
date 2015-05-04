#!/bin/bash

root_dir="$1"
output_dir="$2"
config="$3"
scenario="$4"

run="$5"
record="$6"
db="$7"

makeRun() {
${run} -f "$1" -o "$2" -a "$3"
#exec ${RUN} -o "$2" -f "$1"
}


makeSim() {
#    cd "$root_dir"
	makeRun "$scenario" "$output_dir" "$config"
	eval ${record} --database ${db} write --parameters ${config} --output-dir ${output_dir} --scenario ${scenario} && rm "$output_dir"/*.csv
}

echo -e "Running sim in $root_dir, scenario $scenario, config is \n>>>`cat "$config"`\n<<<\n"
makeSim
