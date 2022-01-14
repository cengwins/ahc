# from Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, ComponentRegistry, Lock, Thread, Topology
#TODO: Does not use AHC messaging!

from random import randrange, randint
import threading, time, queue, math, heapq as hq

DEFAULT_GRID_WIDTH = 80
DEFAULT_GRID_HEIGHT = 80
MAX_NEIGHBOR_DISTANCE = 5
DEFAULT_ASSUMED_DISTANCE = 25

MESSAGE_TYPES = {
  0: "PingNeighbor",
  1: "LSABroadcast",
  2: "TextMessage",
}

# This is the message class that will be used to send messages between nodes
class Message:
  def __init__(self, sender):
    self.sender = sender

# HelloMessages are used to send a ping to a neighbor
class HelloMessage (Message):
  def __init__(self, sender, link):
    super().__init__(sender)
    self.type = 0
    self.link = link

# LSA Broadcast messages are used to announce neighbors of a node to the rest of the network
class LSAMessage (Message):
  def __init__(self, sender, neighbors, source):
    super().__init__(sender)
    self.type = 1
    self.neighbors = neighbors
    self.source = source
    self.visited = []

  def add_visited(self, node):
    self.visited.append(node)

# TextMessage are used to send text messages between nodes
# A node will use its own knowledge of the network to generate a shortest path to the destination
class TextMessage (Message):
  def __init__(self, sender, receiver, text, path):
    super().__init__(sender)
    self.type = 2
    self.receiver = receiver
    self.text = text
    self.path = path

class Link:
  def __init__(self, node1, node2):
    self.node1 = node1
    self.node2 = node2
    self.distance = Grid.distance(node1, node2)
    self.quality = randrange(10) + 1
    self.effective_distance = self.distance * self.quality

# class Edge:
#   def __init__(self, node1_id, node2_id, distance):
#     Edge.val = {}
#     Edge.val[(node1_id, node2_id)] = distance
class Location:
  def __init__(self, x, y):
    self.x = x
    self.y = y

  def __repr__(self):
    return "Location(%d, %d)" % (self.x, self.y)
# Both Grid and Location classes are used to represent the grid and the location of the nodes
# They allow for communication between the nodes ONLY IF they are in range of one another
class Grid:
  def __init__(self):
    self.width = DEFAULT_GRID_WIDTH
    self.height = DEFAULT_GRID_HEIGHT
    self.nodes = []
  
  def __refresh_nodes(self):
    for node in self.nodes:
      node.refresh()

  def __are_neighbors(self, node1, node2):
    if node1 == node2:
      return False
    distance = (node1.location.x - node2.location.x)**2 + (node1.location.y - node2.location.y)**2
    return distance <= MAX_NEIGHBOR_DISTANCE**2

  def __find_neighbors(self, node):
    neighbors = []
    for other_node in self.nodes:
      if self.__are_neighbors(node, other_node):
        neighbors.append(other_node)
    return neighbors

  # used by links to generate quality of the link
  def distance(node1, node2):
    square = (node1.location.x - node2.location.x)**2 + (node1.location.y - node2.location.y)**2
    return square**0.5

  # keeps track of the nodes in the grid
  # nodes cannot access this data (there is no self.grid.nodes access in the node class)
  # this is used purely to call an update on the nodes to generate 
  # their topology maps on their own since a new node has joined the grid
  def add_node(self, node):
    self.nodes.append(node)
    self.__refresh_nodes()

  def delete_node(self, node):
    self.nodes.remove(node)
    del node
    self.__refresh_nodes()

  # WARNING: if neighbor conditions below are removed, the system will become centralized
  # This function is used to send a message to all the neighbors of the node
  # If there is no neighborhood relationship, messages are not sent
  def send_message_to_neighbors(self, message):
    for neighbor in self.__find_neighbors(message.sender):
      neighbor.receive_message(message)

  def send_hello_message_to_neighbors(self, node):
    for neighbor in self.__find_neighbors(node):
      neighbor.receive_message(HelloMessage(node, Link(node, neighbor)))

  # This function sends a message to a neighbor node
  def send_message(self, node1, node2, message):
    if self.__are_neighbors(node1, node2):
      node2.receive_message(message)


class Node:
  instance_id = 1
  def __init__(self, x, y, grid):
    self.location = Location(x,y)
    self.grid = grid
    self.neighbors = []
    self.neighbor_distances = {}
    self.topology = {}
    self.id = Node.instance_id
    Node.instance_id += 1
    self.grid.add_node(self)
    # self.threaded_tasks()
    self.refresh()

  def refresh(self):
    self.grid.send_hello_message_to_neighbors(self)
    self.send_lsa()

  # def start_hello(self):
  #   while(True):
  #     self.grid.send_hello_message_to_neighbors(self)
  #     self.send_lsa()
  #     time.sleep(5)

  # def threaded_tasks(self):
  #   thread1 = threading.Thread(target=self.start_hello, daemon=True)
  #   thread1.start()
    
  def add_neighbor(self, node, distance):
    if node not in self.neighbors:
      self.neighbors.append(node)
      self.neighbor_distances[node.id] = distance

  # This function is used to send a message to all the neighbors of the node
  # If there is no neighborhood relationship, messages are not sent
  # Checks are done at grid class to ensure there is no cheating neighbor relationships
  def send_message_to_neighbors(self, message):
    self.grid.send_message_to_neighbors(self, message)

  def send_message_to_neighbor(self, node, message):
    self.grid.send_message(self, node, message)

  def add_to_topology(self, node, neighbors):
    self.topology[node] = neighbors

  # This function bounces incoming LSA messages to the neighbors
  # If the neighbor vas visited earlier, the message is not sent
  def forward_lsa(self, message):
    message.add_visited(self)
    for neighbor in self.neighbors:
      if neighbor not in message.visited:
        self.grid.send_message(self, neighbor, message)
  
  # This function announces the node's immediate neighbors to the rest of the network
  def send_lsa(self):
    lsa_message = LSAMessage(self, self.neighbors, self)
    lsa_message.add_visited(self)
    self.grid.send_message_to_neighbors(lsa_message)

  def receive_message(self, message):
    if message.type == 0:
      # Hello message
      self.add_neighbor(message.sender, message.link.effective_distance)
    elif message.type == 1:
      # LSA message
      self.add_to_topology(message.source, message.neighbors)
      self.forward_lsa(message)
    elif message.type == 2:
      # print("Received a text message from %d to %d" % (message.sender.id, self.id))
       # Text message
      self.receive_text_message(message)

  def receive_text_message(self, message):
    if message.path[len(message.path)-1] == self.id:
      print("SUCCESS: Message from %d to %d: %s" % (message.sender.id, self.id, message.text))
    else:
      current_path_index = message.path.index(self.id)
      target_index = current_path_index + 1
      target_node = None
      for neighbor in self.neighbors:
        if neighbor.id == message.path[target_index]:
          target_node = neighbor
      # print('Message forwarded to %d from %d' % (target_node.id, self.id))
      self.send_message_to_neighbor(target_node, message)

  def send_text_message(self, target, text):
    path = self.find_shorthest_path_to_node(target)
    if len(path) < 1:
      print("ERROR: No path found to node %d" % target.id)
      return
    next_node_id = path[1]
    next_node = None
    for neighbor in self.neighbors:
      if neighbor.id == next_node_id:
        next_node = neighbor
    message = TextMessage(self, next_node, text, path)
    # print('Message sent to %d from %d' % (target.id, self.id))
    self.send_message_to_neighbor(next_node, message)

  # Preps graph for use in dijkstra's algorithm
  def find_shorthest_path_to_node(self, target):
    graph = {}

    for entry in self.topology:
      graph[entry.id] = {}
      for item in self.topology[entry]:
        # FSR Assumes distances between other neighbors, since we do not have access to that information
        graph[entry.id][item.id] = DEFAULT_ASSUMED_DISTANCE 

    graph[self.id] = self.neighbor_distances
    try:
      return self.dijkstra(graph, self.id, target.id)
    except:
      print("ERROR: Could not find path to node %d" % target.id)

  # Returns shortest path as an array using Dijkstra's algorithm
  def dijkstra(self, graph, starting_vertex, target_id):
    # Initialization
    queue = []
    distances = {}
    previous_vertices = {}
    # Add all nodes to the queue
    for vertex in graph:
      distances[vertex] = math.inf
      previous_vertices[vertex] = None
      queue.append(vertex)
    # Set the starting vertex to 0
    distances[starting_vertex] = 0
    previous_vertices[starting_vertex] = starting_vertex
    # While the queue is not empty
    while queue:
      current_vertex = min(queue, key=lambda vertex: distances[vertex])
      queue.remove(current_vertex)

      if current_vertex == target_id:
        break

      for neighbor in graph[current_vertex]:
        if neighbor not in queue:
          continue
        # Replace the distance if the new distance is less than the old distance
        new_distance = distances[current_vertex] + graph[current_vertex][neighbor]
        if new_distance < distances[neighbor]:
          distances[neighbor] = new_distance
          previous_vertices[neighbor] = current_vertex

    # Reconstruct path
    path = []
    current_vertex = target_id
    while current_vertex != starting_vertex:
      path.append(current_vertex)
      current_vertex = previous_vertices[current_vertex]
    # Add the starting vertex to the path
    path.append(starting_vertex)
    # Reverse the path
    path.reverse()

    return path
    
  def __repr__(self):
    return "Node {0} at {1}".format(self.id, self.location)

# Linear Topology closely packed

# grid = Grid()

# node1 = Node(0,0,grid)
# node2 = Node(1,1,grid)
# node3 = Node(2,2,grid)
# node4 = Node(3,3,grid)
# node5 = Node(4,4,grid)
# node6 = Node(5,5,grid)
# node7 = Node(6,6,grid)
# node8 = Node(7,7,grid)
# node9 = Node(8,8,grid)
# node10 = Node(9,9,grid)
# node11 = Node(10,10,grid)
# node12 = Node(11,11,grid)
# node13 = Node(12,12,grid)
# node14 = Node(13,13,grid)
# node15 = Node(14,14,grid)
# node16 = Node(15,15,grid)
# node17 = Node(16,16,grid)
# node18 = Node(17,17,grid)
# node19 = Node(18,18,grid)
# node20 = Node(19,19,grid)

# node1.send_text_message(node18, "Hello")

# DEMO 2
# Diagonal Topology

# grid = Grid()

# node1 = Node(0,0,grid)
# node2 = Node(2,2,grid)
# node3 = Node(4,4,grid)
# node4 = Node(6,6,grid)
# node5 = Node(8,8,grid)
# node6 = Node(10,10,grid)
# node7 = Node(12,12,grid)
# node8 = Node(14,14,grid)
# node9 = Node(16,16,grid)
# node10 = Node(18,18,grid)
# node11 = Node(20,20,grid)
# node12 = Node(22,22,grid)
# node13 = Node(24,24,grid)
# node14 = Node(26,26,grid)
# node15 = Node(28,28,grid)
# node16 = Node(30,30,grid)
# node17 = Node(32,32,grid)
# node18 = Node(34,34,grid)
# node19 = Node(36,36,grid)
# node20 = Node(38,38,grid)
# node21 = Node(40,40,grid)

# node22 = Node(40,0,grid)
# node23 = Node(38,2,grid)
# node24 = Node(36,4,grid)
# node25 = Node(34,6,grid)
# node26 = Node(32,8,grid)
# node27 = Node(30,10,grid)
# node28 = Node(28,12,grid)
# node29 = Node(26,14,grid)
# node30 = Node(24,16,grid)
# node31 = Node(22,18,grid)
# node32 = Node(20,20,grid)
# node33 = Node(18,22,grid)
# node34 = Node(16,24,grid)
# node35 = Node(14,26,grid)
# node36 = Node(12,28,grid)
# node37 = Node(10,30,grid)
# node38 = Node(8,32,grid)
# node39 = Node(6,34,grid)
# node40 = Node(4,36,grid)
# node41 = Node(2,38,grid)
# node42 = Node(0,40,grid)

# node1.send_text_message(node42, "Hello")

# DEMO 3
# Random Topology

grid = Grid()
nodes = []

for i in range(1,100):
  nodes.append(Node(randint(1,29),randint(1,29),grid))


upper = 90
for j in range(1,upper):
  nodes[randint(1,upper)].send_text_message(nodes[randint(1,upper)], "Hello")