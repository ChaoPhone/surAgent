const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const gridSize = 20;
const width = 400;
const height = 400;

let gameLoop;
let currentDirection = 'RIGHT';
let gameStarted = false;
let gamePaused = false;
let gameOver = false;
let score = 0;
let highScore = 0;

// 初始化游戏
function initGame() {
    document.getElementById('score').textContent = '分数: 0';
    document.getElementById('highScore').textContent = '最高分: 0';
    document.getElementById('gameStatus').textContent = '游戏状态: 等待开始';
    document.getElementById('startBtn').disabled = false;
    document.getElementById('pauseBtn').disabled = true;
    document.getElementById('resetBtn').disabled = true;
}

// 绘制游戏
function drawGame(snake, food) {
    // 清空画布
    ctx.fillStyle = '#f0f0f0';
    ctx.fillRect(0, 0, width, height);
    
    // 绘制蛇
    ctx.fillStyle = '#4CAF50';
    snake.forEach((segment, index) => {
        if (index === 0) {
            // 蛇头
            ctx.fillStyle = '#2E7D32';
        } else {
            // 蛇身
            ctx.fillStyle = '#4CAF50';
        }
        ctx.fillRect(segment[0], segment[1], gridSize, gridSize);
        ctx.strokeStyle = '#000';
        ctx.strokeRect(segment[0], segment[1], gridSize, gridSize);
    });
    
    // 绘制食物
    ctx.fillStyle = '#FF5722';
    ctx.fillRect(food[0], food[1], gridSize, gridSize);
    ctx.strokeStyle = '#000';
    ctx.strokeRect(food[0], food[1], gridSize, gridSize);
}

// 开始游戏
function startGame() {
    fetch('/api/start')
        .then(response => response.json())
        .then(data => {
            console.log('游戏开始:', data);
            gameStarted = true;
            gamePaused = false;
            gameOver = false;
            document.getElementById('gameStatus').textContent = '游戏状态: 进行中';
            document.getElementById('startBtn').disabled = true;
            document.getElementById('pauseBtn').disabled = false;
            document.getElementById('resetBtn').disabled = false;
            
            // 开始游戏循环
            if (gameLoop) clearInterval(gameLoop);
            gameLoop = setInterval(gameTick, 200);
        })
        .catch(error => {
            console.error('开始游戏失败:', error);
        });
}

// 暂停游戏
function pauseGame() {
    if (gamePaused) {
        // 恢复游戏
        gamePaused = false;
        document.getElementById('pauseBtn').textContent = '暂停游戏';
        document.getElementById('gameStatus').textContent = '游戏状态: 进行中';
        gameLoop = setInterval(gameTick, 200);
    } else {
        // 暂停游戏
        gamePaused = true;
        document.getElementById('pauseBtn').textContent = '继续游戏';
        document.getElementById('gameStatus').textContent = '游戏状态: 已暂停';
        clearInterval(gameLoop);
    }
}

// 重置游戏
function resetGame() {
    fetch('/api/reset', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('游戏重置:', data);
        gameStarted = true;
        gamePaused = false;
        gameOver = false;
        currentDirection = 'RIGHT';
        document.getElementById('gameStatus').textContent = '游戏状态: 进行中';
        document.getElementById('pauseBtn').textContent = '暂停游戏';
        
        if (gameLoop) clearInterval(gameLoop);
        gameLoop = setInterval(gameTick, 200);
    })
    .catch(error => {
        console.error('重置游戏失败:', error);
    });
}

// 游戏循环
function gameTick() {
    if (!gameStarted || gamePaused || gameOver) return;
    
    fetch('/api/move', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ direction: currentDirection })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'game_over') {
            gameOver = true;
            clearInterval(gameLoop);
            document.getElementById('gameStatus').textContent = '游戏状态: 游戏结束';
            document.getElementById('startBtn').disabled = false;
            document.getElementById('pauseBtn').disabled = true;
            score = data.score;
            document.getElementById('score').textContent = `分数: ${score}`;
            if (score > highScore) {
                highScore = score;
                document.getElementById('highScore').textContent = `最高分: ${highScore}`;
            }
        } else if (data.status === 'moved') {
            drawGame(data.snake, data.food);
            score = data.score;
            document.getElementById('score').textContent = `分数: ${score}`;
            if (score > highScore) {
                highScore = score;
                document.getElementById('highScore').textContent = `最高分: ${highScore}`;
            }
        }
    })
    .catch(error => {
        console.error('移动失败:', error);
    });
}

// 键盘控制
document.addEventListener('keydown', (event) => {
    if (!gameStarted || gamePaused || gameOver) return;
    
    switch(event.key) {
        case 'ArrowUp':
            currentDirection = 'UP';
            break;
        case 'ArrowDown':
            currentDirection = 'DOWN';
            break;
        case 'ArrowLeft':
            currentDirection = 'LEFT';
            break;
        case 'ArrowRight':
            currentDirection = 'RIGHT';
            break;
    }
});

// 获取游戏状态
function updateGameStatus() {
    fetch('/api/state')
        .then(response => response.json())
        .then(data => {
            console.log('游戏状态:', data);
        })
        .catch(error => {
            console.error('获取状态失败:', error);
        });
}

// 获取分数
function updateScore() {
    fetch('/api/score')
        .then(response => response.json())
        .then(data => {
            score = data.score;
            highScore = data.high_score;
            document.getElementById('score').textContent = `分数: ${score}`;
            document.getElementById('highScore').textContent = `最高分: ${highScore}`;
        })
        .catch(error => {
            console.error('获取分数失败:', error);
        });
}

// 页面加载时初始化
window.onload = function() {
    initGame();
    updateScore();
    
    // 绑定按钮事件
    document.getElementById('startBtn').addEventListener('click', startGame);
    document.getElementById('pauseBtn').addEventListener('click', pauseGame);
    document.getElementById('resetBtn').addEventListener('click', resetGame);
    
    // 初始绘制
    drawGame([], [0, 0]);
};