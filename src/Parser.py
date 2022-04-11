import yaml as y

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

  def parse_data(self, inp): 
    data = y.load(inp)

    try:
      for topo in data.topologies:
        self.topologies.append(TopoType(topo.name, topo.nodes, topo.links))
      
      for exp in data.experiment:
        self.experiments.append(ExperimentType(exp.name, exp.topology, exp.sampling_count, exp.include_usrp))
    except AttributeError:
      print('Yaml file contains missing attributes')
