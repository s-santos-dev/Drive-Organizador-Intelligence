import argparse
import io
import os
import re
import tempfile
import webbrowser
from collections import defaultdict

from googleapiclient.http import MediaIoBaseDownload

from drive_auth import get_drive_service

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    from ebooklib import epub
except Exception:
    epub = None


KEYWORDS = {
    'Programação': {
        'Python': [r'python', r'django', r'flask', r'pandas', r'numpy', r'scipy', r'jupyter', r'anaconda', r'pycharm'],
        'Java': [r'\bjava\b', r'spring', r'android', r'maven', r'gradle', r'hibernate', r'jpa'],
        'JavaScript': [r'javascript', r'node\.?js', r'react', r'vue', r'angular', r'typescript', r'express', r'webpack'],
        'C++': [r'c\+\+', r'cpp', r'boost', r'qt'],
        'C#': [r'c#', r'csharp', r'\.net', r'asp\.net', r'unity', r'xamarin'],
        'PHP': [r'php', r'laravel', r'wordpress', r'symfony'],
        'Ruby': [r'ruby', r'rails', r'sinatra'],
        'Go': [r'\bgo\b', r'golang', r'gin', r'echo'],
        'Rust': [r'rust', r'cargo', r'tokio'],
        'Kotlin': [r'kotlin'],
        'Swift': [r'swift', r'ios'],
        'SQL': [r'sql', r'mysql', r'postgresql', r'oracle', r'tsql', r'database', r'nosql', r'mongodb'],
        'Excel': [r'excel', r'vba', r'power bi', r'dashboard', r'spreadsheet'],
        'Geral': [r'programa', r'algoritm', r'dados', r'structure', r'design pattern', r'oop', r'desenvolvimento']
    },
    'Matemática': {
        'Álgebra': [r'álgebra', r'polinômio', r'equação', r'matriz', r'determinante', r'linear', r'conjunto', r'lógica'],
        'Geometria': [r'geometr', r'trigonometria', r'trigono', r'seno', r'cosseno', r'plano', r'espaço'],
        'Cálculo': [r'cálculo', r'derivada', r'integral', r'limite', r'continuidade', r'função', r'série'],
        'Probabilidade': [r'probabilidade', r'estatíst', r'distribuição', r'variância', r'média', r'hipótese', r'regressão', r'correlação'],
        'Geometria Analítica': [r'analítica', r'cônica', r'parametr'],
        'Topologia': [r'topologia', r'espaço topológico'],
        'Análise': [r'análise', r'real', r'complexa'],
        'Geral': [r'matemat', r'cálculo', r'número', r'aritmética']
    },
    'Segurança': {
        'Pentest': [r'pentest', r'penetration', r'teste segurança', r'vulnerability', r'scanner', r'burp', r'metasploit'],
        'Hacker': [r'hacker', r'hack', r'exploit', r'payload', r'shellcode', r'reverse', r'engineering'],
        'Criptografia': [r'criptogra', r'cipher', r'encrypt', r'decrypt', r'aes', r'rsa', r'hash', r'sha', r'md5'],
        'Redes': [r'rede', r'tcp.?ip', r'protocolo', r'firewall', r'proxy', r'vpn', r'ddos'],
        'Forense': [r'forense', r'forensic', r'investigação'],
        'Geral': [r'seguranç', r'invas', r'crack', r'security', r'vulnerabilidade', r'ataque']
    },
    'Outros': {
        'Geral': []
    }
}


def extract_text_from_pdf(path: str, max_pages: int = 2) -> str:
    if not PdfReader:
        return ''
    try:
        reader = PdfReader(path)
        text = []
        # extrai apenas as 2 primeiras páginas
        for i, p in enumerate(reader.pages[:max_pages]):
            try:
                text.append(p.extract_text() or '')
            except Exception:
                continue
        return '\n'.join(text)[:2000]  # Limita a 2000 caracteres
    except Exception:
        return ''


def extract_text_from_epub(path: str, max_chars: int = 2000) -> str:
    if not epub:
        return ''
    try:
        book = epub.read_epub(path)
        texts = []
        for item in book.get_items():
            if item.get_type() == epub.EpubHtml:
                try:
                    content = item.get_content().decode('utf-8')
                    # strip html tags
                    text = re.sub('<[^<]+?>', '', content)
                    texts.append(text)
                    if len('\n'.join(texts)) > max_chars:
                        break
                except Exception:
                    continue
        return '\n'.join(texts)[:max_chars]
    except Exception:
        return ''


def classify_text(text, filename):
    text_low = (text or '') + '\n' + filename
    text_low = text_low.lower()
    for category, subcats in KEYWORDS.items():
        if isinstance(subcats, dict):
            for subcat, patterns in subcats.items():
                for pat in patterns:
                    if re.search(pat, text_low):
                        return (category, subcat)
        else:
            # compatibilidade com formato antigo (lista)
            for pat in subcats:
                if re.search(pat, text_low):
                    return (category, 'Geral')
    return ('Outros', 'Geral')


def ensure_folder(service, name, parent_id='root'):
    # procura pasta com esse nome no parent
    q = "mimeType='application/vnd.google-apps.folder' and name='{}' and '{}' in parents and trashed=false".format(
        name.replace("'", "\\'"), parent_id)
    res = service.files().list(q=q, fields='files(id, name)').execute()
    files = res.get('files', [])
    if files:
        return files[0]['id']
    # cria
    body = {'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
    folder = service.files().create(body=body, fields='id').execute()
    return folder['id']


def download_file(service, file_id, dest_path, chunk_size=10*1024*1024):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request, chunksize=chunk_size)
    done = False
    retries = 0
    max_retries = 3
    while not done:
        try:
            status, done = downloader.next_chunk()
        except Exception as e:
            retries += 1
            if retries > max_retries:
                raise
            print(f'    Retry {retries}/{max_retries} para chunk...')
            continue


def copy_to_folder(service, file_id, name, folder_id):
    body = {'name': name, 'parents': [folder_id]}
    return service.files().copy(fileId=file_id, body=body).execute()


def list_files_in_folder(service, folder_id):
    files = []
    page_token = None
    q = "'{}' in parents and trashed=false".format(folder_id)
    while True:
        res = service.files().list(q=q, spaces='drive', fields='nextPageToken, files(id, name, mimeType)', pageToken=page_token).execute()
        files.extend(res.get('files', []))
        page_token = res.get('nextPageToken')
        if not page_token:
            break
    return files


def main():
    parser = argparse.ArgumentParser(description='Organiza livros em um Drive de destino por categorias simples.')
    parser.add_argument('--source', '-s', help='ID ou link da pasta/arquivo de origem no Drive.', default=None)
    parser.add_argument('--copy', dest='move', action='store_false', help='Se presente, não apaga a origem (default copia).')
    args = parser.parse_args()

    # Se não passou source, pergunta interativamente
    if not args.source:
        print('\n' + '='*70)
        print('🎯 BEM-VINDO AO DRIVE ORGANIZADOR 📚')
        print('='*70)
        print('\nEste script organiza livros do seu Google Drive por categoria e linguagem.')
        
        # Pede o link
        print('\n' + '-'*70)
        print('Insira o link da pasta ou arquivo no Google Drive que deseja organizar.')
        print('Exemplo: https://drive.google.com/drive/folders/1a2B3cD4e5F6g7H8I9J0 ou https://drive.google.com/file/d/ID/view')
        print('⚠️  Se for arquivo, será organizado individualmente.')
        drive_link = input('\n📁 Cole o link da pasta: ').strip().replace('"', '').replace("'", "")
        
        # Extrai ID do link
        if 'folders/' in drive_link:
            source_id = drive_link.split('folders/')[-1].split('?')[0]
            is_folder = True
        elif 'file/d/' in drive_link:
            source_id = drive_link.split('file/d/')[-1].split('/')[0]
            is_folder = False
        elif 'id=' in drive_link:
            source_id = drive_link.split('id=')[-1].split('&')[0]
            is_folder = True  # assume folder
        else:
            source_id = drive_link
            is_folder = True  # assume folder
        
        args.source = source_id
        print(f'✓ ID extraído: {source_id[:20]}...')
        is_folder = True
    
    # Se passou source via linha de comando, valida e extrai ID se necessário
    else:
        source_input = args.source.strip()
        if 'folders/' in source_input:
            src_id = source_input.split('folders/')[-1].split('?')[0]
            is_folder = True
        elif 'file/d/' in source_input:
            src_id = source_input.split('file/d/')[-1].split('/')[0]
            is_folder = False
        elif 'id=' in source_input:
            src_id = source_input.split('id=')[-1].split('&')[0]
            # Assume folder se não especificado
            is_folder = True
        else:
            # Assume que é ID direto de folder
            src_id = source_input
            is_folder = True
    print(f'\n📥 Listando arquivos da pasta "{src_id[:20]}..."')
    if is_folder:
        files = list_files_in_folder(service, src_id)
        if not files:
            print('❌ Pasta de origem vazia ou não encontrada.')
            return
    else:
        # Trata como um único arquivo
        try:
            file_info = service.files().get(fileId=src_id, fields='id, name, mimeType').execute()
            files = [file_info]
            print(f'✓ Arquivo único encontrado: {file_info["name"]}')
        except Exception as e:
            print(f'❌ Arquivo não encontrado ou erro: {str(e)}')
            return

    print(f'✓ {len(files)} arquivo(s) encontrado(s)')
    
    # cache de pastas criadas (categoria -> linguagem -> folder_id)
    folder_cache = {}
    summary = defaultdict(lambda: defaultdict(int))
    errors = []

    print('\n' + '='*70)
    print('🔄 INICIANDO ORGANIZAÇÃO...')
    print('='*70 + '\n')

    for i, f in enumerate(files, 1):
        fid = f['id']
        name = f.get('name', 'sem_nome')
        mime = f.get('mimeType', '')
        print(f'[{i}/{len(files)}] {name}...', end=' ', flush=True)
        
        text = ''
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(name)[1]) as tmp:
            tmp_path = tmp.name
        
        try:
            # tenta baixar e extrair texto (com timeout implícito de erro)
            try:
                download_file(service, fid, tmp_path)
                ext = os.path.splitext(name)[1].lower()
                if ext == '.pdf':
                    text = extract_text_from_pdf(tmp_path)
                elif ext in ('.epub',) and epub:
                    text = extract_text_from_epub(tmp_path)
                else:
                    # tenta PDF mesmo com outra extensão
                    if PdfReader:
                        text = extract_text_from_pdf(tmp_path)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f'(análise com erro: {str(e)[:20]})', end=' ', flush=True)
                # continua com classificação só pelo nome
            
            # classifica (categoria, linguagem)
            cat, lang = classify_text(text, name)
            
            # garante pastas categoria/linguagem
            if cat not in folder_cache:
                folder_cache[cat] = {}
            if lang not in folder_cache[cat]:
                cat_folder_id = ensure_folder(service, cat)
                lang_folder_id = ensure_folder(service, lang, parent_id=cat_folder_id)
                folder_cache[cat][lang] = lang_folder_id
            
            dest_folder = folder_cache[cat][lang]
            copy_to_folder(service, fid, name, dest_folder)
            summary[cat][lang] += 1
            print(f'✓ {cat}/{lang}')
        except KeyboardInterrupt:
            print('\n[Interrompido pelo usuário]')
            break
        except Exception as e:
            error_msg = f'{name}: {str(e)[:60]}'
            errors.append(error_msg)
            print(f'✗ {error_msg}')
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    print('\n' + '='*60)
    print('RESUMO DA ORGANIZAÇÃO:')
    print('='*60)
    for cat in sorted(summary.keys()):
        total_cat = sum(summary[cat].values())
        print(f'\n📁 {cat}: {total_cat} arquivo(s)')
        for lang in sorted(summary[cat].keys()):
            print(f'   └─ {lang}: {summary[cat][lang]}')
    if errors:
        print(f'\n⚠️  Arquivos com erro ({len(errors)}):')
        for err in errors[:10]:
            print(f'  - {err}')
        if len(errors) > 10:
            print(f'  ... e mais {len(errors)-10} erros')


if __name__ == '__main__':
    main()
