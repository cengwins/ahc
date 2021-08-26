from SelfStabilization.SharedMemory import *

class AroraGoudaNode(SharedMemoryNode):
  def thread_handler(self):
    while True:
      if self.topology.stable.val:
        break

      any_change = False

      if self.root_node.val < self.node_index or \
            (self.parent_node.val == None and (self.root_node.val != self.node_index or self.distance_to_root.val != 0)) or \
            (self.parent_node.val != None and self.parent_node.val not in self.neighbors) or \
            self.distance_to_root.val >= self.K:
        self.parent_node.set(None)
        self.root_node.set(self.node_index)
        self.distance_to_root.set(0)

        any_change = True

      else:
        for neighbor_node__i in self.neighbors:
          neighbor_node_obj = self.topology.nodes[neighbor_node__i]

          if neighbor_node_obj.distance_to_root.val < self.K:
            if self.parent_node.val == neighbor_node__i:
              if self.root_node.val != neighbor_node_obj.root_node.val:
                self.root_node.set(neighbor_node_obj.root_node.val)
                self.distance_to_root.set(neighbor_node_obj.distance_to_root.val + 1)

                any_change = True

              elif self.distance_to_root.val != neighbor_node_obj.distance_to_root.val + 1:
                self.distance_to_root.set(neighbor_node_obj.distance_to_root.val + 1)

                any_change = True

            elif self.root_node.val < neighbor_node_obj.root_node.val:
              self.parent_node.set(neighbor_node_obj.node_index)
              self.root_node.set(neighbor_node_obj.root_node.val)
              self.distance_to_root.set(neighbor_node_obj.distance_to_root.val + 1)

              any_change = True

      self.topology.stable_statuses[self.node_index].set(not any_change)
