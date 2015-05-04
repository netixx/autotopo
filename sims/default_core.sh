#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

java -Djava.awt.headless=true -jar "$DIR/execs/movsim-core.jar" "$@"
