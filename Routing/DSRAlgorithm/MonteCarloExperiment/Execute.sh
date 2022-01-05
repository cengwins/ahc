node_numbers="10 20 30 40"
prob_coefs="2 4 6 8"
repeat_count=100
for node_number in $node_numbers; do
  for prob_coef in $prob_coefs; do
    for i in $(seq 1 $repeat_count); do
      python3 MonteCarloExperiment.py $node_number $prob_coef $i
    done
  done
done

