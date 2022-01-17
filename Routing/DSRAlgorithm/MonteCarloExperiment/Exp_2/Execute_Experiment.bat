set node_numbers=10
set route_lengths=2 4 6 8
set repeat_count=100
for %%a in (%node_numbers%) do (
    for %%b in (%route_lengths%) do (
        for /L %%c in (1,1,%repeat_count%) do (
            python MonteCarloExperiment.py %%a %%b %%c
        )
    )
)


