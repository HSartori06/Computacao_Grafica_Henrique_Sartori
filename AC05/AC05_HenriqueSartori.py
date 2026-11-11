# -*- coding: utf-8 -*-
"""
AC05 — Henrique Sartori | Materiais PBR e Texturas | Blender 4.5 LTS
==================================================================
EXECUÇÃO
  1. Abra, no Blender, a cena FINAL da AC04 (arquivo com ~4 MB).
  2. Deixe a pasta assets_CC0 ao lado do arquivo da AC04, se possível.
  3. Scripting > Open > AC05_HenriqueSartori.py > Alt+P.

O SCRIPT:
  * NÃO apaga a cena e NÃO sobrescreve a AC04.
  * Preserva câmera, luzes, palavra Ibmec, 3 objetos autorais e cenografia.
  * Aplica 3 novos materiais PBR, com UVs nos dois objetos texturizados.
  * Reutiliza mapas Poly Haven (incluídos no .blend ou em assets_CC0).
  * Cria uma textura de madeira AUTORAL, gerada por código e salva em PNG.
  * Empacota recursos, salva AC05_HenriqueSartori.blend e renderiza PNG.
  * Escreve AC05_Relatorio.md, que deve ser revisado após o render.

FALTAM DUAS CAPTURAS MANUAIS PARA ENTREGA (instruções no relatório):
  - AC05_ShaderEditor.png: nós de Base Color, Roughness e Normal.
  - AC05_UVEditor.png: mapa UV da plataforma.

RECURSOS
  https://polyhaven.com/a/metal_plate — licença CC0
  Kenney Space Kit já presente na cena AC04 — licença CC0

IMPORTANTE: Foi validada a sintaxe Python; a cena deve ser executada e
conferida no Blender 4.5 LTS do usuário.
"""

import bpy
import math
import os
import random
from array import array
from pathlib import Path

# --------------------------- CONFIGURAÇÃO ---------------------------
RENDERIZAR = True
RESOLUCAO = (1600, 900)
AMOSTRAS = 64
TAMANHO_MADEIRA = 512
NOME_SAIDA = 'AC05_HenriqueSartori.blend'
NOME_RENDER = 'AC05_RenderFinal.png'
NOME_RELATORIO = 'AC05_Relatorio.md'
NOME_MADEIRA = 'AC05_Madeira_Autoral_Albedo.png'

# ---------------------- VERIFICAÇÕES DE SEGURANÇA --------------------
if not bpy.data.filepath:
    raise RuntimeError('Abra e salve o .blend FINAL da AC04 antes de executar a AC05.')

origem = Path(bpy.data.filepath).resolve()
pasta = origem.parent
assets_dir = pasta / 'assets_CC0'
scene = bpy.context.scene

if origem.stem.lower().startswith('ac05'):
    raise RuntimeError('Abra a AC04, não uma AC05 já editada. O script cria uma CÓPIA independente.')

nomes = ('Obj_PlataformaAscensao', 'Obj_PortalFuturo', 'Obj_TorresConexao', 'Marca_Ibmec')
ausentes = [x for x in nomes if bpy.data.objects.get(x) is None]
if ausentes:
    raise RuntimeError('Não é a AC04 correta. Objetos ausentes: ' + ', '.join(ausentes))

plataforma = bpy.data.objects['Obj_PlataformaAscensao']
portal = bpy.data.objects['Obj_PortalFuturo']
torres = bpy.data.objects['Obj_TorresConexao']
marca = bpy.data.objects['Marca_Ibmec']
if not all(o.type == 'MESH' for o in (plataforma, portal, torres)):
    raise RuntimeError('Os três objetos autorais devem ser malhas (MESH).')
if scene.camera is None:
    raise RuntimeError('A câmera principal da AC04 não foi encontrada.')

saida = pasta / NOME_SAIDA
if saida.exists():
    # Não sobrescreve entregas anteriores.
    i = 2
    while (pasta / f'AC05_HenriqueSartori_{i}.blend').exists():
        i += 1
    saida = pasta / f'AC05_HenriqueSartori_{i}.blend'


def imagem_existente(sufixo):
    """Encontra mapas já empacotados na AC04 ou em assets_CC0."""
    sufixo = sufixo.lower()
    for img in bpy.data.images:
        nome = (img.name + ' ' + os.path.basename(img.filepath or '')).lower()
        if 'metal_plate_' + sufixo + '_1k' in nome:
            try:
                if img.packed_file is not None or (img.filepath and Path(bpy.path.abspath(img.filepath)).is_file()):
                    return img
            except Exception:
                pass
    for filename in (f'metal_plate_{sufixo}_1k.jpg', f'polyhaven_metal_plate_{sufixo}_1k.jpg'):
        arq = assets_dir / filename
        if arq.is_file():
            return bpy.data.images.load(str(arq), check_existing=True)
    return None


img_metal_cor = imagem_existente('diff')
img_metal_rug = imagem_existente('rough')
img_metal_nor = imagem_existente('nor_gl')
faltam = [nom for nom, img in [('Base Color',img_metal_cor),('Roughness',img_metal_rug),('Normal',img_metal_nor)] if img is None]
if faltam:
    raise FileNotFoundError('Faltam mapas Poly Haven: ' + ', '.join(faltam)
                            + '. Coloque os três JPGs metal_plate_*_1k em: ' + str(assets_dir)
                            + '. Nenhuma alteração foi feita na cena.')

for img, espaco in ((img_metal_cor,'sRGB'), (img_metal_rug,'Non-Color'), (img_metal_nor,'Non-Color')):
    img.colorspace_settings.name = espaco

print('[AC05] Cena AC04 carregada:', origem)
print('[AC05] Mapas externos encontrados, iniciando atualização de materiais.')

# ----------------------- COLEÇÃO AUXILIAR ---------------------------
col = bpy.data.collections.get('AC05_Materiais_Texturas')
if col is None:
    col = bpy.data.collections.new('AC05_Materiais_Texturas')
    principal = bpy.data.collections.get('AP1_Ibmec_Conceito')
    (principal or scene.collection).children.link(col)

# --------------------------- UV AUTOMÁTICO --------------------------
def uv_smart(obj, nome_uv):
    """Smart UV Project para base poligonal; uma UV por loop/canto."""
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name=nome_uv)
    else:
        obj.data.uv_layers.active.name = nome_uv
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    try:
        bpy.ops.uv.smart_project(island_margin=0.025)
    except Exception:
        # Mapeamento planar/cilíndrico seguro, sem dependência de contexto da UV.
        bpy.ops.object.mode_set(mode='OBJECT')
        uv = obj.data.uv_layers.active
        for p in obj.data.polygons:
            for li in p.loop_indices:
                v = obj.data.vertices[obj.data.loops[li].vertex_index].co
                uv.data[li].uv = (v.x/12.0 + 0.5, v.y/12.0 + 0.5) if abs(p.normal.z) > .7 else (v.x/12.0 + .5, v.z/8.0)
    finally:
        if obj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    return obj.data.uv_layers.active.name


def uv_torre_cilindro(obj, nome_uv):
    """Desdobramento UV cilíndrico para manter os veios da madeira verticais."""
    mesh = obj.data
    uv = mesh.uv_layers.get(nome_uv) or mesh.uv_layers.new(name=nome_uv)
    mesh.uv_layers.active = uv
    cx, cy = -6.33, 0.30  # centro da torre original no mesh da AC04
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            p = mesh.vertices[mesh.loops[li].vertex_index].co
            if abs(poly.normal.z) > 0.75:
                u, v = (p.x - cx + .85)/1.70, (p.y - cy + .85)/1.70
            else:
                u = (math.atan2(p.y-cy, p.x-cx) + math.pi) / (2 * math.pi)
                v = min(1.0, max(0.0, p.z/7.1))
            uv.data[li].uv = (u, v)
    return uv.name


uv_plataforma = uv_smart(plataforma, 'UV_AC05_Plataforma_Smart')
uv_torres = uv_torre_cilindro(torres, 'UV_AC05_Torres_Cilindrico')

# ------------------------- MAPA DE MADEIRA --------------------------
# Cria imagem sRGB com veios irregulares: não exige baixar nova biblioteca.
# A textura é salva em assets_CC0 e depois EMPACOTADA no blend de entrega.
assets_dir.mkdir(parents=True, exist_ok=True)
madeira_path = assets_dir / NOME_MADEIRA

madeira = bpy.data.images.get('AC05_Madeira_Autoral_Imagem')
if madeira is None:
    madeira = bpy.data.images.new('AC05_Madeira_Autoral_Imagem', width=TAMANHO_MADEIRA,
                                 height=TAMANHO_MADEIRA, alpha=True, float_buffer=False)

rng = random.Random(2605)
n = TAMANHO_MADEIRA
pixels = array('f')
# grain control: variação longitudinal suave + veios e poros finos.
for y in range(n):
    fy = y / n
    sin_y = math.sin(2 * math.pi * fy * 4)
    for x in range(n):
        fx = x / n
        w = fx + .033 * sin_y + .012 * math.sin(fy * 32 + fx * 11)
        vao = .5 + .5 * math.sin(2*math.pi*11*w + .22*math.sin(2*math.pi*fy*3))
        fino = .5 + .5 * math.sin(2*math.pi*57*w)
        micro = (rng.random()-.5)*.027
        # carvalho/nogueira escurecida, contraste visível sem parecer plástico
        lum = max(0.05, min(1, .23 + .23*vao + .07*fino + micro))
        pixels.extend((lum*.91, lum*.49, lum*.245, 1.0))

madeira.pixels.foreach_set(pixels)
madeira.update()
madeira.filepath_raw = str(madeira_path)
madeira.file_format = 'PNG'
madeira.save()
madeira.colorspace_settings.name = 'sRGB'

# ----------------------- HELPERS DE MATERIAIS ------------------------
def material_novo(nome, cor, metal, rough):
    mat = bpy.data.materials.get(nome) or bpy.data.materials.new(nome)
    mat.use_nodes = True
    mat.diffuse_color = (*cor, 1)
    nd = mat.node_tree.nodes
    nd.clear()
    links = mat.node_tree.links
    out = nd.new('ShaderNodeOutputMaterial'); out.location=(700,130)
    bsdf = nd.new('ShaderNodeBsdfPrincipled'); bsdf.location=(370,130)
    bsdf.inputs['Base Color'].default_value=(*cor,1)
    bsdf.inputs['Metallic'].default_value=metal
    bsdf.inputs['Roughness'].default_value=rough
    links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    return mat,nd,links,bsdf


def conectar_uv(nd, links, uvname, escala=(1,1,1)):
    u = nd.new('ShaderNodeUVMap'); u.location=(-1050,-90)
    u.uv_map = uvname
    u.label = 'UV EDITOR: ' + uvname
    m = nd.new('ShaderNodeMapping'); m.location=(-830,-90)
    m.inputs['Scale'].default_value = escala
    links.new(u.outputs['UV'], m.inputs['Vector'])
    return m.outputs['Vector']


def img_node(nd,links,nome,imagem,vec, pos):
    node = nd.new('ShaderNodeTexImage'); node.location = pos
    node.label=nome
    node.image = imagem
    node.extension='REPEAT'
    links.new(vec,node.inputs['Vector'])
    return node


# 1) METAL DA PLATAFORMA: três mapas (Color, Roughness, Normal)
metal, nodes,links,bsdf = material_novo('MAT_AC05_Metal_Plataforma_PolyHaven',(.68,.76,.86),.86,.32)
vec = conectar_uv(nodes,links,uv_plataforma,(1.05,1.05,1))
tex_cor = img_node(nodes,links,'01 | Poly Haven / Base Color / sRGB',img_metal_cor,vec,(-600,440))
tex_rug = img_node(nodes,links,'02 | Poly Haven / Roughness / Non-Color',img_metal_rug,vec,(-600,80))
tex_nor = img_node(nodes,links,'03 | Poly Haven / Normal GL / Non-Color',img_metal_nor,vec,(-600,-260))

# Reduz visualmente a saturação do metal, sem eliminar detalhe de imagem.
mix = nodes.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.location=(-15,460)
mix.inputs[0].default_value=.32
mix.inputs[2].default_value=(.68,.82,1.0,1.0)
links.new(tex_cor.outputs['Color'],mix.inputs[1])
links.new(mix.outputs['Color'],bsdf.inputs['Base Color'])

ajuste = nodes.new('ShaderNodeMapRange'); ajuste.location=(-15,40)
ajuste.label='Faixa de rugosidade 0.18 a 0.62'
ajuste.inputs['From Min'].default_value=0
ajuste.inputs['From Max'].default_value=1
ajuste.inputs['To Min'].default_value=.18
ajuste.inputs['To Max'].default_value=.62
links.new(tex_rug.outputs['Color'],ajuste.inputs['Value'])
links.new(ajuste.outputs['Result'],bsdf.inputs['Roughness'])
normal = nodes.new('ShaderNodeNormalMap');normal.location=(-15,-260)
normal.inputs['Strength'].default_value=.38
normal.space='TANGENT'
links.new(tex_nor.outputs['Color'],normal.inputs['Color'])
links.new(normal.outputs['Normal'],bsdf.inputs['Normal'])

# 2) MADEIRA DAS TORRES: imagem gerada por código, metallic=0
wood,nodes,links,bsdf = material_novo('MAT_AC05_Madeira_Torres_Autoral',(.28,.12,.05),0.0,.44)
vec=conectar_uv(nodes,links,uv_torres,(1.8,2.6,1))
tex_wood=img_node(nodes,links,'Imagem / madeira gerada proceduralmente / sRGB',madeira,vec,(-640,240))
links.new(tex_wood.outputs['Color'],bsdf.inputs['Base Color'])
noise=nodes.new('ShaderNodeTexNoise');noise.location=(-640,-90)
noise.inputs['Scale'].default_value=24.0
noise.inputs['Detail'].default_value=2.0
links.new(vec,noise.inputs['Vector'])
bump=nodes.new('ShaderNodeBump');bump.location=(-250,-110)
bump.inputs['Strength'].default_value=.13
bump.inputs['Distance'].default_value=.035
links.new(noise.outputs['Fac'],bump.inputs['Height'])
links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])

# 3) ESPELHO DO PORTAL: Principled BSDF metal polido, sem imagem.
mirror,nodes,links,bsdf = material_novo('MAT_AC05_Espelho_Portal',(.68,.82,.97),1.0,.065)
bsdf.inputs['Coat Weight'].default_value=.22
bsdf.inputs['Coat Roughness'].default_value=.08
bsdf.label='ESPELHO / superfície metálica muito lisa'

for obj,mat in ((plataforma,metal),(torres,wood),(portal,mirror)):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.material_index=0
    obj['AC05_Material'] = mat.name

# Integridade do conjunto: não altera materiais, posição ou geometria da marca Ibmec.
# Não altera a câmera nem as luzes da AC04, para comparação consistente.
scene['AC05_Etapa'] = 'PBR/UV/BaseColor/Roughness/Normal'
scene['AC05_Texturas_Externas'] = 'Poly Haven Metal Plate (CC0)'
scene['AC05_Textura_Autoral'] = 'AC05_Madeira_Autoral_Albedo.png (gerada em Python)'

# Ativa a plataforma, para facilitar as capturas no Shader/UV Editor.
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
plataforma.select_set(True)
bpy.context.view_layer.objects.active=plataforma
scene.frame_set(360)

# Render PBR, mantendo enquadramento, iluminação e marca original.
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x,scene.render.resolution_y = RESOLUCAO
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=False
if hasattr(scene,'eevee') and hasattr(scene.eevee,'taa_render_samples'):
    scene.eevee.taa_render_samples=AMOSTRAS

# Texturas locais incluídas NO arquivo Blender para independência de pastas externas.
try:
    bpy.ops.file.pack_all()
except Exception as exc:
    print('[AC05] AVISO ao empacotar:', exc)

scene.render.filepath=str(pasta/NOME_RENDER)
bpy.ops.wm.save_as_mainfile(filepath=str(saida),check_existing=False)
print('[AC05] Arquivo Blender salvo:',saida)

relatorio = pasta / NOME_RELATORIO
relatorio.write_text(f'''# AC05 — Evolução da Cena: Materiais PBR e Texturas

**Aluno:** Henrique Sartori  
**Software:** Blender 4.5 LTS  
**Projeto:** Ibmec: Arquitetura do Futuro  
**Arquivo:** `{saida.name}`  
**Base:** cópia da AC04, com câmera, iluminação, cenografia e composição preservadas.

## Materiais dos três objetos autorais

| Objeto | Material | Base Color / cor | Metallic | Roughness | Textura de imagem |
|---|---|---|---:|---:|---|
| `Obj_PlataformaAscensao` | `MAT_AC05_Metal_Plataforma_PolyHaven` | Poly Haven `metal_plate_diff_1k.jpg`, com tonalização azul suave | 0.86 | Mapa de rugosidade remapeado de 0.18 a 0.62 (base 0.32) | Sim |
| `Obj_TorresConexao` | `MAT_AC05_Madeira_Torres_Autoral` | Imagem de veios de madeira escura gerada em Python | 0.00 | 0.44 | Sim |
| `Obj_PortalFuturo` | `MAT_AC05_Espelho_Portal` | RGB (0.68, 0.82, 0.97), aparência de metal cromado frio | 1.00 | 0.065 | Não, cor sólida PBR |

O primeiro material simula metal de superfície ligeiramente irregular. O segundo representa madeira escurecida em um ambiente de arquitetura tecnológica. O terceiro utiliza rugosidade muito baixa e alta metalicidade para um acabamento espelhado. **Todos usam Principled BSDF.**

## Ligações dos mapas de textura

**Plataforma — três mapas de imagem Poly Haven:**

- `UV Map → Mapping → Image Texture (Base Color, sRGB) → Mix Color (leve tonalização) → Principled BSDF / Base Color`.
- `UV Map → Mapping → Image Texture (Roughness, Non-Color) → Map Range (0.18–0.62) → Principled BSDF / Roughness`.
- `UV Map → Mapping → Image Texture (Normal GL, Non-Color) → Normal Map (Strength 0.38) → Principled BSDF / Normal`.

**Torres:** `UV Map → Mapping → Image Texture (madeira, sRGB) → Base Color`. Um `Noise Texture` procedimental alimenta `Bump → Normal` para relevo discreto. Esse relevo **não** é apresentado como mapa normal de imagem.

**Portal:** Principled BSDF de metal altamente polido, sem textura de imagem, com Coat Weight 0.22 e Coat Roughness 0.08.

## UV Mapping

- **Plataforma:** *Smart UV Project*, margem de ilha 0.025. O método distribui as superfícies poligonais por ilhas para reduzir distorções nas paredes laterais e nos degraus; o material utiliza UV Map explícito.
- **Torres:** mapeamento cilíndrico programático, com orientação longitudinal dos veios. As faces horizontais recebem projeção plana; as laterais recebem U angular e V proporcional à altura.
- O mapa UV é aplicado à geometria original da torre; a segunda torre é reproduzida por Mirror Modifier.
- Conferir visualmente o UV Editor e ajustar ilhas caso sejam observadas emendas ou deformações excessivas.

## Iluminação e composição

As luzes Area e a câmera da AC04 foram preservadas. Espera-se que a iluminação realce as irregularidades do metal, a textura menos reflexiva da madeira e os highlights concentrados do portal espelhado. **Após abrir o PNG, confirmar e registrar os efeitos realmente observados.**

A marca **Ibmec** mantém o objeto, a tipografia e o material da AC04, sem aplicação de madeira, metal texturizado ou normal map sobre as letras.

## Fontes e licenças

- **Poly Haven — Metal Plate:** https://polyhaven.com/a/metal_plate — **CC0**, mapas Base Color, Roughness e Normal GL, resolução 1K. Usado na plataforma.
- **Madeira autoral:** textura PNG gerada pelo código `AC05_HenriqueSartori.py`, sem biblioteca externa. Usada nas torres.
- **Kenney Space Kit:** https://kenney.nl/assets/space-kit — **CC0**, modelos de apoio importados na AC04 e preservados nesta evolução.
- O script executa `Pack Resources` para incorporar ao arquivo `.blend` os mapas de imagem utilizados.

## Entregáveis visuais pendentes de captura no Blender

1. `AC05_RenderFinal.png` — render pela câmera principal, gerado pelo script.
2. `AC05_ShaderEditor.png` — captura REAL dos nós do material da plataforma no Shader Editor (mostrar Base Color, Roughness, Normal Map e Principled BSDF).
3. `AC05_UVEditor.png` — captura REAL do UV Editor com `Obj_PlataformaAscensao` em Edit Mode e a imagem `metal_plate_diff_1k.jpg` exibida.

**Revisão antes da entrega:** verificar imagem final, orientação da madeira, UVs, legibilidade do Ibmec e disponibilidade de todas as texturas no `.blend` reaberto.
''',encoding='utf-8')

# O relatório é escrito antes do render; se o render falhar, ele continua disponível.
if RENDERIZAR:
    bpy.ops.render.render(write_still=True)
    print('[AC05] Render salvo:',pasta/NOME_RENDER)


print('\n[AC05] CONCLUÍDO. Pastas e arquivos:')
for p in (saida,pasta/NOME_RENDER,relatorio,madeira_path):
    print('   ',p)
print('[AC05] Restam apenas as capturas reais do Shader Editor e UV Editor.')
