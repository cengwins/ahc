from ahc.Ahc import Lock


def singleton(cls):
  instance = [None]
  def wrapper(*args, **kwargs):
    if instance[0] is None:
      instance[0] = cls(*args, **kwargs)
    return instance[0]
  return wrapper

@singleton
class GSRExperimentCollector:
    MESSAGE_COUNT = {}
    completion = []
    first_routing_completion = 0
    n_control_messages = 0
    completion_lock = Lock()
