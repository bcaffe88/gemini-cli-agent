#!/usr/bin/env python3
import os
import sys
import json
from github import Github
from git import Repo
import google.generativeai as genai
import shutil
import time

class AutonomousAgent:
    def __init__(self):
        # Configurar APIs
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
        self.vercel_token = os.environ.get('VERCEL_TOKEN', '')
        
        if not self.github_token or not self.gemini_api_key:
            raise Exception("❌ Configure GITHUB_TOKEN e GEMINI_API_KEY!")
        
        self.gh = Github(self.github_token)
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
        
        self.workspace = "/app/workspace"
        os.makedirs(self.workspace, exist_ok=True)
    
    def create_project_from_description(self, description, project_name):
        """Cria um projeto completo a partir de uma descrição"""
        
        print(f"\n🤖 Iniciando criação do projeto: {project_name}")
        print(f"📝 Descrição: {description}\n")
        
        # ETAPA 1: Planejar o projeto com Gemini
        print("🧠 ETAPA 1: Planejando arquitetura...")
        plan = self._plan_project(description)
        print(f"✅ Plano criado:\n{plan}\n")
        
        # ETAPA 2: Gerar código
        print("💻 ETAPA 2: Gerando código...")
        code_files = self._generate_code(description, plan)
        print(f"✅ {len(code_files)} arquivos gerados\n")
        
        # ETAPA 3: Criar repositório no GitHub
        print("📦 ETAPA 3: Criando repositório no GitHub...")
        repo = self._create_github_repo(project_name)
        print(f"✅ Repositório criado: {repo.html_url}\n")
        
        # ETAPA 4: Clonar e adicionar arquivos
        print("📂 ETAPA 4: Adicionando arquivos ao repositório...")
        repo_path = self._setup_local_repo(repo, code_files)
        print(f"✅ Arquivos adicionados\n")
        
        # ETAPA 5: Deploy automático
        print("🚀 ETAPA 5: Fazendo deploy...")
        deploy_url = self._deploy_project(repo, repo_path)
        print(f"✅ Deploy completo!\n")
        
        # RESULTADO FINAL
        print("=" * 60)
        print("🎉 PROJETO CRIADO COM SUCESSO!")
        print("=" * 60)
        print(f"📦 Repositório: {repo.html_url}")
        print(f"🌐 App online: {deploy_url}")
        print(f"📁 Arquivos: {len(code_files)}")
        print("=" * 60)
        
        return {
            "repo_url": repo.html_url,
            "deploy_url": deploy_url,
            "files": list(code_files.keys())
        }
    
    def _plan_project(self, description):
        """Usa Gemini para planejar o projeto"""
        prompt = f"""
Você é um arquiteto de software expert. Crie um plano detalhado para este projeto:

DESCRIÇÃO: {description}

Retorne um JSON com esta estrutura:
{{
    "tipo": "web-app | landing-page | dashboard | api",
    "tecnologias": ["React", "TailwindCSS", ...],
    "arquivos": [
        {{"path": "index.html", "descricao": "Página principal"}},
        {{"path": "style.css", "descricao": "Estilos"}},
        ...
    ],
    "features": ["Feature 1", "Feature 2", ...]
}}

Seja específico e prático. Foque em criar algo funcional e moderno.
"""
        
        response = self.model.generate_content(prompt)
        plan_text = response.text
        
        # Extrair JSON da resposta
        try:
            # Remove markdown code blocks se existir
            if "```json" in plan_text:
                plan_text = plan_text.split("```json")[1].split("```")[0]
            elif "```" in plan_text:
                plan_text = plan_text.split("```")[1].split("```")[0]
            
            plan = json.loads(plan_text.strip())
            return plan
        except:
            # Fallback: retornar plano básico
            return {
                "tipo": "web-app",
                "tecnologias": ["HTML", "CSS", "JavaScript"],
                "arquivos": [
                    {"path": "index.html", "descricao": "Página principal"},
                    {"path": "style.css", "descricao": "Estilos"},
                    {"path": "script.js", "descricao": "Lógica"}
                ],
                "features": ["Interface responsiva", "Design moderno"]
            }
    
    def _generate_code(self, description, plan):
        """Gera o código de cada arquivo usando Gemini"""
        code_files = {}
        
        for file_info in plan.get('arquivos', []):
            file_path = file_info['path']
            file_desc = file_info['descricao']
            
            print(f"  📄 Gerando {file_path}...")
            
            prompt = f"""
Crie o arquivo {file_path} para este projeto:

DESCRIÇÃO DO PROJETO: {description}

DESCRIÇÃO DO ARQUIVO: {file_desc}

TECNOLOGIAS: {', '.join(plan.get('tecnologias', []))}

IMPORTANTE:
- Código completo e funcional
- Sem comentários explicativos desnecessários
- Use boas práticas
- Design moderno e responsivo
- Se for CSS, use um design premium e colorido
- Se for HTML, inclua estrutura completa

Retorne APENAS o código, sem explicações.
"""
            
            response = self.model.generate_content(prompt)
            code = response.text
            
            # Limpar código (remover markdown)
            if "```" in code:
                code = code.split("```")[1]
                if code.startswith("html") or code.startswith("css") or code.startswith("javascript"):
                    code = "\n".join(code.split("\n")[1:])
                code = code.strip()
            
            code_files[file_path] = code
            time.sleep(1)  # Evitar rate limit
        
        # Adicionar README automático
        code_files["README.md"] = f"""# {plan.get('tipo', 'Projeto').title()}

🚀 Projeto criado automaticamente pelo Gemini Agent

## 📋 Descrição
{description}

## 🛠️ Tecnologias
{', '.join(plan.get('tecnologias', []))}

## ✨ Features
{chr(10).join([f'- {f}' for f in plan.get('features', [])])}

## 🚀 Deploy
Este projeto foi deployado automaticamente.

---
Criado com ❤️ por Gemini Agent
"""
        
        return code_files
    
    def _create_github_repo(self, project_name):
        """Cria repositório no GitHub"""
        user = self.gh.get_user()
        
        try:
            # Tenta criar novo repo
            repo = user.create_repo(
                project_name,
                description=f"🤖 Projeto criado automaticamente pelo Gemini Agent",
                private=False,
                auto_init=False
            )
            return repo
        except:
            # Se já existe, usa o existente
            repo = user.get_repo(project_name)
            print(f"  ⚠️ Repositório já existe, usando existente")
            return repo
    
    def _setup_local_repo(self, repo, code_files):
        """Clona repo e adiciona arquivos"""
        repo_path = os.path.join(self.workspace, repo.name)
        
        # Remove se existir
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        
        # Clona
        repo_url = f"https://{self.github_token}@github.com/{repo.full_name}.git"
        
        try:
            git_repo = Repo.clone_from(repo_url, repo_path)
        except:
            # Se repo vazio, inicia novo
            os.makedirs(repo_path)
            git_repo = Repo.init(repo_path)
            origin = git_repo.create_remote('origin', repo_url)
        
        # Criar arquivos
        for file_path, content in code_files.items():
            full_path = os.path.join(repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Commit e push
        git_repo.git.add(A=True)
        git_repo.index.commit("🤖 Initial commit by Gemini Agent")
        
        try:
            git_repo.git.push('--set-upstream', 'origin', 'main')
        except:
            try:
                git_repo.git.push('--set-upstream', 'origin', 'master')
            except:
                pass
        
        return repo_path
    
    def _deploy_project(self, repo, repo_path):
        """Deploy automático (Vercel ou GitHub Pages)"""
        
        # Opção 1: Vercel (se token configurado)
        if self.vercel_token:
            try:
                import requests
                response = requests.post(
                    'https://api.vercel.com/v13/deployments',
                    headers={'Authorization': f'Bearer {self.vercel_token}'},
                    json={
                        'name': repo.name,
                        'gitSource': {
                            'type': 'github',
                            'repo': repo.full_name,
                            'ref': 'main'
                        }
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return f"https://{data['url']}"
            except:
                pass
        
        # Opção 2: GitHub Pages (fallback)
        try:
            repo.enable_pages(source="gh-pages", path="/")
            return f"https://{repo.owner.login}.github.io/{repo.name}"
        except:
            pass
        
        # Retorna URL do repo se deploy falhar
        return repo.html_url

# ============ CLI ============

def main():
    if len(sys.argv) < 2:
        print("""
🤖 GEMINI AUTONOMOUS AGENT
        
Uso:
  python agent.py create "descrição do projeto" nome-do-projeto
  
Exemplos:
  python agent.py create "app de delivery de pizzaria com carrinho" pizzaria-delivery
  python agent.py create "landing page para academia com formulário" landing-academia
  python agent.py create "dashboard de vendas com gráficos" dashboard-vendas
        """)
        return
    
    command = sys.argv[1]
    
    if command == "create":
        description = sys.argv[2]
        project_name = sys.argv[3] if len(sys.argv) > 3 else f"project-{int(time.time())}"
        
        agent = AutonomousAgent()
        result = agent.create_project_from_description(description, project_name)
        
        print("\n✅ Processo completo!")
        print(f"\n🔗 Acesse seu projeto em: {result['deploy_url']}")

if __name__ == "__main__":
    main()