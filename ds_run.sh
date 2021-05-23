#!/bin/bash

set -e

run_sim() {
    python3 ../cli.py djikstra-scholten 100 100 --run_until_termination --passiveness_death_thresh 3000 --hard_stop_nodes --hard_stop_min_tick 50 --hard_stop_max_tick 250 --node_package_process_per_tick 3 --node_initial_activeness_prob .5 --node_activeness_communication_prob .8 --wait_ticks_after_termination 50 --only_root_alive_initially --no_realtime_plot "${1}" "${2}" > "${1}_${2}_run-${3}.out" <<< "\n"
}

for i in {1..10}; do
    run_sim "grid" "3" "${i}"
    run_sim "grid" "4" "${i}"
    run_sim "grid" "5" "${i}"
    run_sim "grid" "6" "${i}"
    run_sim "grid" "7" "${i}"
    run_sim "grid" "8" "${i}"
    run_sim "grid" "9" "${i}"
    run_sim "grid" "10" "${i}"
done

for i in {1..10}; do
    run_sim "star" "4" "${i}"
    run_sim "star" "9" "${i}"
    run_sim "star" "19" "${i}"
    run_sim "star" "29" "${i}"
    run_sim "star" "39" "${i}"
    run_sim "star" "49" "${i}"
    run_sim "star" "59" "${i}"
done

for i in {1..10}; do
    run_sim "erg" "5" "${i}"
    run_sim "erg" "10" "${i}"
    run_sim "erg" "15" "${i}"
    run_sim "erg" "20" "${i}"
    run_sim "erg" "25" "${i}"
    run_sim "erg" "30" "${i}"
    run_sim "erg" "35" "${i}"
    run_sim "erg" "40" "${i}"
    run_sim "erg" "45" "${i}"
    run_sim "erg" "50" "${i}"
done