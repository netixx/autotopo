# autotopo
AutoTopo

This project is a java implementation of an inter-vehicular network architecture.

# Maven

This project is built with maven.

## Movsim integration

At this point, it is capable of interfacing with a modified version of the Movsim simulator, available at [https://github.com/netixx/movsim/tree/autotopo](https://github.com/netixx/movsim/tree/autotopo). It should be bundled with Movsim to work.

It is imported as a dependency in movsim.

Typical compilation (see makeMovsimJars.sh, which assumes the movsim project is located at the same level as autotopo) :
```
# in autotopo
mvn install
# in Movsim
mvn package
```

# sims directory

The sims directory contains useful files to perform simulations.

The example dir contains premade examples.

Python files are support files uses to gather, store and plot results. makeResults.py contains example usage of those files.

The other shell scripts are used to start simulations and java executables.
