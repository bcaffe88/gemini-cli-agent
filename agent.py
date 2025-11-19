#!/usr/bin/env python3
import os
import sys
import json
from github import Github
from git import Repo
import google.generativeai as genai
import shutil
import time
import traceback

class AutonomousAgent:
    def __init__(self):
        # Configurar APIs
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
        
        if not self.github_token or not self.gemini_api_key:
            raise Exception("❌ Configure GITHUB_TOKEN e GEMINI_API_KEY!")
        
        self.gh = Github(self.github_token)
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
        
        self.workspace = "/app/workspace"
        os.makedirs(self.workspace, exist_ok=True)
        
        # Configurar git
        os.system('git config --global user.name "Gemini Agent"')
        os.system('git config --global user.email "agent@criptopnz.com"')
    
    def create_project_from_description(self, description, project_name, callback=None):
        """Cria um projeto completo a partir de uma descrição
        callback: função para enviar progresso (opcional)
        """
        
        def log(message, step=None):
            print(message)
            if callback:
                callback(message, step)
        
        try:
            log(f"🤖 Iniciando criação do projeto: {project_name}", "init")
            log(f"📝 Descrição: {description}", "init")
            
            # ETAPA 1: Planejar o projeto
            log("\n🧠 ETAPA 1/5: Planejando arquitetura...", "planning")
            plan = self._plan_project(description)
            log(f"✅ Plano criado: {plan.get('tipo', 'projeto')}", "planning")
            
            # ETAPA 2: Gerar código
            log(f"\n💻 ETAPA 2/5: Gerando {len(plan.get('arquivos', []))} arquivos...", "generating")
            code_files = self._generate_code(description, plan, callback=log)
            log(f"✅ {len(code_files)} arquivos gerados", "generating")
            
            # ETAPA 3: Criar repositório
            log("\n📦 ETAPA 3/5: Criando repositório no GitHub...", "repo")
            repo = self._create_github_repo(project_name)
            log(f"✅ Repositório: {repo.html_url}", "repo")
            
            # ETAPA 4: Adicionar arquivos
            log("\n📂 ETAPA 4/5: Commitando arquivos...", "commit")
            repo_path = self._setup_local_repo(repo, code_files)
            log("✅ Arquivos adicionados ao repositório", "commit")
            
            # ETAPA 5: Deploy
            log("\n🚀 ETAPA 5/5: Fazendo deploy...", "deploy")
            deploy_url = self._deploy_project(repo, repo_path)
            log(f"✅ Deploy completo!", "deploy")
            
            # SUCESSO
            result = {
                "success": True,
                "repo_url": repo.html_url,
                "deploy_url": deploy_url,
                "files": list(code_files.keys()),
                "project_name": project_name
            }
            
            log("\n🎉 PROJETO CRIADO COM SUCESSO!", "complete")
            log(f"📦 Repositório: {repo.html_url}", "complete")
            log(f"🌐 App online: {deploy_url}", "complete")
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Erro: {str(e)}\n{traceback.format_exc()}"
            log(error_msg, "error")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def _plan_project(self, description):
        """Usa Gemini para planejar o projeto"""
        prompt = f"""
Você é um arquiteto de software expert. Crie um plano DETALHADO para este projeto:

DESCRIÇÃO: {description}

Retorne APENAS um JSON válido (sem markdown, sem explicações) com esta estrutura EXATA:
{{
    "tipo": "web-app",
    "tecnologias": ["HTML5", "CSS3", "JavaScript"],
    "arquivos": [
        {{"path": "index.html", "descricao": "Página principal HTML5"}},
        {{"path": "style.css", "descricao": "Estilos CSS3 modernos"}},
        {{"path": "script.js", "descricao": "Lógica JavaScript"}}
    ],
    "features": ["Feature 1", "Feature 2", "Feature 3"]
}}

REGRAS IMPORTANTES:
- Use APENAS HTML, CSS e JavaScript vanilla (sem frameworks)
- Mínimo 3 arquivos: index.html, style.css, script.js
- Seja específico nas descrições
- Foque em criar algo funcional e moderno
- Liste todas as features importantes
"""
        
        response = self.model.generate_content(prompt)
        plan_text = response.text.strip()
        
        # Extrair JSON
        try:
            if "```json" in plan_text:
                plan_text = plan_text.split("```json")[1].split("```")[0]
            elif "```" in plan_text:
                plan_text = plan_text.split("```")[1].split("```")[0]
            
            plan = json.loads(plan_text.strip())
            
            # Validar estrutura
            if 'arquivos' not in plan or len(plan['arquivos']) == 0:
                raise ValueError("Plano sem arquivos")
            
            return plan
            
        except Exception as e:
            print(f"⚠️ Erro ao parsear plano, usando fallback: {e}")
            # Fallback: plano básico
            return {
                "tipo": "web-app",
                "tecnologias": ["HTML5", "CSS3", "JavaScript"],
                "arquivos": [
                    {"path": "index.html", "descricao": "Página principal"},
                    {"path": "style.css", "descricao": "Estilos CSS"},
                    {"path": "script.js", "descricao": "Lógica JavaScript"}
                ],
                "features": ["Interface responsiva", "Design moderno"]
            }
    
    def _generate_code(self, description, plan, callback=None):
        """Gera o código de cada arquivo"""
        code_files = {}
        
        arquivos = plan.get('arquivos', [])
        total = len(arquivos)
        
        for idx, file_info in enumerate(arquivos, 1):
            file_path = file_info['path']
            file_desc = file_info['descricao']
            
            if callback:
                callback(f"  📄 Gerando {file_path} ({idx}/{total})...", "generating")
            
            prompt = f"""
Crie o arquivo {file_path} para este projeto:

DESCRIÇÃO DO PROJETO: {description}

DESCRIÇÃO DO ARQUIVO: {file_desc}

TECNOLOGIAS: {', '.join(plan.get('tecnologias', []))}

FEATURES DO PROJETO: {', '.join(plan.get('features', []))}

REGRAS CRÍTICAS:
1. Retorne APENAS o código, sem explicações antes ou depois
2. Não use markdown (```), retorne o código puro
3. Código COMPLETO e FUNCIONAL
4. Se for HTML: estrutura completa com <!DOCTYPE html>
5. Se for CSS: design moderno, responsivo, cores vibrantes
6. Se for JS: código funcional e comentado
7. Use boas práticas e padrões modernos
8. Faça algo IMPRESSIONANTE visualmente

IMPORTANTE: O código será usado diretamente, então ZERO explicações, ZERO markdown.
"""
            
            try:
                response = self.model.generate_content(prompt)
                code = response.text.strip()
                
                # Limpar markdown se existir
                if code.startswith("```"):
                    lines = code.split("\n")
                    code = "\n".join(lines[1:-1]) if len(lines) > 2 else code
                    code = code.strip()
                
                code_files[file_path] = code
                time.sleep(2)  # Rate limit
                
            except Exception as e:
                print(f"⚠️ Erro ao gerar {file_path}: {e}")
                # Fallback básico
                if file_path.endswith('.html'):
                    code_files[file_path] = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{plan.get('tipo', 'Projeto')}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Projeto em construção</h1>
    <p>{description}</p>
    <script src="script.js"></script>
</body>
</html>"""
                elif file_path.endswith('.css'):
                    code_files[file_path] = """* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Arial, sans-serif; padding: 20px; }"""
                elif file_path.endswith('.js'):
                    code_files[file_path] = """console.log('App iniciado');"""
        
        # README
        code_files["README.md"] = f"""# {plan.get('tipo', 'Projeto').title()}

🤖 **Criado automaticamente pelo Gemini Agent**

## 📋 Descrição
{description}

## 🛠️ Tecnologias
{', '.join(plan.get('tecnologias', []))}

## ✨ Features
{chr(10).join([f'- {f}' for f in plan.get('features', [])])}

## 🚀 Como usar
1. Clone o repositório
2. Abra o `index.html` no navegador
3. Pronto!

---
💜 Criado com Gemini Agent by @BCaffé
"""
        
        return code_files
    
    def _create_github_repo(self, project_name):
        """Cria repositório no GitHub"""
        user = self.gh.get_user()
        
        try:
            repo = user.create_repo(
                project_name,
                description=f"🤖 Projeto criado automaticamente pelo Gemini Agent",
                private=False,
                auto_init=False
            )
            return repo
        except:
            # Se já existe, usa existente
            repo = user.get_repo(project_name)
            print(f"  ⚠️ Repositório já existe, reutilizando")
            return repo
    
    def _setup_local_repo(self, repo, code_files):
        """Clona repo e adiciona arquivos"""
        repo_path = os.path.join(self.workspace, repo.name)
        
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        
        repo_url = f"https://{self.github_token}@github.com/{repo.full_name}.git"
        
        try:
            git_repo = Repo.clone_from(repo_url, repo_path)
        except:
            os.makedirs(repo_path, exist_ok=True)
            git_repo = Repo.init(repo_path)
            git_repo.create_remote('origin', repo_url)
        
        # Criar arquivos
        for file_path, content in code_files.items():
            full_path = os.path.join(repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Commit e push
        git_repo.git.add(A=True)
        git_repo.index.commit("🤖 Initial commit - Created by Gemini Agent")
        
        try:
            git_repo.git.push('--set-upstream', 'origin', 'main')
        except:
            try:
                git_repo.git.push('--set-upstream', 'origin', 'master')
            except Exception as e:
                print(f"⚠️ Erro no push: {e}")
        
        return repo_path
    
    def _deploy_project(self, repo, repo_path):
        """Deploy via GitHub Pages"""
        try:
            # Habilitar GitHub Pages
            repo.create_file(
                ".github/workflows/pages.yml",
                "Setup GitHub Pages",
                """name: Deploy to GitHub Pages
on:
  push:
    branches: [ main, master ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./
""",
                branch="main"
            )
            
            time.sleep(2)
            
            # Tentar habilitar Pages
            try:
                repo.create_pages_site(source={"branch": "main", "path": "/"})
            except:
                pass
            
            pages_url = f"https://{repo.owner.login}.github.io/{repo.name}/"
            return pages_url
            
        except Exception as e:
            print(f"⚠️ Deploy automático falhou: {e}")
            return repo.html_url


# CLI
def main():
    if len(sys.argv) < 2:
        print("""
🤖 GEMINI AUTONOMOUS AGENT

Uso:
  python agent.py create "descrição" nome-projeto

Exemplo:
  python agent.py create "app de delivery de pizzaria" pizzaria-app
        """)
        return
    
    command = sys.argv[1]
    
    if command == "create":
        description = sys.argv[2]
        project_name = sys.argv[3] if len(sys.argv) > 3 else f"project-{int(time.time())}"
        
        agent = AutonomousAgent()
        result = agent.create_project_from_description(description, project_name)
        
        if result['success']:
            print(f"\n✅ Acesse: {result['deploy_url']}")
        else:
            print(f"\n❌ Erro: {result['error']}")

if __name__ == "__main__":
    main()
