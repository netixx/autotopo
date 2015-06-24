#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

AUTOTOPO_DIR="$DIR/../"
MAVEN_INSTALL="mvn -Dmaven.test.skip=true --quiet clean install"

EXEC_DIR="$DIR/execs"

MOVSIM_CORE_EXEC="movsim-core.jar"
MOVSIM_VIEWER_EXEC="movsim-viewer.jar"

MOVSIM_LOC="$DIR/../../movsim"

MOVSIM_CORE="$MOVSIM_LOC/core"
MOVSIM_VIEWER="$MOVSIM_LOC/viewer"

MOVSIM_CORE_JAR="$MOVSIM_CORE/target/MovsimCore-1.6.0-SNAPSHOT-jar-with-dependencies.jar" 
MOVSIM_VIEWER_JAR="$MOVSIM_VIEWER/target/MovsimViewer-1.6.0-SNAPSHOT-jar-with-dependencies.jar" 

MAVEN_PACKAGE="mvn -Dmaven.test.skip=true --quiet clean package"

function getJar() {
#cd "$1"
#echo "Packaging $1..."
#${MAVEN_PACKAGE}
#echo "Done"
dest="$EXEC_DIR/$3"
cp "$2" "$dest"
echo "Copied $2 to $dest"
}

function packageMovsim() {
echo -n "Packaging Movsim...  "
cd "$MOVSIM_LOC"
${MAVEN_PACKAGE}
echo "Done"
}

echo -n "Installing Autotopo...  "
cd "$AUTOTOPO_DIR"
${MAVEN_INSTALL}
echo "Done"

packageMovsim
getJar "$MOVSIM_CORE" "$MOVSIM_CORE_JAR" "$MOVSIM_CORE_EXEC"
getJar "$MOVSIM_VIEWER" "$MOVSIM_VIEWER_JAR" "$MOVSIM_VIEWER_EXEC"

echo "Done"

cd "$DIR"
