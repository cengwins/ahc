from enum import Enum

class ARAEventTypes(Enum):
  REGULAR = "regular"
  FANT = "forwardant"
  BANT = "backwardant"
  DUPLICATE_ERROR = "duplicateerror"
  ROUTE_ERROR = "rotuerror"