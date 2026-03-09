# Drive Organizador 📚

Script Python para organizar automaticamente livros em um Google Drive, classificando-os por categoria e linguagem de programação.

## Funcionalidades

✅ Autenticação OAuth2 com Google Drive  
✅ Cópia automática de arquivos do Drive  
✅ Classificação por categoria:
- Programação (Python, Java, JavaScript, C++, C#, Go, Rust, SQL, Excel, etc.)
- Matematica
- Segurança (Pentest, Hacker, Criptografia)
- Outros

✅ Criação automática de pastas por linguagem dentro de cada categoria  
✅ Tratamento de erros robusto  
✅ Resumo detalhado ao final  

## Instalação

1. Instale as dependências:
```bash
python -m pip install -r requirements.txt
```

2. Certifique-se de que `credentials.json` está na pasta do projeto (obtido do Google Cloud Console).

## Uso

Execute o script:

```bash
python organiza_livros.py
```

### Primeira Execução
- Na primeira execução, um navegador abrirá pedindo autorização para acessar o Google Drive.
- Faça login com sua conta do Google e autorize o acesso.
- Um arquivo `token.json` será criado automaticamente (salva as credenciais).
- Em seguida, o navegador abrirá o Google Drive para você navegar e copiar o link da pasta com os livros.

### Trocar de Conta
Para usar outra conta do Google (ex: com mais espaço):
```bash
# No Windows (PowerShell):
Remove-Item token.json
# No Linux/Mac:
rm token.json
python organiza_livros.py
```

## Estrutura de Pastas Criada

O script criará a seguinte estrutura no root do seu Drive:

```
📁 Programação/
  📁 Python/
  📁 Java/
  📁 JavaScript/
  📁 C++/
  📁 C#/
  📁 Go/
  📁 Rust/
  📁 SQL/
  📁 Excel/
  📁 Geral/
📁 Matemática/
  📁 Álgebra/
  📁 Geometria/
  📁 Cálculo/
  📁 Probabilidade/
  📁 Geometria Analítica/
  📁 Topologia/
  📁 Análise/
  📁 Geral/
📁 Segurança/
  📁 Pentest/
  📁 Hacker/
  📁 Criptografia/
  📁 Redes/
  📁 Forense/
  📁 Geral/
📁 Outros/
  📁 Geral/
```

## Classificação

Os livros são classificados automaticamente pelo **nome do arquivo**. Exemplos:

- `"Python for Excel.pdf"` → Programacao/Python/
- `"Use a cabeça Java.pdf"` → Programacao/Java/
- `"Estatística Descritiva.pdf"` → Matematica/Geral/
- `"Pentest Metodologia.pdf"` → Seguranca/Pentest/

## Palavras-Chave de Classificação

Você pode editar as palavras-chave no arquivo `organiza_livros.py` na seção `KEYWORDS` para ajustar a classificação:

```python
KEYWORDS = {
    'Programação': {
        'Python': [r'python', r'django', r'flask', r'pandas'],
        'Java': [r'\bjava\b', r'spring', r'android'],
        # ... mais linguagens
    },
    # ... mais categorias
}
```

## Dependências

- `google-api-python-client`: Acesso à API do Google Drive
- `google-auth-oauthlib`: Autenticação OAuth2
- `google-auth-httplib2`: Autenticação HTTP

Instaladas via `requirements.txt`.

## Troubleshooting

### Erro: "Este app não passou na verificação do Google"
**Solução:** Adicione seu e-mail como Test User no Google Cloud Console → OAuth consent screen → Test users.

### Erro de conexão/timeout
**Solução:** Verifique sua conexão com a internet e tente novamente. Para arquivos grandes, aguarde mais tempo.

### Token.json corrompido
**Solução:** Delete o arquivo e execute novamente para gerar um novo token.

### Pasta não encontrada
**Solução:** Verifique se o ID da pasta está correto e se sua conta tem acesso a ela.

## Contato

Se tiver problemas ou sugestões, entre em contato! 📧

---

**Versão:** 1.0  
**Última atualização:** 8 de março de 2026
