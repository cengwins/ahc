set node_numbers=10 20 30 40
set prob_coefs=2 4 6 8
set repeat_count=100
for %%a in (%node_numbers%) do (
    for %%b in (%prob_coefs%) do (
        for /L %%c in (1,1,%repeat_count%) do (
            python MonteCarloExperiment.py %%a %%b %%c
        )
    )
)


