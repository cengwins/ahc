from SelfStabilization.SharedMemory import *

class RequestDirection:
  ASK = 1
  GRANT = 2



class AfekKuttenYangNodeCopy:
  def __init__(self, topology, node_index):
    self.topology = topology
    self.node_index = node_index

  def update(self):
    node_instance = self.topology.nodes[self.node_index]

    self.parent_node = node_instance.parent_node.val
    self.root_node = node_instance.root_node.val
    self.distance_to_root = node_instance.distance_to_root.val

    self.req_node = node_instance.req_node.val
    self.req_from_node = node_instance.req_from_node.val
    self.req_to_node = node_instance.req_to_node.val
    self.req_direction = node_instance.req_direction.val

    self.toggle = node_instance.toggle.val



class AfekKuttenYangNode(SharedMemoryNode):
  def __init__(self, topology, node_index, K):
    super().__init__(topology, node_index, K)

    self.req_node = RWLockedVal(None)
    self.req_from_node = RWLockedVal(None)
    self.req_to_node = RWLockedVal(None)
    self.req_direction = RWLockedVal(None)

    self.toggle = RWLockedVal(True)

    self.neighbor_copies = dict()

    for neighbor_node in self.neighbors:
      self.neighbor_copies[neighbor_node] = AfekKuttenYangNodeCopy(self.topology, neighbor_node)

  def setup(self):
    for neighbor_node in self.neighbors:
      self.neighbor_copies[neighbor_node].update()

  @property
  def am_root(self):
    return self.parent_node.val is None and self.root_node.val == self.node_index and self.distance_to_root.val == 0

  @property
  def not_root(self):
    if self.parent_node.val is None:
      return False

    parent_obj = self.neighbor_copies[self.parent_node.val]

    return self.parent_node.val in self.neighbors and \
      self.root_node.val > self.node_index and \
      self.root_node.val == parent_obj.root_node and \
      self.distance_to_root.val == parent_obj.distance_to_root + 1

  @property
  def max_root(self):
    root_node = self.root_node.val

    for neighbor_node in self.neighbors:
      neighbor = self.neighbor_copies[neighbor_node]

      if root_node < neighbor.root_node:
        return False

    return True

  def fetch_asking(self, q):
    q_node_obj = self.neighbor_copies[q]
    q_root_node = q_node_obj.root_node

    for neighbor_node in self.neighbors:
      neighbor = self.neighbor_copies[neighbor_node]

      if q_root_node < neighbor.root_node:
        return False

    return self.req_node.val == self.req_from_node.val == self.node_index and \
        self.req_to_node.val == q and \
        self.req_direction.val == RequestDirection.ASK

  def fetch_granted(self, q):
    q_node_obj = self.neighbor_copies[q]

    # Second statement has changed
    return self.req_node.val == q_node_obj.req_node and \
        self.node_index == q_node_obj.req_from_node and \
        q_node_obj.req_direction == RequestDirection.GRANT and \
        self.req_direction.val == RequestDirection.ASK

  @property
  def requestor(self):
    return self.req_to_node.val in self.neighbors and \
      self.neighbor_copies[self.req_to_node.val].root_node > self.node_index and \
      self.req_node.val == self.req_from_node.val == self.node_index

  def fetch_handling(self, q):
    q_node_obj = self.neighbor_copies[q]

    return self.req_node.val == q_node_obj.req_node and \
      self.req_from_node.val == q and \
      q_node_obj.req_to_node == self.node_index and \
      self.req_to_node.val == self.parent_node.val and \
      q_node_obj.req_direction == RequestDirection.ASK

  def fetch_request(self, q):
    q_node_obj = self.neighbor_copies[q]
    q_node_am_root = q_node_obj.parent_node is None and q_node_obj.root_node == q and q_node_obj.distance_to_root == 0

    return ((q_node_am_root and q_node_obj.req_node == q_node_obj.req_from_node == q) or \
      (q_node_obj.parent_node == self.node_index and q_node_obj.req_node != q and q_node_obj.req_node is not None)) and \
        q_node_obj.req_to_node == self.node_index

  @property
  def not_handling(self):
    return self.req_node.val is None and \
      self.req_from_node.val is None and \
      self.req_to_node.val is None and \
      self.req_direction.val is None

  def thread_handler(self):
    while True:
      if self.topology.stable.val:
        break

      for neighbor_node in self.neighbors:
        self.neighbor_copies[neighbor_node].update()

      is_all_toggle = True

      for neighbor_node in self.neighbors:
        if self.toggle.val != self.topology.nodes[neighbor_node].neighbor_copies[self.node_index].toggle:
          is_all_toggle = False
          break

      if is_all_toggle:
        if not (self.not_root and self.max_root) and not self.am_root:
          self.parent_node.set(None)
          self.root_node.set(self.node_index)
          self.distance_to_root.set(0)

        elif not self.max_root:
          is_all_not_asking = True

          for neighbor_node in self.neighbors:
            if self.fetch_asking(neighbor_node):
              is_all_not_asking = False
              break

          if is_all_not_asking:
            selected_q = -1
            selected_root_node = -1

            for neighbor_node in self.neighbors:
              new_root_node = self.neighbor_copies[neighbor_node].root_node

              if new_root_node > selected_root_node:
                selected_root_node = new_root_node
                selected_q = neighbor_node

            if selected_q != -1:
              self.req_node.set(self.node_index)
              self.req_from_node.set(self.node_index)
              self.req_to_node.set(selected_q)
              self.req_direction.set(RequestDirection.ASK)

          elif self.requestor and self.fetch_granted(self.req_to_node.val):
            new_parent = self.req_to_node.val

            self.parent_node.set(new_parent)
            self.root_node.set(self.neighbor_copies[new_parent].root_node)
            self.distance_to_root.set(self.neighbor_copies[new_parent].distance_to_root + 1)

            self.req_node.set(None)
            self.req_from_node.set(None)
            self.req_to_node.set(None)
            self.req_direction.set(None)

        else:
          is_all_not_request_and_not_handling = True

          for neighbor_node in self.neighbors:
            if self.fetch_request(neighbor_node) and self.fetch_handling(neighbor_node):
              is_all_not_request_and_not_handling = False
              break

          if is_all_not_request_and_not_handling:
            if not self.not_handling:
              self.req_node.set(None)
              self.req_from_node.set(None)
              self.req_to_node.set(None)
              self.req_direction.set(None)

            elif self.am_root or \
                (self.parent_node.val is not None and self.neighbor_copies[self.parent_node.val].req_from_node != self.node_index):
              selected_q = None

              for neighbor_node in self.neighbors:
                if self.fetch_request(neighbor_node):
                  selected_q = neighbor_node
                  break

              if selected_q != None:
                self.req_node.set(self.neighbor_copies[selected_q].req_node)
                self.req_from_node.set(selected_q)
                self.req_to_node.set(self.parent_node.val)
                self.req_direction.set(RequestDirection.GRANT)


          elif self.am_root and self.req_direction.val == RequestDirection.ASK:
            self.req_direction.set(RequestDirection.GRANT)

          elif self.parent_node.val is not None and self.fetch_granted(self.parent_node.val):
            self.req_direction.set(RequestDirection.GRANT)

        self.topology.stable_statuses[self.node_index].set(
          self.max_root and (
            (self.node_index == self.K and self.am_root) or
            (self.node_index != self.K and self.not_root)
          )
        )

        self.toggle.set(not self.toggle.val)
