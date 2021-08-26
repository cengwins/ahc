from timeit import default_timer as timer
import pickle
print(timer())

graph, count, completion, route = pickle.load(open("Results/39128.153763338.exp", "rb"))
print(graph)
print(count)
print(completion)
print(route)