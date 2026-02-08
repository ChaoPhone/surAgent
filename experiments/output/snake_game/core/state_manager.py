class StateManager:
    def __init__(self):
        self.state = 'paused'
        self.game_started = False
    
    def start_game(self):
        self.state = 'playing'
        self.game_started = True
    
    def pause_game(self):
        self.state = 'paused'
    
    def end_game(self):
        self.state = 'ended'
    
    def get_state(self):
        return self.state
    
    def is_game_started(self):
        return self.game_started