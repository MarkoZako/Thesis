Compile example:
./build_champsim.sh perceptron next_line next_line srripstatsmore 1; cp bin/champsim bin/perceptron-next_line-next_line-srripstatsmore-1core-16way

Always compile in the simulators home directory First argument "perceptron" is
the branch predictor, next argument "next_line" is the L2 prefetcher, third
argument "next_line" is the LLC prefetcher and last argument "srripstatsmore"
is the LLC cache replacement policy. The last argument, "1", is the number of
cores.

The available options for each argument are the files in the relative folders,
"branch", "prefetcher" and "replacement", without their extension. For
example change the compile and run with the SRRIP policy, which is implemented
in file replacement/srrip.llc_repl, you need to change
the 4th argument to "srrip".

The second part of the compile command just copies the file binary to a more
self-expanatory filename because I had to run with difference cache
associativities, you can ommit and just use the produce file which in the
above example will be "perceptron-next_line-next_line-srripstatsmore-1core"

For replacement the following files are explained:
drrip.llc_repl is currently set to DRRIP (original, damaged). To change to
DRRIP_3 you need to edit the file and change line 7, to: #define BIP_MAX 0. To
change to DRRIP_V2 you need to change line 85, to: int V2 = 1. BE AWARE that
the DRRIP is set to run the long output file. To disable the long output you
need to comment line 83, starts with "cout << "BA: " << blockAddress"

srrip.llc_repl is set to run normal SRRIP 0-2-0-2

srripwbpass.llc_repl is set to run SRRIP 0-2-2-2

srripstatsmore.llc_repl is set to run SRRIP191. To run SRRIP191_BIP32 you need
to change line 26, to: #define BIP_MAX 32. To run the new SRRIP191_PID you
need to change the line 11, to #define PID 1. To run SRRIP_D2 you need to
change line 3521, to int D22 = 1;

----------------------------------------------
Run examples:
Single core:
/home/marios/mysims/champsim/bin/perceptron-next_line-next_line-srripstatsmore-1core-16way
-warmup_instructions 100000000  -simulation_instructions 500000000 -traces
Roms.trace.gz

Four core:
/home/marios/mysims/champsim/bin/perceptron-next_line-next_line-srripstatsmore-1core-16way
-warmup_instructions 100000000  -simulation_instructions 500000000
Fotonik3d.trace.gz Omnetpp.trace.gz Parest.trace.gz Roms.trace.gz

