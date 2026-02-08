class ScoreManager:
    def __init__(self):
        self.score = 0
        self.high_score = 0
    
    def increase_score(self, points=10):
        self.score += points
        if self.score > self.high_score:
            self.high_score = self.score
    
    def get_score(self):
        return self.score
    
    def get_high_score(self):
        return self.high_score
    
    def reset_score(self):
        self.score = 0