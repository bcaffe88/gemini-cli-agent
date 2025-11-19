// Estado global
let currentProjectId = null;
let progressInterval = null;

// Elementos DOM
const mainForm = document.getElementById('mainForm');
const progressCard = document.getElementById('progressCard');
const successCard = document.getElementById('successCard');
const errorCard = document.getElementById('errorCard');
const projectForm = document.getElementById('projectForm');
const description = document.getElementById('description');
const projectName = document.getElementById('projectName');
const charCount = document.getElementById('charCount');
const progressLog = document.getElementById('progressLog');

// Contador de caracteres
description.addEventListener('input', () => {
    charCount.textContent = description.value.length;
});

// Auto-gerar nome do projeto a partir da descrição
description.addEventListener('blur', () => {
    if (!projectName.value && description.value) {
        const words = description.value
            .toLowerCase()
            .split(' ')
            .slice(0, 3)
            .join('-')
            .replace(/[^a-z0-9-]/g, '');
        projectName.value = words || 'meu-projeto';
    }
});

// Função para definir exemplo
function setExample(desc, name) {
    description.value = desc;
    projectName.value = name;
    charCount.textContent = desc.length;
    description.focus();
}

// Submit do formulário
projectForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const desc = description.value.trim();
    const name = projectName.value.trim();
    
    if (!desc || !name) {
        alert('Preencha todos os campos!');
        return;
    }
    
    // Validar nome do projeto
    if (!/^[a-z0-9-]+$/.test(name)) {
        alert('Nome do projeto inválido! Use apenas letras minúsculas, números e hífens.');
        return;
    }
    
    await createProject(desc, name);
});

// Criar projeto
async function createProject(desc, name) {
    try {
        // Mostrar tela de progresso
        showScreen('progress');
        addLog('🚀 Iniciando criação do projeto...');
        
        // Chamar API
        const response = await fetch('/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                description: desc,
                project_name: name
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Erro ao criar projeto');
        }
        
        currentProjectId = data.project_id;
        addLog(`✅ Projeto iniciado: ${currentProjectId}`);
        
        // Monitorar progresso
        startProgressMonitoring();
        
    } catch (error) {
        console.error('Erro:', error);
        showError(error.message);
    }
}

// Monitorar progresso
function startProgressMonitoring() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/progress/${currentProjectId}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    if (msg.step === 'complete') {
                        // Projeto completo
                        clearInterval(progressInterval);
                        showSuccess(msg.result);
                    } else if (msg.step === 'error') {
                        // Erro
                        clearInterval(progressInterval);
                        showError(msg.error);
                    } else {
                        // Atualizar progresso
                        updateProgress(msg.step, msg.message);
                        addLog(msg.message);
                    }
                });
            }
        } catch (error) {
            console.error('Erro ao monitorar progresso:', error);
        }
    }, 1000);
}

// Atualizar progresso visual
function updateProgress(step, message) {
    const steps = document.querySelectorAll('.step');
    
    steps.forEach(stepEl => {
        const stepName = stepEl.getAttribute('data-step');
        
        if (stepName === step) {
            stepEl.classList.add('active');
        } else if (shouldMarkCompleted(stepName, step)) {
            stepEl.classList.remove('active');
            stepEl.classList.add('completed');
        }
    });
}

// Verificar se step deve ser marcado como completo
function shouldMarkCompleted(stepName, currentStep) {
    const order = ['init', 'planning', 'generating', 'repo', 'commit', 'deploy'];
    const currentIndex = order.indexOf(currentStep);
    const stepIndex = order.indexOf(stepName);
    return stepIndex < currentIndex;
}

// Adicionar log
function addLog(message) {
    const logEntry = document.createElement('div');
    logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logEntry.style.marginBottom = '5px';
    progressLog.appendChild(logEntry);
    progressLog.scrollTop = progressLog.scrollHeight;
}

// Mostrar sucesso
function showSuccess(result) {
    showScreen('success');
    
    document.getElementById('repoLink').href = result.repo_url;
    document.getElementById('deployLink').href = result.deploy_url;
    document.getElementById('filesCount').textContent = result.files.length;
    document.getElementById('projectNameResult').textContent = result.project_name;
    
    // Confetti effect (opcional)
    triggerConfetti();
}

// Mostrar erro
function showError(message) {
    showScreen('error');
    document.getElementById('errorMessage').textContent = message;
}

// Alternar telas
function showScreen(screen) {
    mainForm.classList.add('hidden');
    progressCard.classList.add('hidden');
    successCard.classList.add('hidden');
    errorCard.classList.add('hidden');
    
    switch(screen) {
        case 'form':
            mainForm.classList.remove('hidden');
            break;
        case 'progress':
            progressCard.classList.remove('hidden');
            // Reset progresso
            document.querySelectorAll('.step').forEach(step => {
                step.classList.remove('active', 'completed');
            });
            progressLog.innerHTML = '';
            break;
        case 'success':
            successCard.classList.remove('hidden');
            break;
        case 'error':
            errorCard.classList.remove('hidden');
            break;
    }
}

// Reset formulário
function resetForm() {
    showScreen('form');
    projectForm.reset();
    charCount.textContent = '0';
    currentProjectId = null;
    
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

// Confetti effect
function triggerConfetti() {
    // Criar confetti simples com emojis
    const emojis = ['🎉', '🎊', '✨', '🚀', '💜', '⭐'];
    
    for (let i = 0; i < 30; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.textContent = emojis[Math.floor(Math.random() * emojis.length)];
            confetti.style.position = 'fixed';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.top = '-50px';
            confetti.style.fontSize = '30px';
            confetti.style.zIndex = '9999';
            confetti.style.pointerEvents = 'none';
            confetti.style.animation = 'fall 3s linear';
            
            document.body.appendChild(confetti);
            
            setTimeout(() => confetti.remove(), 3000);
        }, i * 100);
    }
}

// Adicionar animação de queda
const style = document.createElement('style');
style.textContent = `
    @keyframes fall {
        to {
            transform: translateY(100vh) rotate(360deg);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Check health
async function checkHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        let message = `Status: ${data.status}\n`;
        message += `GitHub: ${data.github_configured ? '✅' : '❌'}\n`;
        message += `Gemini: ${data.gemini_configured ? '✅' : '❌'}`;
        
        alert(message);
    } catch (error) {
        alert('Erro ao verificar status: ' + error.message);
    }
}

// Log inicial
console.log('🤖 Gemini Agent iniciado!');
console.log('💜 Desenvolvido por CriptoPNZ');
