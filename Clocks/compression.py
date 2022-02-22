import math
import operator
import networkx as nx
import matplotlib.pyplot as plt
import threading
import numpy as np

mutex1 = threading.Lock()
mutex2 = threading.Lock()

def compareSizes(n, m, bits):
   
    AdjLst = (n * 32) + (m * 32)
    AdjMat = n * n 
    sizeEncode = n * (n - 1)
    sizeEncodeEdge = math.log(comb(n * (n - 1), m), 2)

    return [AdjLst, AdjMat, sizeEncode, sizeEncodeEdge]

def comb2(n):
    return n * (n - 1) / 2.0

def perm(n, k): 
    p = 1

    for i in range(n, (n-k), -1): 
        p = p * i

    return p 

def comb(n, k):
    comb = perm(n, k) // math.factorial(k)
    return comb

def H(i):
    return 1 + math.ceil( -1/2 + math.sqrt(1/4 + i))


def mynewtonana(f, x0, c, g, m, epsilon, max_iter):
    '''Approximate solution of f(x)=0 by Newton's method using analytical first derivative. '''

    # Input - f: the objection/cost function 
    #       - x0: initial approximation to a zero of f
    #       - c: current edge label, used for finding the derivate 
    #       - g: the integer used to represent the graph, use for overcoming an unexpected occurence
    #       - delta: tolerance for f(xn), f(xn) < delta
    #       - epsilon: one of the stopping criteria, the bound for |xn1 - xn| < epsilon
    #       - max_iter: maximum number of iterations
    # Output - xn; the Newton-Raphson approximation to the zero

    
    xn = x0
    for n in range(0, max_iter):
        if ( xn >= c):
            fxn = f(xn)

            if fxn == 0 : 
                #print(f"ending after {n} iterations fxn = 0 sending {xn}")
                return xn

            Dfxn = Jprime(xn, c) 
  
            if math.fabs(fxn) < epsilon: 
                #print(f"ending after {n} iterations fxn = {fxn} sending {xn}")
                return xn


            if Dfxn == 0:
                print('Zero derivative. No solution found.')
                return xn 
         
            xn1 = xn - f(xn)/Dfxn
            
            err = math.fabs(xn1 - xn)

            relerror = (2 * err) / (math.fabs(xn1) + epsilon)
            xn = xn1   

            if (relerror < epsilon ):
                #print(f"ending after {n} iterations relative error sending {xn}")
                return xn1

            # Solution to an unpredictable problem
            if (math.floor(xn) + 2 == g+1):
                return math.fabs(xn+1)
        else:
            xn = c

    return math.fabs(xn)




############################################### BOTH N AND M UNKNOWN #################################################################

def encode(graph):
    bi = {}
    i = 0 

    for k, v in graph.adjacency(): 
        for m in v: 
            u, v = int(k), int(m)
            i = (2 * u + (v - 1)*(v - 2)) if u < v else (2 * v + u * (u - 3) + 1)
            bi[int(i)] = 1

    return bi


def decode(enc): 
    graph = nx.DiGraph()

    for i in enc:
        bi = enc[i]
        if (i % 2) != 0:
            u = int(H(i))
            v = int(((i + 1) / 2) - comb2(u-1))
            graph.add_edge(u,v)
        else: 
            v = int(H(i))
            u = int((i/2) - comb2(v-1))
            graph.add_edge(u,v)

    return graph 

############################################### ONLY N KNOWN #################################################################

def encode_n(graph, n):
    bi = [0 for j in range(n * (n - 1) + 1)]

    def C(u, v, n):
        return (u / 2.0) * (2 * n - 1 - u) + v - n

    def F(u, v, n, a):
        return a if u < v else a + comb2(n)

    i = 0

    for k, v in graph.adjacency():
        for m in v:
            u, v = int(k), int(m)
            i = C(u, v, n) if u < v else C(v, u, n) + comb2(n)
            bi[int(i)] = 1

    return bi


def decode_n(enc, n):
    graph = nx.DiGraph()

    for i in range(1, len(enc)): 
        bi = enc[i]
        if bi: 
            j = i if i <= comb2(n) else i - comb2(n)
            t = n - (1.0 / 2)

            u = int(math.ceil(t - math.sqrt(t * t - 2 * j)))
            v = int(j + n + u * ((u + 1) / 2.0 - n))

            if i <= comb2(n): 
                graph.add_edge(u, v)
            else: 
                graph.add_edge(v, u)

    return graph


############################################### N AND M KNOWN #################################################################

class Link: 
    def __init__(self, u, v): 
        self.src = u
        self.dest = v
        self.num = (2 * u) + (v - 1) * (v - 2) if u < v else (2 * v) + u *(u - 3) + 1


def J(x, c, g):

    if g <= 1: 
        g = 1
    tot = 0 
    #cons = (1.0 / math.log10(g))

    for p in range(1, c + 1): 
        tot += math.log10((x-c)/(p * 1.0) + 1)
    
    #return math.fabs(cons*tot-1)
    # Alternatively
    result = tot - math.log10(g)

    return result


def Jprime(x, c): 
    tot = np.float64(0.0)
    ln = np.float64(1.0) / math.log(10)

    for p in range(0, c): 
        tot += np.float64(1.0) / np.float64(x-p)

    return tot*ln

# Check again doesn't seem to work
def J2(x,c,g ):
    return comb(int(x), int(c)) - g


def encode_nm(graph): 
    global mutex1
    mutex1.acquire()
    m = 0
    j = 1
    tot = 0 
    links = []

    # Number of links 
    for k, v in graph.adjacency(): 
        m += len(v)

    # Encode links 
    for k, v in graph.adjacency(): 
        for r in v: 
            u, v = int(k), int(r)
            links.append(Link(u, v))

    # Sort links by i_c
    links.sort(key=operator.attrgetter('num'))


    for l in links: 
        tot += int(math.pow(-1, m - j)) * (comb(l.num, j)-1)
        j += 1

    mutex1.release()
    return  m, tot


def decode_nm(g, m): 
    global mutex2
    mutex2.acquire()
    graph = nx.DiGraph()
    x = m

    for c in range(m, 0, -1): 
        y = lambda x: J(x, c, g)        
        result = mynewtonana(y, x, c, g, m, 10e-11, 12)
        decimal = result - int(result)
        
        if (round(decimal, 5) == 0.00000): 
            # Reveluate with less tolerance
            xn = mynewtonana(y, x, c, g, m, 10e-6, 12)
            result = xn

        x = result
        i = math.floor(x) + 1

        if (i % 2) != 0:

            u = int(H(i))
            v = int(((i + 1) / 2) - comb2(u-1))
            graph.add_edge(u,v)
        else: 
            v = int(H(i))
            u = int((i/2) - comb2(v-1))
            graph.add_edge(u,v)
      
        g = comb(i, c) - g -1
        
    mutex2.release()
    return graph


############################################################# MAIN ###############################################


if __name__ == "__main__":

    # A example to test the coding and decoding algorithms 
    G = nx.DiGraph()
    G.add_edges_from(
        [(1, 5), (2, 4), (4, 3), (4 , 5), (5, 6), (6, 12), 
         (11,12), (13, 21), (21, 22), (22, 23), (25, 26), 
         (23, 24), (26, 23), (27, 28), (28, 29), (29, 30), 
         (33, 34), (34, 35), (8, 9), (36, 9), (9, 10) ])

    # Ecnode the graph G
    m, tot = encode_nm(G)

    # decode the graph
    dec = decode_nm(tot,m)
    
    # Print out the decoded graph
    for k, v in dec.adjacency():
        print(f"{k}: {dec[k]}")



