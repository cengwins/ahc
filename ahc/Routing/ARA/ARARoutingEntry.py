from ahc.Routing.ARA.ARAConfiguration import ARAConfiguration

class ARARoutingEntry:
  def __init__(self, destination, nextHopAddress):
    self.destination = destination
    self.nextHopAddress = nextHopAddress
    self.pheromone = 0.0

  def increasePheromone(self):
    self.pheromone = self.pheromone + ARAConfiguration.PHEROMONE_DELTA

  def evaporatePheromone(self):
    self.pheromone = (1-ARAConfiguration.EVAPORATION_FACTOR) * self.pheromone