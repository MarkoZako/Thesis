#!/usr/bin/tcsh

setenv TRACE_DIR /home/students/cs/benchmarks/champsim/
set binary=$1
set n_warm=$2
set n_sim=$3
set trace=$4
set outname=$5
set rdir=results-$binary-$outname
set outp=$rdir/$trace.out

mkdir -p $rdir

bin/$binary -warmup_instructions ${n_warm}000000 -simulation_instructions ${n_sim}000000 -traces ${TRACE_DIR}${trace}.trace.gz >& $outp &
