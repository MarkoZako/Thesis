#!/usr/bin/tcsh

setenv TRACE_DIR /home/students/cs/benchmarks/champsim/
set binary=$1
set n_warm=$2
set n_sim=$3
set trace=$4
set optionlist=`echo $5`
set psolist=`echo $6`
set masklist=`echo $7`
#echo $optionlist
@ track = -2

foreach option ($optionlist)
foreach pso ($psolist)
foreach mask ($masklist)

set rdir=results-$binary-$option-$pso-$mask-$track
mkdir -p results/$rdir
set outp=results/$rdir/$trace.out

echo $outp

bin/$binary -warmup_instructions ${n_warm}000000 -simulation_instructions ${n_sim}000000 -r $option -psel_width $pso -psel_mask $mask -track_set $track -traces ${TRACE_DIR}${trace}.trace.gz >& $outp

end
end
end
