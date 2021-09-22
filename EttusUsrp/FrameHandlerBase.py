from Ahc import ComponentModel, singleton
 



@singleton
class FramerObjects():
    framerobjects = {}
    def add_framer(self, id, obj):
        self.framerobjects[id] = obj
    
    def get_framer_by_id(self, id):
        return self.framerobjects[id]
    
class FrameHandlerBase(ComponentModel):

    def __init__(self,componentname, componentinstancenumber):
        super().__init__(componentname, componentinstancenumber)
        framers.add_framer(id(self), self)
        
framers = FramerObjects()
