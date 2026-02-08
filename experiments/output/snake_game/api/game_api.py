from flask import Flask, request, jsonify
from core.game_logic import SnakeGame
from core.score_manager import ScoreManager
from core.state_manager import StateManager

app = Flask(__name__)
game = SnakeGame()
score_manager = ScoreManager()
state_manager = StateManager()

@app.route('/api/start', methods=['GET'])
def start_game():
    game.reset_game()
    score_manager.reset_score()
    state_manager.start_game()
    return jsonify(status='started', message='Game started')

@app.route('/api/move', methods=['POST'])
def move():
    if not state_manager.is_game_started():
        return jsonify(status='error', message='Game not started'), 400
    
    direction = request.json.get('direction')
    if direction not in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
        return jsonify(status='error', message='Invalid direction'), 400
    
    success = game.move(direction)
    
    if success:
        if game.is_game_over():
            state_manager.end_game()
            return jsonify(status='game_over', score=score_manager.get_score())
        
        # 检查是否吃到食物
        if len(game.get_snake()) > 3:  # 如果蛇变长了，说明吃到了食物
            score_manager.increase_score()
        
        return jsonify(
            status='moved',
            score=score_manager.get_score(),
            snake=game.get_snake(),
            food=game.get_food()
        )
    else:
        state_manager.end_game()
        return jsonify(status='game_over', score=score_manager.get_score())

@app.route('/api/score', methods=['GET'])
def get_score():
    return jsonify(
        score=score_manager.get_score(),
        high_score=score_manager.get_high_score()
    )

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(
        state=state_manager.get_state(),
        game_started=state_manager.is_game_started(),
        game_over=game.is_game_over()
    )

@app.route('/api/reset', methods=['POST'])
def reset_game():
    game.reset_game()
    score_manager.reset_score()
    state_manager.start_game()
    return jsonify(status='reset', message='Game reset')