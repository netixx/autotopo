#!/bin/bash

output_dir="$1"
config="$2"
scenario="$3"

run="$4"
record="$5"
db="$6"

makeRun() {
${run} -f "$1" -o "$2" -a "$3"
#exec ${RUN} -o "$2" -f "$1"
}


makeSim() {
#    cd "$root_dir"
	makeRun "$scenario" "$output_dir" "$config"
	python ${record} write --database ${db} --parameters ${config} --output-dir ${output_dir} --scenario ${scenario}
	#&& rm "$output_dir"/*.csv
}

echo -e "\nRunning sim: scenario $scenario, config is \n>>>`cat "$config"`\n<<<\n"
makeSim
cp "$scenario" "$output_dir/"
