from argparse import ArgumentParser
from simulator_sf import run_shavit_francez_simulation
from simulator_ds import run_dijkstra_scholten_simulation

algorithm_handlers = {
    "djikstra-scholten": run_dijkstra_scholten_simulation,
    "shavit-francez": run_shavit_francez_simulation,
}

    ## IMPORTANT NOTE
    # possibe evaluation metrics
    # num(control packages) / num(total packages) => 
    # tick(algo done) - tick(termination) => ne kadar erken detect etti

parser = ArgumentParser()
parser.add_argument("algorithm", type=str, choices=list(algorithm_handlers.keys()))
parser.add_argument("simulation_ticks", type=int)
parser.add_argument("ms_per_tick", type=int)
parser.add_argument("--node_min_activeness_after_receive", type=int, default=3) # paket aldiktan sonra min bu kadar aktif kal
parser.add_argument("--node_max_activeness_after_receive", type=int, default=5) # paket aldiktan sonra max bu kadar aktif kal
parser.add_argument("--node_activeness_communication_prob", type=float, default=0.5) # alive iken baska nodelara paket gonderme olasiligi
parser.add_argument("--node_initial_activeness_prob", type=float, default=0.5)
parser.add_argument("--node_package_process_per_tick", type=int, default=5)

parser.add_argument("--only_root_alive_initially", action="store_true", default=False)

parser.add_argument("--run_until_termination", action="store_true", default=False)
parser.add_argument("--exit_on_termination", action="store_true", default=False)
parser.add_argument("--wait_ticks_after_termination", type=int, default=0)

parser.add_argument("--passiveness_death_thresh", type=int, default=20)
parser.add_argument("--hard_stop_nodes", action="store_true", default=False)
parser.add_argument("--hard_stop_min_tick", type=int, default=50)
parser.add_argument("--hard_stop_max_tick", type=int, default=300)
parser.add_argument("--hard_stop_prob", type=float, default=0.5)

parser.add_argument("--no_realtime_plot", action="store_true", default=False)
parser.add_argument("--save_tick_plots", action="store_true", default=False)
parser.add_argument("--tick_plots_save_dir", type=str, default="simdump")
parser.add_argument("--generate_gif", action="store_true", default=False)

sp = parser.add_subparsers()

erg_parser = sp.add_parser("erg")
erg_parser.add_argument("node_count", type=int)
erg_parser.add_argument("--node_connectivity", type=float, default=0.5)
erg_parser.set_defaults(network_type="erg")

grid_parser = sp.add_parser("grid")
grid_parser.add_argument("node_count_on_edge", type=int)
grid_parser.set_defaults(network_type="grid")

star_parser = sp.add_parser("star")
star_parser.add_argument("slave_count", type=int)
star_parser.add_argument("--master_is_root", type=bool, default=True)
star_parser.set_defaults(network_type="star")

if __name__ == "__main__":
    args = parser.parse_args()
    print(f"[+] Network type: {args.network_type}")

    if args.generate_gif:
        args.save_tick_plots = True

    algorithm_handlers[args.algorithm](args)