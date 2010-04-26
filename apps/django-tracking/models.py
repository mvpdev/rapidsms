from django.db import models

"""
Contains all the virtual class to use when you want to track a model.
"""

#TODO : forcing subclassing is bad. We should probably do that using
# register or generic relationships like django-tag do.


class StateError(Exception):
    """
    Exception used when manipulating states. Just a wrapper around Exception
    to allow clean try / catch.
    """
    pass



class State(models.Model):
    """
    A state in which any tracked object can be. Virtual, should be subclassed.
    """
    
    title = models.CharField(max_lenght=400, blank=True)
    cancel = models.BooleanField(default=False)
    created = models.DateTimeField(auto_created=True)  
    holder = models.ForeignKey("Tracked")
    
    
    def create_next_state(self):
        """
        Any state should implement this to create the state right after it.
        It shoudl return a state object.
        """
        raise ValueError("Not implemented")
    


class Tracked(models.Model):
    """
    A model destined to be tracked. Virtual, should be subclassed.
    """
    
    state = models.ForeignKey(State)
    
    
    def __init__(self, initial_state):
        super(models.Model, self).__init__(self)
        self.state = initial_state
        
    
    def get_history(self):
        """
        Get the queryset of the states this tracked object has been in.
        """
        
        return State.objects().filter(holder=self).order_by("-created")
    

    def get_previous_state(self):
        """
        Give you the previous state in the history of the tracked object.
        """
        previous_states = self.get_history().filter(cancel=False, 
                                                    created_lt=self.created)
        if previous_states.count():
            return previous_states[0]
        
        raise StateError("No state before this one")    
    

    def set_to_next_state(self, state=None):
        """
        Set the tracked object to it's next state.
        """
        
        self.state = state or self.state.create_next_state()
        
    
    def cancel(self):
        """
        Cancel the current state.
        """
        self.state.cancelled = True
        try:
            self.state = self.get_previous_state()
        except StateError, e:
            self.state.cancelled = False
            raise e