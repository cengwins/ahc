### Leader Election

#### Introduction
Election algorithms mainly aim to select one process among other process to act as the organizer of some distributed task. In the election algorithms, it is assumed that every active process in the distributed system has a unique priority number. Election algorithms provides following properties  

#### Election Algorithm: Echo algorithm with Extinction

In this section, the detailed information about echo algorithm with extinction is given. Behind this algorithm, there exist simple idea which is each initiator run the echo algorithm tagged with its ID. The wave started with highest ID completes. After that, that process, initiator becomes leader. 
If there exist a non-initiator in the system, it joins the first wave that hits them. For example, consider two process, process p and process q, participating a wave tagged with their names. The process takes a wave message from q tagged with its ID

\begin{itemize}
    \item If q $>$ p, then p makes the process q, the sender, its parent and changes to wave tagged with p. After that, it behaves the incoming messages accordingly. 
    \item If p $>$ q, then p continues with the wave tagged with q. 
    \item If p $=$ q, then treats the incoming message by depending on the algorithm implemented of the wave tagged with q. 
\end{itemize}

#### Minimum Spanning Trees: The Gallager-Humblet-Spira algorithm

First, if we consider the definition of minimum spanning tree, it is a tree that contains every process in the network and keeps the sum of the weights of channels minimum. It is assumed that different channels in the network have different weights in the network. 

The Gallager-Humblet-Spira algorithm is distributed version of Kruskal's algorithm which provides computing minimum spanning trees in a uni-processor setting. Kruskal's algorithm is based on choosing the lowest-weight edge in the network. In the implementation of Kruskal's algorithm cycles are not allowed, because it would be a contradiction with nature of minimum spanning trees. 

In distributed systems, it becomes harder for processes to decide whether its channels are outgoing edge or not. In the Gallager-Humblet-Spira algorithm, each fragment carries fragment name which is non-negative real number,and level which is greater or equal to 0. 

- sleep : If a processor in the sleep state, as happened in the election algorithm, it wakes up as soon as a message arrives 
- find : If a processor in the find state, there can be 2 options:
  - It might be waiting for report from its children for lowest-weight outgoing edge, 
  - Or, it is looking for its lowest-weight outgoing edge. 
- found : If a processor is in the found state, it informed its parent about its lowest-weight outgoing edge and it is aware of to its parent. 

In addition there also exist status for channels of processes to maintain status, which are

- basic edge : if an edge marked as a basic edge, then it is undecided whether it will be in the channel or not. 
- branch edge : If the channel is a part of the minimum spanning tree, then it is a branch edge 
- rejected : The rejected status means the channel is not a part of the minimum spanning tree
\end{itemize}