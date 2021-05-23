# Wave algorithm

## why echo?
- works for cyclic graphs, tree algo only works in acyclic ones.

# evaluation metrics# possibe evaluation metrics

- control packet drop in SF is not a big deal, there are N waves. in DS, just one controller exist (initiator).
- detection lateness in SF > DS (smaller is better)
- detection success SF > DS (bigger is better)

- CPR : control packet ratio = num(control packages) / num(total packages)
- DL : detection latency = tick(algo done) - tick(termination) => ne kadar erken detect etti
- WPR : wave packet ratio = num(wave packages) / num(total packages)
- CPPN : control packets per node = num(control packages) / num(nodes)
- WPPN : wave packets per node = num(wave packages) / num(nodes)

- ALSO, these metrics can be analyzed dependent on the network structure!!