from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import threading
import queue
import os
from agent import AutonomousAgent

app = Flask(__name__)
CORS(app)

# Fila para armazenar progresso
progress_queues = {}

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create_project():
    """Endpoint para criar projeto"""
    data = request.json
    description = data.get('description', '')
    project_name = data.get('project_name', '')
    
    if not description or not project_name:
        return jsonify({
            'success': False,
            'error': 'Descrição e nome do projeto são obrigatórios'
        }), 400
    
    # Criar fila de progresso para este projeto
    project_id = f"{project_name}-{int(os.times().elapsed * 1000)}"
    progress_queues[project_id] = queue.Queue()
    
    # Função de callback para progresso
    def progress_callback(message, step):
        progress_queues[project_id].put({
            'message': message,
            'step': step
        })
    
    # Executar em thread separada
    def run_agent():
        try:
            agent = AutonomousAgent()
            result = agent.create_project_from_description(
                description, 
                project_name,
                callback=progress_callback
            )
            progress_queues[project_id].put({
                'message': 'complete',
                'step': 'complete',
                'result': result
            })
        except Exception as e:
            progress_queues[project_id].put({
                'message': f'Erro: {str(e)}',
                'step': 'error',
                'error': str(e)
            })
    
    thread = threading.Thread(target=run_agent)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'project_id': project_id,
        'message': 'Projeto iniciado! Acompanhe o progresso.'
    })

@app.route('/progress/<project_id>', methods=['GET'])
def get_progress(project_id):
    """Endpoint para obter progresso do projeto"""
    if project_id not in progress_queues:
        return jsonify({'error': 'Projeto não encontrado'}), 404
    
    messages = []
    q = progress_queues[project_id]
    
    # Pegar todas as mensagens disponíveis
    while not q.empty():
        try:
            msg = q.get_nowait()
            messages.append(msg)
        except queue.Empty:
            break
    
    return jsonify({
        'messages': messages
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'Gemini Agent',
        'github_configured': bool(os.environ.get('GITHUB_TOKEN')),
        'gemini_configured': bool(os.environ.get('GEMINI_API_KEY'))
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
