# import yaml as y

class TopoType:
  name = ""
  nodes = []

  def __init__(self, name, nodes, links):
      self.name = name
      self.nodes = nodes
      self.links = links

class ExperimentType: 
  name = ""
  topology_name = ""
  sampling_count = 0
  usrp_included = False

  def __init__(self, name, topology_name, sampling_count, include_hw):
    self.name = name
    self.topology_name = topology_name
    self.sampling_count = sampling_count
    self.usrp_included = include_hw
  
  

class AhcObject: 
  topologies = []
  experiments = []
  experiment_count = 0
  def __init__(self) -> None:
      pass
