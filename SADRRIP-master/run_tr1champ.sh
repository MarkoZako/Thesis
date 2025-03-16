#!/usr/bin/tcsh

setenv TRACE_DIR /home/students/cs/benchmarks/champsim/
set binary=$1
set n_warm=$2
set n_sim=$3
set trace=$4
set optionlist=`echo $5`
set psolist=`echo $6`
set masklist=`echo $7`
set dsalgolist=`echo $8`
set windowlist=`echo $9`
set srlist=`echo $10`
set brlist=`echo $11`
set boolist=`echo $12`
set hitlist=`echo $13`
set demlist=`echo $14`
#echo $optionlist

foreach option ($optionlist)
foreach pso ($psolist)
foreach mask ($masklist)
foreach dsalgo ($dsalgolist)
foreach window ($windowlist)
foreach srt ($srlist)
foreach brt ($brlist)
foreach boost ($boolist)
foreach hit ($hitlist)
foreach dem ($demlist)

set rdir=results-$binary-$option-$pso-$mask-$dsalgo-$window-$srt-$brt-$boost-$hit-$dem-t3
mkdir -p results/$rdir
set outp=results/$rdir/$trace.out

#echo $outp

./bin/$binary -warmup_instructions ${n_warm}000000 -simulation_instructions ${n_sim}000000 -r $option -psel_width $pso -psel_mask $mask -hit_mask $hit -dsalgo $dsalgo -window_size $window -sr_thr $srt -br_thr $brt -boost $boost -demote_mask $dem -track_set -3 -traces ${TRACE_DIR}${trace}.trace.gz >& $outp

end
end
end
end
end
end
end
end
end
end
