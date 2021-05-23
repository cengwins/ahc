#!/bin/bash

set -e

run_sim_ds() {
    python3 ../cli.py djikstra-scholten 100 100 --run_until_termination --passiveness_death_thresh 3000 --hard_stop_nodes --hard_stop_min_tick 50 --hard_stop_max_tick 300 --node_package_process_per_tick 3 --node_initial_activeness_prob .5 --node_activeness_communication_prob .5 --wait_ticks_after_termination 200 --only_root_alive_initially --no_realtime_plot "${1}" "${2}" > "DS_${1}_${2}_run-${3}.out" <<< "\n"
}

run_sim_sf() {
    python3 ../cli.py shavit-francez 100 100 --run_until_termination --passiveness_death_thresh 3000 --hard_stop_nodes --hard_stop_min_tick 50 --hard_stop_max_tick 300 --node_package_process_per_tick 3 --node_initial_activeness_prob .5 --node_activeness_communication_prob .5 --wait_ticks_after_termination 200 --only_root_alive_initially --no_realtime_plot "${1}" "${2}" > "SF_${1}_${2}_run-${3}.out" <<< "\n"
}

for i in {1..10}; do
    run_sim_ds "grid" "3" "${i}"
    run_sim_ds "grid" "4" "${i}"
    run_sim_ds "grid" "5" "${i}"
    run_sim_ds "grid" "6" "${i}"
    run_sim_ds "grid" "7" "${i}"
    run_sim_ds "grid" "8" "${i}"
    run_sim_ds "grid" "9" "${i}"
    run_sim_ds "grid" "10" "${i}"
    run_sim_sf "grid" "3" "${i}"
    run_sim_sf "grid" "4" "${i}"
    run_sim_sf "grid" "5" "${i}"
    run_sim_sf "grid" "6" "${i}"
    run_sim_sf "grid" "7" "${i}"
    run_sim_sf "grid" "8" "${i}"
    run_sim_sf "grid" "9" "${i}"
    run_sim_sf "grid" "10" "${i}"
done

for i in {1..10}; do
    run_sim_ds "star" "4" "${i}"
    run_sim_ds "star" "9" "${i}"
    run_sim_ds "star" "19" "${i}"
    run_sim_ds "star" "29" "${i}"
    run_sim_ds "star" "39" "${i}"
    run_sim_ds "star" "49" "${i}"
    run_sim_ds "star" "59" "${i}"
    run_sim_sf "star" "4" "${i}"
    run_sim_sf "star" "9" "${i}"
    run_sim_sf "star" "19" "${i}"
    run_sim_sf "star" "29" "${i}"
    run_sim_sf "star" "39" "${i}"
    run_sim_sf "star" "49" "${i}"
    run_sim_sf "star" "59" "${i}"
done

for i in {1..10}; do
    run_sim_ds "erg" "5" "${i}"
    run_sim_ds "erg" "10" "${i}"
    run_sim_ds "erg" "15" "${i}"
    run_sim_ds "erg" "20" "${i}"
    run_sim_ds "erg" "25" "${i}"
    run_sim_ds "erg" "30" "${i}"
    run_sim_ds "erg" "35" "${i}"
    run_sim_ds "erg" "40" "${i}"
    run_sim_ds "erg" "45" "${i}"
    run_sim_ds "erg" "50" "${i}"
    run_sim_sf "erg" "5" "${i}"
    run_sim_sf "erg" "10" "${i}"
    run_sim_sf "erg" "15" "${i}"
    run_sim_sf "erg" "20" "${i}"
    run_sim_sf "erg" "25" "${i}"
    run_sim_sf "erg" "30" "${i}"
    run_sim_sf "erg" "35" "${i}"
    run_sim_sf "erg" "40" "${i}"
    run_sim_sf "erg" "45" "${i}"
    run_sim_sf "erg" "50" "${i}"
done