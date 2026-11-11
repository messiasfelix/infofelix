#!/usr/bin/env python3
"""Gerador do InfoFelix para GitHub Pages: URLs próprias e Pages CMS intacto."""
from pathlib import Path
import json, shutil, re, html, unicodedata, sys
from urllib.parse import quote
import xml.etree.ElementTree as ET

SOURCE=Path(__file__).resolve().parents[1]
DEST=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else SOURCE/'_site'
BASE='https://messiasfelix.github.io/infofelix/'
ALIAS={
 'guia-fundamentos':'tensao-corrente-e-resistencia',
 'guia-componentes':'como-funciona-um-mosfet',
 'guia-cursos':'eletronica-basica-aula-1',
 'guia-diagnosticos':'fonte-de-tv-sem-tensao-de-saida',
 'guia-esquemas':'leitura-de-esquemas-eletricos',
 'guia-ferramentas':'como-medir-tensao',
 'guia-multimetro':'como-medir-tensao-corretamente',
 'guia-fonte':'fonte-standby',
 'guia-circuito':'identificando-componentes-em-esquemas',
}
CATEGORIES={
 'biblioteca':'Biblioteca', 'anotacoes':'Todas as anotações',
 'fundamentos':'Fundamentos de eletrônica','componentes':'Componentes eletrônicos',
 'cursos':'Cursos de eletrônica','diagnosticos':'Diagnósticos de bancada',
 'esquemas':'Esquemas elétricos','ferramentas':'Ferramentas e medições',
}

def slug(value):
    result=unicodedata.normalize('NFKD',str(value))
    result=''.join(c for c in result if not unicodedata.combining(c))
    return re.sub(r'^-+|-+$','',re.sub(r'-+','-',re.sub(r'[^a-z0-9-]','-',result.lower())))

def article_path(item):
    prefix={'aula':'aulas','diagnostico':'diagnosticos'}.get(item.get('tipo'),'artigos')
    key=ALIAS.get(item.get('id'),slug(item.get('id')))
    if not key: raise ValueError('Anotação sem identificador válido')
    return f'{prefix}/{key}/'

def e(value): return html.escape(str(value or ''),quote=True)

if DEST.exists(): shutil.rmtree(DEST)
DEST.mkdir(parents=True)
for name in ('index.html','css','js','imagens','dados'):
    src=SOURCE/name
    if not src.exists(): raise RuntimeError(f'Arquivo/pasta necessário ausente: {name}')
    if src.is_dir(): shutil.copytree(src,DEST/name)
    else: shutil.copy2(src,DEST/name)
(DEST/'.nojekyll').write_text('',encoding='utf-8')
items=json.loads((SOURCE/'dados/conteudos.json').read_text(encoding='utf-8'))
if not isinstance(items,list): raise TypeError('dados/conteudos.json precisa ser lista')
template=(SOURCE/'index.html').read_text(encoding='utf-8')
# A raiz mantém o HTML original, com CSS e JS separados.
urls=[BASE]
used=set()

def page(path,title,description,initial_markup):
    depth=len([p for p in path.split('/') if p]); rel='../'*depth
    markup=template.replace('<head>',f'<head><base href="{rel}">',1)
    markup=markup.replace('<title>InfoFelix — Biblioteca de Eletrônica</title>',f'<title>{e(title)} — InfoFelix</title>',1)
    markup=markup.replace('content="InfoFelix: estudos, anotações e diagnósticos de eletrônica."',f'content="{e(description)[:155]}"',1)
    markup=markup.replace('<main id="app" tabindex="-1"></main>',f'<main id="app" tabindex="-1">{initial_markup}</main>',1)
    # Canonical está no próprio documento HTML e não exige configurações adicionais.
    markup=markup.replace('</head>',f'<link rel="canonical" href="{BASE+path}"></head>',1)
    target=DEST/path/'index.html'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(markup,encoding='utf-8')
    urls.append(BASE+path)

for route,title in CATEGORIES.items():
    shown=items if route in ('biblioteca','anotacoes') else [x for x in items if x.get('categoria')==route]
    links=''.join(f'<p><a href="{article_path(x)}">{e(x.get("titulo"))}</a></p>' for x in shown)
    page(route+'/',title,f'{title}: estudos e conteúdos técnicos InfoFelix',f'<section class="page-top"><h1>{e(title)}</h1></section><section class="article-body">{links}</section>')

for item in items:
    path=article_path(item)
    if path in used: raise ValueError(f'URLs duplicadas: {path}')
    used.add(path)
    title=item.get('titulo') or 'Sem título'
    summary=item.get('resumo') or ''
    image=item.get('imagem') or 'imagens/placa.webp'
    cat=item.get('categoria') or 'biblioteca'
    # O HTML completo fica na página gerada, mesmo se o JavaScript estiver desligado.
    body=f'<a class="back" href="{cat}/">← Voltar para {e(cat)}</a><article class="article"><img class="article-cover" src="{e(image)}" alt="Imagem ilustrativa de {e(title)}"><div class="article-body"><span class="tag">{e(cat)} · {e(item.get("data"))}</span><h1>{e(title)}</h1><p class="summary">{e(summary)}</p><div class="notice">Conteúdo educativo demonstrativo. Confira documentação e procedimentos de segurança antes de aplicar na bancada.</div><div class="richcontent">{item.get("conteudo") or ""}</div><a class="back" href="{cat}/">← Voltar à categoria</a></div></article>'
    page(path,title,summary,body)

# Busca é interativa no navegador, com URL acessível.
page('pesquisa/','Pesquisar anotações','Pesquisa de conteúdos de eletrônica InfoFelix','<section class="page-top"><h1>Pesquisar conteúdo</h1><p>Digite um termo no campo de busca acima.</p></section>')

# Ajuda visual em caso de página inexistente. Não substituir links atuais sem critério.
(DEST/'404.html').write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Página não encontrada — InfoFelix</title><body style="font:18px system-ui;padding:10vh 8vw;max-width:700px"><h1>Página não encontrada</h1><p>Esta anotação pode ter sido movida ou excluída.</p><p><a href="/infofelix/">Voltar para o InfoFelix</a></p></body></html>',encoding='utf-8')

sitemap=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
for u in urls: ET.SubElement(ET.SubElement(sitemap,'url'),'loc').text=u
(DEST/'sitemap.xml').write_bytes(ET.tostring(sitemap,encoding='utf-8',xml_declaration=True))
(DEST/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+BASE+'sitemap.xml\n',encoding='utf-8')
print(f'Geradas {len(urls)} URLs em {DEST}; {len(items)} anotações do JSON atual')
