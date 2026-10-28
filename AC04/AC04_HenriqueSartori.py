# -*- coding: utf-8 -*-
"""
AC04 — HENRIQUE SARTORI | GERADOR UNIFICADO | Blender 4.5 LTS
================================================================
Um unico script substitui V2 (construcao do zero) + V3 (melhorias).
NAO precisa abrir o projeto da AP1 nem executar outro script.

ANTES DE EXECUTAR:
  1. Abra File > New > General no Blender 4.5 LTS.
  2. Salve essa cena vazia (por exemplo AC04_Base_Temporaria.blend) em
     D:/TRABALHO/COMPUTAÇÃO_GRAFICA.
  3. Garanta que a pasta assets_CC0 fique ao lado do .blend salvo:
       satelliteDish.glb; satelliteDish_large.glb; satelliteDish_detailed.glb
       metal_plate_diff_1k.jpg; metal_plate_rough_1k.jpg;
       metal_plate_nor_gl_1k.jpg
  4. Abra ESTE .py na aba Scripting e pressione Alt+P.

O SCRIPT LIMPA A CENA ABERTA EM MEMORIA. NAO APAGA ARQUIVOS DO WINDOWS.
Nunca sobrescreve um .blend de entrega preexistente. Gera:
  AC04_HenriqueSartori.blend   (se o nome estiver livre) ou
  AC04_HenriqueSartori_FINAL.blend / FINAL_2.blend ...
  AC04_RenderFinal.png
  AC04_Comparacao.png
  AC04_Relatorio.md

O codigo nao foi testado no Blender em nosso ambiente; foi verificado
por analise estatica e compilacao Python. Confirme os PNGs antes de entregar.

Kenney Space Kit (CC0): https://kenney.nl/assets/space-kit
Poly Haven Metal Plate (CC0): https://polyhaven.com/a/metal_plate
Os modelos externos sao auxiliares; os tres objetos autorais permanecem
plataforma, portal e torres. Phong/Blinn-Phong sao aproximacoes Principled BSDF.
"""

# Primeira verificacao: antes de apagar a cena, precisa haver um .blend salvo.
import bpy
if not bpy.data.filepath:
    raise RuntimeError(
        'Antes de rodar: File > Save As e salve uma cena NOVA na pasta '
        'COMPUTAÇÃO_GRAFICA, ao lado de assets_CC0.')
try:
    import numpy
except ImportError as exc:
    raise RuntimeError('O Python deste Blender precisa ter NumPy para criar o PNG comparativo.') from exc

import math
import os
import urllib.request
from pathlib import Path
from mathutils import Vector, Matrix

NOME = 'HenriqueSartori'
ALUNO = 'Henrique Sartori'
NOME_ARQUIVO = NOME
NOME_ALUNO = ALUNO
CAMINHO_FONTE_IBMEC = ''  # pode informar o caminho de uma fonte oficial autorizada
GERAR_RENDERS = False    # a imagem final e criada depois, apenas uma vez, na etapa integrada V3
RESOLUCAO_PERCENT = 75  # use 100 para renders finais em alta resolucao
SAMPLES_EEVEE = 32
RESOLUCAO_X = 1600
RESOLUCAO_Y = 900
PERCENTUAL_RENDER = RESOLUCAO_PERCENT
BAIXAR_ASSETS_EXTERNOS = False  # os seis arquivos ja estao na pasta assets_CC0
USAR_PROPS_KENNEY = True
USAR_TEXTURE_POLYHAVEN = True
EXIGIR_ASSETS_EXTERNOS = True   # Se faltarem arquivos, avisa ANTES de mexer na cena
TEMPO_DOWNLOAD_SEGUNDOS = 8

# Usa a pasta do .blend aberto. Ex.: TRABALHO/COMPUTACAO_GRAFICA.
# Se estiver em arquivo novo SEM salvar, usa a pasta Downloads como alternativa.
PASTA = Path(bpy.data.filepath).resolve().parent if bpy.data.filepath else Path.home() / 'Downloads'
PASTA.mkdir(parents=True,exist_ok=True)
ASSETS = PASTA / 'assets_CC0'
# O script NAO procura assets em pastas inventadas: apenas em assets_CC0
# ao lado do .blend que estiver aberto e salvo.

IMAGENS = PASTA  # arquivos gerados diretamente ao lado dos seus trabalhos

if bpy.app.version < (4, 5, 0) or bpy.app.version >= (5, 0, 0):
    print('AVISO: este script foi desenvolvido especificamente para o Blender 4.5 LTS. Detectado:', bpy.app.version_string)

print('[AC04] Pasta de trabalho detectada:', PASTA)
print('[AC04] Procurando bibliotecas externas em:', ASSETS)
print('[AC04] Pasta de assets existe:', ASSETS.is_dir())
for arquivo_necessario in ('satelliteDish.glb', 'satelliteDish_large.glb',
                          'satelliteDish_detailed.glb', 'metal_plate_diff_1k.jpg',
                          'metal_plate_rough_1k.jpg', 'metal_plate_nor_gl_1k.jpg'):
    print('[ASSET LOCAL]', arquivo_necessario,
          'OK' if (ASSETS / arquivo_necessario).is_file() else 'NAO ENCONTRADO')
# Valida os recursos externos ANTES de apagar a cena em memoria.
# Aceita a grafia original dos JPGs do Poly Haven ou o prefixo 'polyhaven_'.
requeridos = ('satelliteDish.glb', 'satelliteDish_large.glb',
              'satelliteDish_detailed.glb', 'metal_plate_diff_1k.jpg',
              'metal_plate_rough_1k.jpg', 'metal_plate_nor_gl_1k.jpg')
pendentes = [a for a in requeridos if not (ASSETS / a).is_file()
            and not (ASSETS / ('polyhaven_' + a)).is_file()]
if EXIGIR_ASSETS_EXTERNOS and pendentes:
    raise FileNotFoundError(
        'Pasta assets_CC0 incompleta ou no lugar errado. Pasta esperada: '
        + str(ASSETS) + '. Faltam: ' + ', '.join(pendentes)
        + '. Mova os seis arquivos para essa pasta; NENHUM objeto da cena foi apagado.')
print('[AC04] Criando nova cena. Nao alterarei os arquivos .blend existentes.')

# A limpeza afeta apenas a cena aberta em memoria, NAO os arquivos no Windows.

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
# Reinicia as colecoes desta cena sem apagar arquivos em disco.
for col in list(bpy.data.collections):
    bpy.data.collections.remove(col, do_unlink=True)

scene = bpy.context.scene
if 'AC04_V3_Aplicado' in scene:
    del scene['AC04_V3_Aplicado']
scene.frame_start = 1
scene.frame_end = 360
scene.render.fps = 24
scene.render.fps_base = 1.0
scene.render.resolution_x = RESOLUCAO_X
scene.render.resolution_y = RESOLUCAO_Y
scene.render.resolution_percentage = PERCENTUAL_RENDER
scene.render.film_transparent = False
scene.render.image_settings.color_mode = 'RGBA'
scene.display_settings.display_device = 'sRGB'
try:
    scene.view_settings.view_transform = 'AgX'
except Exception:
    pass
scene.render.engine = 'BLENDER_EEVEE_NEXT'  # Blender 4.5 (5.0 usa outro identificador)
if hasattr(scene, 'eevee') and hasattr(scene.eevee, 'taa_render_samples'):
    scene.eevee.taa_render_samples = SAMPLES_EEVEE

# Collections organizadas; a principal inclui TODOS os elementos.
for coll in list(scene.collection.children):
    if coll.name in ('Collection', 'AP1_Ibmec_Conceito'):
        scene.collection.children.unlink(coll)
principal = bpy.data.collections.new('AP1_Ibmec_Conceito')
scene.collection.children.link(principal)

def nova_subcolecao(nome):
    c = bpy.data.collections.new(nome)
    principal.children.link(c)
    return c

c_marca = nova_subcolecao('01_Marca')
c_autorais = nova_subcolecao('02_Objetos_Autorais_EXATAMENTE_3')
c_aux = nova_subcolecao('03_Elementos_Auxiliares')
c_luzes = nova_subcolecao('04_Iluminacao_AP2')

# AC04 V2: essas quatro colecoes faltavam na versao anterior.
# Uma colecao agrega todos os elementos complementares da composicao.
c_expandida = nova_subcolecao('05_AC04_Cenografia_e_Recursos_Externos')
def criar_filhos_da_expansao(nome):
    col = bpy.data.collections.new(nome)
    c_expandida.children.link(col)
    return col
cenografia = criar_filhos_da_expansao('AC04_AUX_Cenografia_NaoAutoral')
externos = criar_filhos_da_expansao('AC04_LIB_Kenney_CC0_NaoAutoral')
texto_aux = criar_filhos_da_expansao('AC04_AUX_Legendas')
luzes = criar_filhos_da_expansao('AC04_Luzes_Fixas_Comparacao')

def atribuir_colecao(obj, col):
    for antiga in list(obj.users_collection):
        antiga.objects.unlink(obj)
    col.objects.link(obj)
    return obj

def material_pbr(nome, cor, metallic=0.0, roughness=0.45, emission=None, emiss_strength=0.0,
                 textura=False):
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    mat.diffuse_color = (*cor[:3], 1.0)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    if bsdf is None:
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        out = nodes.get('Material Output') or nodes.new('ShaderNodeOutputMaterial')
        links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = (*cor[:3], 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if emission:
        ecolor = bsdf.inputs.get('Emission Color')
        estrength = bsdf.inputs.get('Emission Strength')
        if ecolor:
            ecolor.default_value = (*emission[:3], 1.0)
        if estrength:
            estrength.default_value = emiss_strength
    if textura:
        tex = nodes.new('ShaderNodeTexNoise')
        tex.label = 'Textura procedural da superfície'
        tex.inputs['Scale'].default_value = 18.0
        tex.inputs['Detail'].default_value = 3.0
        coord = nodes.new('ShaderNodeTexCoord')
        links.new(coord.outputs['Generated'], tex.inputs['Vector'])
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.14
        bump.inputs['Distance'].default_value = 0.05
        links.new(tex.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
        remap = nodes.new('ShaderNodeMapRange')
        remap.inputs['From Min'].default_value = 0.0
        remap.inputs['From Max'].default_value = 1.0
        remap.inputs['To Min'].default_value = max(roughness - 0.12, 0.08)
        remap.inputs['To Max'].default_value = min(roughness + 0.12, 0.95)
        links.new(tex.outputs['Fac'], remap.inputs['Value'])
        links.new(remap.outputs['Result'], bsdf.inputs['Roughness'])
    return mat

azul_escuro = material_pbr('M01_AzulIbmec_Anodizado', (0.017,0.052,0.16), .72, .27, textura=True)
azul_med = material_pbr('M02_AzulTecnologico', (0.022,0.19,0.36), .66, .27, textura=True)
dourado = material_pbr('M03_DouradoInstitucional', (0.91,0.51,0.07), .64, .23)
marfim = material_pbr('M04_Tipografia_Clara', (0.93,0.96,1.0), .15, .22)
portal_ouro = material_pbr('M05_Portal_LuzDourada', (.92,.45,.05), .52, .20,
                           emission=(1.0,.35,.02), emiss_strength=1.6)
portal_azul = material_pbr('M06_Portal_LuzAzul', (.03,.37,.67), .45, .24,
                           emission=(.03,.3,1.0), emiss_strength=1.4)
portal_prata = material_pbr('M07_Portal_Plateado', (.55,.7,.78), .88, .19)
piso = material_pbr('M08_Piso_Procedural', (.027,.04,.065), .35, .48, textura=True)

# -------------------------- OBJETO AUTORAL 1 --------------------------
# Pódio octogonal com anéis de vértices, recuos (inset) e subidas (extrusion).
# É UM único objeto de malha com diversos andares modelados proceduralmente.

def criar_plataforma():
    n = 8
    rings = [
        (5.28, 3.55, 0.06),
        (5.28, 3.55, 0.52),
        (4.98, 3.34, 0.52),
        (4.98, 3.34, 0.70),
        (4.55, 2.92, 0.70),
        (4.55, 2.92, 0.98),
        (4.18, 2.56, 0.98),
        (4.18, 2.56, 1.18),
    ]
    verts, faces, indices = [], [], []
    for rx, ry, z in rings:
        for k in range(n):
            a = 2 * math.pi * (k + 0.5) / n
            verts.append((rx * math.cos(a), ry * math.sin(a), z))
    faces.append(tuple(range(n - 1, -1, -1)))
    indices.append(0)
    for i in range(len(rings)-1):
        for k in range(n):
            kp = (k + 1) % n
            faces.append((i*n+k, i*n+kp, (i+1)*n+kp, (i+1)*n+k))
            # alterna filetes dourados com corpo azul/metalizado
            indices.append(1 if i in (1, 3, 5) else (2 if i == 6 else 0))
    faces.append(tuple((len(rings)-1)*n + k for k in range(n)))
    indices.append(0)
    mesh = bpy.data.meshes.new('Malha_Plataforma_Inset_Extrude')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('Obj_PlataformaAscensao', mesh)
    c_autorais.objects.link(obj)
    for mat in (azul_escuro, dourado, azul_med):
        obj.data.materials.append(mat)
    for poly, idx in zip(obj.data.polygons, indices):
        poly.material_index = idx
    bevel = obj.modifiers.new('Bevel_Bordas_Plataforma', 'BEVEL')
    bevel.width = 0.07
    bevel.segments = 3
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = math.radians(42)
    return obj

plataforma = criar_plataforma()

# --------------------------- OBJETO AUTORAL 2 -------------------------
# Portal triplo composto de 3 superfícies toroidais numa única malha.
# A animação do AP2 gira o conjunto mantendo apenas 1 objeto autoral.

def criar_portal():
    verts, faces, material_faces = [], [], []
    major_seg, minor_seg = 112, 10
    configura = [
        (2.91, 3.16, 0.105, -0.27, math.radians(18), 0),
        (3.36, 3.53, 0.095,  0.00, math.radians(-9), 1),
        (3.78, 3.91, 0.082,  0.25, math.radians(11), 2),
    ]
    for rx, rz, tube, depth, inclinacao, mat_id in configura:
        offset = len(verts)
        for i in range(major_seg):
            t = 2 * math.pi * i / major_seg
            x0 = rx * math.cos(t)
            z0 = rz * math.sin(t)
            # inclinação in-plane de elipses, propositalmente autoral
            xx = math.cos(inclinacao)*x0 - math.sin(inclinacao)*z0
            zz = math.sin(inclinacao)*x0 + math.cos(inclinacao)*z0
            nx = math.cos(t)
            nz = math.sin(t)
            for j in range(minor_seg):
                v = 2 * math.pi * j / minor_seg
                x = xx + tube * math.cos(v) * nx
                z = zz + tube * math.cos(v) * nz
                y = depth + tube * math.sin(v)
                verts.append((x,y,z))
        for i in range(major_seg):
            for j in range(minor_seg):
                a = offset + i * minor_seg + j
                b = offset + ((i + 1) % major_seg) * minor_seg + j
                c = offset + ((i + 1) % major_seg) * minor_seg + ((j + 1) % minor_seg)
                d = offset + i * minor_seg + ((j + 1) % minor_seg)
                faces.append((a,b,c,d))
                material_faces.append(mat_id)
    mesh = bpy.data.meshes.new('Malha_TriploPortal_Toroides')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('Obj_PortalFuturo', mesh)
    c_autorais.objects.link(obj)
    obj.location = (0, 1.5, 3.97)
    for mat in (portal_ouro, portal_azul, portal_prata):
        mesh.materials.append(mat)
    for poly, idx in zip(mesh.polygons, material_faces):
        poly.material_index = idx
        poly.use_smooth = True
    return obj

portal = criar_portal()

# --------------------------- OBJETO AUTORAL 3 -------------------------
# Uma torre esculpida em prismas; Mirror no eixo X cria a torre simétrica.

def criar_torres():
    n = 8
    cx = -6.33
    rings = [
        (0.70,0.65,0.08),
        (0.72,0.67,0.35),
        (0.62,0.59,0.56),
        (0.62,0.59,4.90),
        (0.55,0.51,5.22),
        (0.44,0.42,5.89),
        (0.37,0.37,6.45),
        (0.17,0.21,6.92),
    ]
    verts, faces, indices = [], [], []
    for rx, ry, z in rings:
        for i in range(n):
            a = math.tau * (i+0.5) / n
            verts.append((cx + rx*math.cos(a), 0.30 + ry*math.sin(a), z))
    faces.append(tuple(range(n-1,-1,-1)))
    indices.append(0)
    for k in range(len(rings)-1):
        for i in range(n):
            j = (i + 1) % n
            faces.append((k*n+i, k*n+j, (k+1)*n+j, (k+1)*n+i))
            indices.append(1 if k in (1,4,6) else 0)
    faces.append(tuple((len(rings)-1)*n + i for i in range(n)))
    indices.append(1)
    mesh = bpy.data.meshes.new('Malha_Torre_Extrusoes_Cortes')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('Obj_TorresConexao', mesh)
    c_autorais.objects.link(obj)
    mesh.materials.append(azul_med)
    mesh.materials.append(dourado)
    for poly, idx in zip(mesh.polygons, indices):
        poly.material_index = idx
    mirror = obj.modifiers.new('Mirror_Torres_Simetria_X', 'MIRROR')
    mirror.use_axis[0] = True
    mirror.use_axis[1] = False
    mirror.use_axis[2] = False
    bevel = obj.modifiers.new('Bevel_Torres', 'BEVEL')
    bevel.width = 0.055
    bevel.segments = 2
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = math.radians(44)
    return obj

torres = criar_torres()

# -------------------------- MARCA IBMEC -------------------------------
# Texto extrudado (não contado entre os 3 objetos autorais).
text_data = bpy.data.curves.new('Fonte_Ibmec_Extrudada', type='FONT')
text_data.body = 'Ibmec'
text_data.align_x = 'CENTER'
text_data.align_y = 'CENTER'
text_data.size = 2.15
text_data.extrude = 0.10
text_data.bevel_depth = 0.013
text_data.bevel_resolution = 3
if CAMINHO_FONTE_IBMEC and os.path.isfile(CAMINHO_FONTE_IBMEC):
    text_data.font = bpy.data.fonts.load(CAMINHO_FONTE_IBMEC)
text = bpy.data.objects.new('Marca_Ibmec', text_data)
c_marca.objects.link(text)
text.rotation_euler = (math.radians(90), 0, 0)
text.location = (0, -0.92, 3.55)
text.data.materials.append(marfim)
# Ajuste automático de proporção: garantir legibilidade e largura ~7 unidades.
bpy.context.view_layer.update()
if text.dimensions.x > 0.01:
    factor = 7.15 / text.dimensions.x
    text.scale = (factor,factor,factor)
bpy.context.view_layer.update()

# --------------------------- AUXILIARES -------------------------------
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-0.05))
chao = atribuir_colecao(bpy.context.object, c_aux)
chao.name = 'Aux_Chao_Cenario'
chao.data.materials.append(piso)

world = scene.world or bpy.data.worlds.new('World_Ibmec')
scene.world = world
world.use_nodes = True
world_bg = world.node_tree.nodes.get('Background')
world_bg.inputs['Color'].default_value = (.055,.075,.13,1)
world_bg.inputs['Strength'].default_value = .24

# Câmera principal; animação adicionada somente à versão AP2.
def mirar(obj, alvo):
    v = Vector(alvo) - obj.location
    obj.rotation_euler = v.to_track_quat('-Z','Y').to_euler()

camdata = bpy.data.cameras.new('Lente_AP1_AP2')
camera = bpy.data.objects.new('Cam_Principal_AP1', camdata)
c_aux.objects.link(camera)
scene.camera = camera
camdata.type = 'PERSP'
camdata.lens = 42
camdata.clip_end = 450
camera.location = (2.15,-24.6,9.3)
mirar(camera, (0,0.25,3.8))

# Luzes já ficam separadas em coleção auxiliar e são desenvolvidas na AP2.
def criar_luz(nome, tipo, loc, target, cor, energia, tamanho):
    ld = bpy.data.lights.new(nome, tipo)
    ld.energy = energia
    ld.color = cor
    if tipo == 'AREA':
        ld.shape = 'DISK'
        ld.size = tamanho
    ob = bpy.data.objects.new(nome, ld)
    c_luzes.objects.link(ob)
    ob.location = loc
    mirar(ob, target)
    return ob

luz_frontal = criar_luz('Luz_Key_Frontal', 'AREA', (0,-7,11), (0,0,3.4), (1,.87,.67), 3000, 9)
luz_azul = criar_luz('Luz_Rim_Azul', 'AREA', (6,4,9), (0,0,3.8), (.36,.64,1), 2700, 8)
luz_orange = criar_luz('Luz_Lateral_Dourada', 'AREA', (-7,-2,7), (0,0,3.8), (1,.57,.23), 2400, 7)



# OBJETOS RECRIADOS A PARTIR DO CONCEITO AP1
plataforma = bpy.data.objects["Obj_PlataformaAscensao"]
portal = bpy.data.objects["Obj_PortalFuturo"]
torres = bpy.data.objects["Obj_TorresConexao"]
marca = bpy.data.objects["Marca_Ibmec"]

# Confirmacao dos 3 autorais apos geracao procedural.
assert {o.name for o in c_autorais.objects} == {
    'Obj_PlataformaAscensao', 'Obj_PortalFuturo', 'Obj_TorresConexao'
}, 'A colecao autoral deve conter exatamente 3 objetos.'
assert scene.render.fps == 24 and scene.frame_end == 360

# MATERIAIS DIDATICOS: Lambert difuso REAL; Phong/Blinn APROXIMACOES PBR

# ========================================================================

def material_principled(nome, cor, roughness, ior_level, metallic=0.0, emission=None):
    mat = bpy.data.materials.get(nome) or bpy.data.materials.new(nome)
    mat.use_nodes = True
    mat.diffuse_color = (*cor, 1.0)
    mat.node_tree.nodes.clear()
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (300, 60)
    p = nodes.new('ShaderNodeBsdfPrincipled')
    p.location = (0, 60)
    p.inputs['Base Color'].default_value = (*cor, 1.0)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    spec = p.inputs.get('Specular IOR Level') or p.inputs.get('IOR Level') or p.inputs.get('Specular')
    if spec:
        spec.default_value = ior_level
    if emission is not None:
        inp = p.inputs.get('Emission Color')
        if inp:
            inp.default_value = (*emission[0], 1.0)
        inp = p.inputs.get('Emission Strength')
        if inp:
            inp.default_value = emission[1]
    links.new(p.outputs['BSDF'], out.inputs['Surface'])
    return mat

# Esta versao evita qualquer brilho especular no Lambert de modo explicito.
lambert = bpy.data.materials.get('MAT_Lambert') or bpy.data.materials.new('MAT_Lambert')
lambert.use_nodes = True
lambert.diffuse_color = (0.49, 0.61, 0.73, 1)
lambert.node_tree.nodes.clear()
diff = lambert.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
diff.location = (0, 30)
diff.inputs['Color'].default_value = (0.49, 0.61, 0.73, 1)
diff.inputs['Roughness'].default_value = 0.0
out = lambert.node_tree.nodes.new('ShaderNodeOutputMaterial')
out.location = (260, 30)
lambert.node_tree.links.new(diff.outputs['BSDF'], out.inputs['Surface'])

phong = material_principled('MAT_Phong', (0.11, 0.32, 0.71), 0.20, 0.55)
blinn = material_principled('MAT_BlinnPhong', (0.73, 0.45, 0.13), 0.10, 0.85)

for ob, mat in ((plataforma, lambert), (portal, phong), (torres, blinn)):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for poly in ob.data.polygons:
        poly.material_index = 0
    ob['AC04_Modelo'] = mat.name
# Marca_Ibmec e intencionalmente intocada.

# Materiais da cenografia (nao se sobrepoem aos 3 objetos autorais)
carvao = material_principled('AUX_Metal_Grafite', (0.020, 0.032, 0.060), .36, .50, metallic=.72)
azul_escuro = material_principled('AUX_Azul_Arquitetonico', (.035, .070, .140), .30, .55, metallic=.62)
aco = material_principled('AUX_Aluminio', (.31, .39, .47), .25, .53, metallic=.80)
led_azul = material_principled('AUX_LED_Ciano', (.015, .65, 1.0), .40, .4, emission=((.03, .55, 1.0), 3.6))
led_ouro = material_principled('AUX_LED_Amber', (1.0, .47, .08), .40, .4, emission=((1.0, .31, .025), 3.0))
led_branco = material_principled('AUX_LED_Branco', (.8, .95, 1.0), .40, .4, emission=((.62, .88, 1.0), 2.4))


def colocar_colecao(obj, colecao):
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    colecao.objects.link(obj)
    return obj


def bloco(nome, pos, dims, mat, bevel=0.0, col=cenografia):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    ob = colocar_colecao(bpy.context.object, col)
    ob.name = nome
    ob.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new('Acabamento_Bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = 'ANGLE'
    ob['Classificacao'] = 'AUXILIAR — nao e objeto autoral'
    return ob


def linha_curve(nome, coords, raio, mat, col=cenografia, cyclic=False):
    curve = bpy.data.curves.new(f'{nome}_Curva', type='CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 2
    curve.bevel_depth = raio
    curve.bevel_resolution = 3
    poly = curve.splines.new('POLY')
    poly.points.add(len(coords)-1)
    for point, co in zip(poly.points, coords):
        point.co = (*co, 1)
    poly.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(nome, curve)
    col.objects.link(ob)
    ob.data.materials.append(mat)
    ob['Classificacao'] = 'AUXILIAR — nao e objeto autoral'
    return ob


def arco(nome, rx, ry, cy, z, ang0, ang1, mat, raio=.02, steps=96):
    coords = []
    for i in range(steps+1):
        a = ang0 + (ang1-ang0)*i/steps
        coords.append((rx*math.cos(a), cy + ry*math.sin(a), z))
    return linha_curve(nome, coords, raio, mat)

# ========================================================================
# AMBIENTE: ARQUITETURA CINEMATICA / PISO TECNOLOGICO / ARCOS / LUMINARIAS
# ========================================================================
# Chao recriado proceduralmente; material e posicao serao mantidos neste teste.
# Cenografia e instalada fora da area da marca, como elemento de apoio.
bloco('AUX_Plataforma_Inferior_Cenografica', (0, 0.55, -.18), (15.5, 13.0, .40), carvao, .22)
bloco('AUX_Passarela_Acesso', (0, -7.0, -.075), (4.0, 12.0, .19), azul_escuro, .08)

# Duas fileiras de luzes discretas ao longo da passarela.
for lado in (-1, 1):
    for i in range(8):
        yy = -11.5 + i*1.4
        bloco(f'AUX_Sinalizacao_Pista_{lado}_{i}', (lado*1.65, yy, .043),
              (.07, .72, .018), led_azul if i%2 else led_ouro, .012)

# Piso tecnico desenhado como circuitos e trilhos concentricos.
for i, raio in enumerate((5.6, 6.15, 7.15)):
    pts = [(raio*math.cos(j*math.tau/128),
            .6 + (raio*.78)*math.sin(j*math.tau/128), .041)
           for j in range(128)]
    linha_curve(f'AUX_Anel_Piso_{i}', pts, .025 if i==1 else .013,
                led_ouro if i==1 else led_azul, cyclic=True)
for lado in (-1,1):
    for i in range(6):
        x = lado*(5.2 + .38*i)
        linha_curve(f'AUX_Circuito_Lateral_{lado}_{i}',
                    [(x, -4.6, .045), (x, 3.0 + i*.28, .045)], .012,
                    led_azul if i % 3 else led_ouro)

# Arquibancada-arquitetura ao fundo: nervuras e vigas verticalizadas.
for i, y in enumerate((3.9, 5.0, 6.1, 7.2)):
    for lado in (-1,1):
        # Suportes distantes; nao obstruem a marca ou o portal.
        bloco(f'AUX_Pilar_Fundo_{i}_{lado}',
              (lado*(7.15+i*.36), y, 3.65),
              (.28, .46, 7.5), azul_escuro, .085)
        linha_curve(f'AUX_Linha_Pilar_{i}_{lado}',
                    [(lado*(7.15+i*.36)-lado*.17, y-.25, .45),
                     (lado*(7.15+i*.36)-lado*.17, y-.25, 7.4)],
                    .027, led_azul if i%2 else led_ouro)

# Arcos semicirculares altos ligando parte superior sem cobrir IBMEC.
for i, y in enumerate((4.2, 6.3, 8.3)):
    pts = []
    for j in range(61):
        theta = math.pi*(j/60)
        pts.append((7.4*math.cos(theta), y, 4.0+4.9*math.sin(theta)))
    linha_curve(f'AUX_Estrutura_Arco_Grande_{i}', pts, .095, carvao)
    if i != 1:
        linha_curve(f'AUX_Fibra_Luminosa_Arco_{i}',
                    [(x, yy-.16, z+.08) for x, yy, z in pts],
                    .022, led_azul)

# Pontos de controle: consoles baixos e lamelas. Tudo tratado como CENOGRAFIA.
for lado in (-1,1):
    x = lado*7.35
    bloco(f'AUX_Console_Pedestal_{lado}', (x,-3.65,.7),
          (.85,1.0,1.50), carvao, .10)
    tela = bloco(f'AUX_Console_Tela_{lado}', (x,-4.0,1.50),
                 (1.15,.10,.78), azul_escuro, .045)
    tela.rotation_euler.x = math.radians(-14)
    for i in range(5):
        bloco(f'AUX_Console_Indicador_{lado}_{i}',
              (x-.43+i*.22,-4.075,1.54), (.12,.020,.025),
              led_ouro if i==2 else led_azul, .004)

# ========================================================================
# LIBRARY ASSETS: MODELOS 3D KENNEY, E TEXTURAS PBR POLY HAVEN (CC0)
# ========================================================================
# Fontes verificaveis, de uso educativo e comercial sem obrigacao de credito:
# https://kenney.nl/assets/space-kit | CC0 1.0
# https://polyhaven.com/a/metal_plate | CC0 1.0
# Baixar da web e opcional. Se nao houver internet, a geometria base continua.
# Procura primeiro arquivos ja copiados para ASSETS pelo usuario.

fontes_kenney = {
    'satelliteDish': 'https://raw.githubusercontent.com/euuuuuuuan/voidclad-public/main/assets/vendor/kenney_space_kit/satelliteDish.glb',
    'satelliteDish_large': 'https://raw.githubusercontent.com/euuuuuuuan/voidclad-public/main/assets/vendor/kenney_space_kit/satelliteDish_large.glb',
    'satelliteDish_detailed': 'https://raw.githubusercontent.com/euuuuuuuan/voidclad-public/main/assets/vendor/kenney_space_kit/satelliteDish_detailed.glb',
}
texturas_ph = {
    'diff': 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/metal_plate/metal_plate_diff_1k.jpg',
    'rough': 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/metal_plate/metal_plate_rough_1k.jpg',
    'nor_gl': 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/metal_plate/metal_plate_nor_gl_1k.jpg',
}

recursos_ok = []
recursos_indisponiveis = []

def obter(url, nome):
    arquivo = ASSETS / nome
    if arquivo.is_file() and arquivo.stat().st_size > 512:
        return arquivo
    # Aceita tambem os nomes ORIGINAIS do Poly Haven baixados pelo usuario.
    if nome.startswith('polyhaven_'):
        alternativa = ASSETS / nome[len('polyhaven_'):]
        if alternativa.is_file() and alternativa.stat().st_size > 512:
            return alternativa
    if not BAIXAR_ASSETS_EXTERNOS:
        recursos_indisponiveis.append(nome)
        return None
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'Blender-AC04-Educacional/1.0'})
        with urllib.request.urlopen(req, timeout=TEMPO_DOWNLOAD_SEGUNDOS) as resposta:
            body = resposta.read(5_000_000)
        if len(body) < 512:
            raise ValueError('Arquivo vazio ou incompleto')
        if nome.lower().endswith('.glb') and body[:4] != b'glTF':
            raise ValueError('O download nao e um arquivo GLB valido')
        if nome.lower().endswith('.jpg') and body[:2] != b'\xff\xd8':
            raise ValueError('O download nao e uma imagem JPEG valida')
        arquivo.write_bytes(body)
        print('[EXTERNO] baixado:', nome, len(body), 'bytes')
        return arquivo
    except Exception as e:
        recursos_indisponiveis.append(nome)
        print('[AVISO] recurso externo indisponivel:', nome, type(e).__name__, str(e))
        return None


def importar_kenney(caminho, nome, posicao, altura, angulo_z=0):
    # Normaliza o tamanho do modelo importado por sua bounding-box.
    anteriores = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.gltf(filepath=str(caminho))
    except Exception as e:
        print('[AVISO] Falha na importacao do GLB:', caminho, str(e))
        return False
    importados = [ob for ob in bpy.data.objects if ob not in anteriores]
    if not importados:
        return False
    bpy.context.view_layer.update()
    cantos = [ob.matrix_world @ Vector(c) for ob in importados if ob.type=='MESH' for c in ob.bound_box]
    if not cantos:
        for ob in importados: bpy.data.objects.remove(ob, do_unlink=True)
        return False
    mini = Vector([min(p[i] for p in cantos) for i in range(3)])
    maxi = Vector([max(p[i] for p in cantos) for i in range(3)])
    centro = (mini + maxi)*.5
    span = max((maxi - mini).z, .01)
    fator = altura / span
    transf = (Matrix.Translation(Vector(posicao))
              @ Matrix.Rotation(math.radians(angulo_z),4,'Z')
              @ Matrix.Scale(fator,4)
              @ Matrix.Translation(Vector((-centro.x,-centro.y,-mini.z))))
    # Mover APENAS os pais de topo preserva hierarquia do glTF.
    import_set = set(importados)
    raizes = [ob for ob in importados if ob.parent not in import_set]
    for ob in raizes:
        ob.matrix_world = transf @ ob.matrix_world
    for ob in importados:
        colocar_colecao(ob, externos)
        ob.name = 'LIB_Kenney_'+nome+'_'+ob.name
        ob['Autor'] = 'Kenney — Space Kit'
        ob['Licenca'] = 'CC0 1.0 Universal'
        ob['Papel'] = 'Modelo EXTERNO auxiliar; nao integra os 3 autorais'
    recursos_ok.append('Modelo Kenney: '+nome)
    return True

if USAR_PROPS_KENNEY:
    for key, pos, altura, ang in (
        ('satelliteDish', (-8.65, 1.7, -.14), 1.9, 45),
        ('satelliteDish_large', (8.65, 2.0, -.14), 2.25, -45),
        ('satelliteDish_detailed', (0.0, 8.7, -.16), 2.0, 0),
    ):
        caminho = obter(fontes_kenney[key], key+'.glb')
        if caminho:
            importar_kenney(caminho, key, pos, altura, ang)

# PBR externo em objetos AUXILIARES. Nenhum dos tres modelos didaticos e alterado.
tex_paths = {}
if USAR_TEXTURE_POLYHAVEN:
    for typ, url in texturas_ph.items():
        f = obter(url, 'polyhaven_metal_plate_'+typ+'_1k.jpg')
        if f:
            tex_paths[typ] = f

# Material de piso com mapas externos (color/rough/normal), com fallback procedural.
piso_pbr = material_principled('AUX_Piso_Texturizado_PBR', (.12,.15,.18), .72, .45, metallic=.45)
node_tree = piso_pbr.node_tree
nodes, links = node_tree.nodes, node_tree.links
pbr = next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
texcoord = nodes.new('ShaderNodeTexCoord'); texcoord.location=(-720,-80)
mapping = nodes.new('ShaderNodeMapping'); mapping.location=(-540,-80)
mapping.inputs['Scale'].default_value=(3.0,3.0,3.0)
links.new(texcoord.outputs['Generated'],mapping.inputs['Vector'])
if 'diff' in tex_paths:
    img = bpy.data.images.load(str(tex_paths['diff']), check_existing=True)
    node = nodes.new('ShaderNodeTexImage'); node.location=(-320,350); node.image=img
    links.new(mapping.outputs['Vector'], node.inputs['Vector'])
    links.new(node.outputs['Color'], pbr.inputs['Base Color'])
if 'rough' in tex_paths:
    img = bpy.data.images.load(str(tex_paths['rough']), check_existing=True)
    img.colorspace_settings.name='Non-Color'
    node = nodes.new('ShaderNodeTexImage'); node.location=(-330,100); node.image=img
    links.new(mapping.outputs['Vector'], node.inputs['Vector'])
    links.new(node.outputs['Color'], pbr.inputs['Roughness'])
if 'nor_gl' in tex_paths:
    img = bpy.data.images.load(str(tex_paths['nor_gl']), check_existing=True)
    img.colorspace_settings.name='Non-Color'
    node = nodes.new('ShaderNodeTexImage'); node.location=(-350,-160); node.image=img
    normal = nodes.new('ShaderNodeNormalMap'); normal.location=(-95,-160)
    normal.inputs['Strength'].default_value=.38
    links.new(mapping.outputs['Vector'], node.inputs['Vector'])
    links.new(node.outputs['Color'], normal.inputs['Color'])
    links.new(normal.outputs['Normal'], pbr.inputs['Normal'])
if not tex_paths:
    # Fallback sem downloads: ruido procedural e bump em materiais AUXILIARES.
    noise = nodes.new('ShaderNodeTexNoise');noise.location=(-330,80)
    noise.inputs['Scale'].default_value=11
    bump = nodes.new('ShaderNodeBump');bump.location=(-85,-160)
    bump.inputs['Strength'].default_value=.14
    bump.inputs['Distance'].default_value=.08
    links.new(mapping.outputs['Vector'],noise.inputs['Vector'])
    links.new(noise.outputs['Fac'],bump.inputs['Height'])
    links.new(bump.outputs['Normal'],pbr.inputs['Normal'])

piso_amostra = bloco('AUX_Placa_Exposicao_PBR_Externo', (0,-10.95,.052),
                    (3.8, 2.0, .045), piso_pbr, .025)
if tex_paths:
    recursos_ok.append('Texturas Poly Haven Metal Plate (mapas): '+', '.join(sorted(tex_paths)))

# ========================================================================
# LEGENDAS DIDATICAS DISCRETAS (foco da marca continua intacto)
# ========================================================================

def legenda(nome, corpo, loc, mat, size=.30):
    cu = bpy.data.curves.new(nome+'_dados', type='FONT')
    cu.body = corpo
    cu.size = size
    cu.align_x='CENTER'
    cu.extrude=.002
    ob=bpy.data.objects.new(nome, cu)
    texto_aux.objects.link(ob)
    ob.rotation_euler.x=math.radians(90)
    ob.location=loc
    cu.materials.append(mat)
    ob['Classificacao']='AUXILIAR didatico, nao objeto autoral'
    return ob

legenda('AUX_Titulo_Lambert', '01  /  LAMBERT  /  DIFUSO', (-5.0,-5.1,.22),led_branco,.26)
legenda('AUX_Titulo_Phong', '02  /  PHONG  /  BRILHO', (0,-5.1,.22),led_azul,.26)
legenda('AUX_Titulo_Blinn', '03  /  BLINN-PHONG', (5.0,-5.1,.22),led_ouro,.26)

# ========================================================================
# ILUMINACAO CONTROLADA: MESMAS LUZES / MESMA CAMERA / MESMO FRAME
# ========================================================================
for ob in bpy.data.objects:
    if ob.type=='LIGHT':
        ob.hide_render=True

def apontar(obj, alvo):
    direction=Vector(alvo)-obj.location
    obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()

def luz_area(nome,loc,alvo,potencia,cor,tamanho):
    data=bpy.data.lights.new(nome,'AREA')
    data.energy=potencia
    data.color=cor
    data.shape='DISK'
    data.size=tamanho
    ob=bpy.data.objects.new(nome,data)
    luzes.objects.link(ob)
    ob.location=loc
    apontar(ob,alvo)
    ob.hide_render=False
    return ob

luz_area('AC04_KEY_Area_Fixa',(-6.0,-7.0,13.5),(0,0,3.6),2800,(1,.93,.83),5)
luz_area('AC04_FILL_Area_Fixa',(7.5,-4.2,7.2),(0,0,3.7),480,(.68,.82,1),8)

world=bpy.data.worlds.new('AC04_World_Noturno')
world.use_nodes=True
bg=world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value=(.020,.035,.070,1)
    bg.inputs['Strength'].default_value=.25
scene.world=world



# ============== ETAPA FINAL: AJUSTES E COMPARACAO VISUAL ==============

# Escolhe nome limpo e NUNCA substitui um projeto .blend que ja exista.
def escolher_nome_saida(pasta, nome):
    primeiro = pasta / nome
    if not primeiro.exists():
        return primeiro
    candidato = pasta / 'AC04_HenriqueSartori_FINAL.blend'
    if not candidato.exists():
        return candidato
    for n in range(2, 1000):
        candidato = pasta / f'AC04_HenriqueSartori_FINAL_{n}.blend'
        if not candidato.exists():
            return candidato
    raise RuntimeError('Muitas versoes na pasta; remova backups antigos antes de continuar.')

import bpy
import math
from pathlib import Path
from mathutils import Vector

try:
    import numpy as np
except ImportError as e:
    raise RuntimeError('Numpy não está disponível no Python do Blender. O script não alterou nada.') from e

# =============================== CONFIGURAÇÃO =============================
RESOLUCAO = (1600, 900)
FRAME_AVALIACAO = 360
RENDERIZAR = True
PASTA = Path(bpy.data.filepath).resolve().parent if bpy.data.filepath else None
if PASTA is None:
    raise RuntimeError('Salve uma cena nova .blend na pasta COMPUTAÇÃO_GRAFICA antes de executar.')

scene = bpy.context.scene

NECESSARIOS = ['Obj_PlataformaAscensao', 'Obj_PortalFuturo', 'Obj_TorresConexao',
               'Marca_Ibmec', 'Cam_Principal_AP1',
               'AC04_KEY_Area_Fixa', 'AC04_FILL_Area_Fixa']
faltando = [nome for nome in NECESSARIOS if bpy.data.objects.get(nome) is None]
if faltando:
    raise RuntimeError('Erro na etapa de construcao: objetos ausentes: ' + ', '.join(faltando))
for material in ['MAT_Lambert','MAT_Phong','MAT_BlinnPhong']:
    if bpy.data.materials.get(material) is None:
        raise RuntimeError('Erro na etapa de construcao: material ausente: '+material)

# não muda a aplicação dos 3 materiais exigidos
plataforma = bpy.data.objects['Obj_PlataformaAscensao']
portal = bpy.data.objects['Obj_PortalFuturo']
torres = bpy.data.objects['Obj_TorresConexao']
marca = bpy.data.objects['Marca_Ibmec']
camera = bpy.data.objects['Cam_Principal_AP1']
scene.camera = camera

# =================== 1. RETIRAR ANTENA DO TEXTO ==========================
# O modelo detailed Kenney está no centro do portal, exatamente atrás de "Ibmec".
# Deslocá-lo pelo(s) nó(s) raiz preserva a hierarquia de importação glTF.
grp = [o for o in bpy.data.objects if o.name.startswith('LIB_Kenney_satelliteDish_detailed_')]
raizes = [o for o in grp if o.parent not in grp]
for raiz in raizes:
    mx = raiz.matrix_world.copy()
    mx.translation += Vector((9.4, -3.0, 0.0))
    raiz.matrix_world = mx
print('[V3] Partes Kenney central encontradas:', len(grp), '; raízes deslocadas:', len(raizes))

# =================== 2. IDENTIDADE VISUAL E COMPOSIÇÃO ===================
# Marca permanece texto original. Mudamos apenas posição, não as letras.
marca.location.y = -1.55   # separação espacial do portal atrás
marca.location.z = 4.05    # nome melhor posicionado dentro dos anéis

# Abertura do portal: anéis não devem cortar as extremidades da palavra.
portal.scale.x = 1.24
portal.scale.z = 1.08

# Sombra/contorno discreto separado, como elemento gráfico AUXILIAR.
# A marca original NÃO tem materiais alterados.
col_aux = bpy.data.collections.get('03_Elementos_Auxiliares')
if col_aux:
    escuro = bpy.data.materials.get('AUX_Sombra_Tipografia_V3')
    if escuro is None:
        escuro = bpy.data.materials.new('AUX_Sombra_Tipografia_V3')
        escuro.use_nodes = True
        nodo = escuro.node_tree.nodes.get('Principled BSDF')
        if nodo:
            nodo.inputs['Base Color'].default_value = (.006,.015,.038,1)
            nodo.inputs['Roughness'].default_value = .95
    dados = marca.data.copy()
    dados.name = 'AUX_Fonte_Contorno_Da_Marca'
    dados.materials.clear()
    dados.materials.append(escuro)
    sombra = bpy.data.objects.new('AUX_Contorno_Da_Marca_NaoAutoral',dados)
    col_aux.objects.link(sombra)
    sombra.location = marca.location + Vector((0,0.16,-.01))
    sombra.rotation_euler = marca.rotation_euler.copy()
    sombra.scale = marca.scale.copy() * 1.045
    sombra['Papel'] = 'Contorno auxiliar para legibilidade; não é objeto autoral.'

# Câmera mais frontal, mas ainda em perspectiva para preservar profundidade.
# A mesma câmera será usada NOS DOIS renders V3.
camera.location = (1.12,-24.9,8.25)
alvo = Vector((0,0.10,3.88))
camera.rotation_euler = (alvo-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.lens = 42

# =================== 3. DESTACAR COMPONENTE ESPECULAR ====================
# Fontes fixas, SEM mudar entre materiais/capturas.
# Luz KEY menor e mais direcional: realces concentrados observáveis.
key = bpy.data.objects['AC04_KEY_Area_Fixa']
fill = bpy.data.objects['AC04_FILL_Area_Fixa']
key.location = (-5.6,-8.0,10.6)
key.rotation_euler = (Vector((0,0,3.8))-key.location).to_track_quat('-Z','Y').to_euler()
key.data.energy = 3750
key.data.color = (1.0,0.93,0.85)
key.data.shape = 'DISK'
key.data.size = 2.3
key.hide_render = False

fill.location = (7.8,-5.2,7.3)
fill.rotation_euler = (Vector((0,0,3.6))-fill.location).to_track_quat('-Z','Y').to_euler()
fill.data.energy = 350
fill.data.color = (0.64,0.80,1.0)
fill.data.shape = 'DISK'
fill.data.size = 7.5
fill.hide_render = False

# Consistência didática: mantém Diffuse BSDF da plataforma, Principled dos
# outros dois; não altera IOR Level / Roughness da V2 (0.20/0.55, 0.10/0.85).
assert plataforma.data.materials[0].name == 'MAT_Lambert'
assert portal.data.materials[0].name == 'MAT_Phong'
assert torres.data.materials[0].name == 'MAT_BlinnPhong'

# =================== 4. RENDER / QUALIDADE ===============================
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x, scene.render.resolution_y = RESOLUCAO
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.use_stamp = False
scene.render.film_transparent = False
scene.render.fps = 24
scene.frame_start,scene.frame_end = 1,360
scene.frame_set(FRAME_AVALIACAO)
scene.view_settings.view_transform = 'AgX'

# Guarda imutáveis de comparação
setup_luzes = tuple((o.name, tuple(o.location), tuple(o.rotation_euler),
                     o.data.energy, o.data.size, tuple(o.data.color)) for o in (key,fill))

# =================== 5. PAINEL EM TRÊS COLUNAS ===========================
# Montagem inteiramente em Blender Python + numpy, sem Pillow nem dependências
# do Windows. Reaproveita recortes DA MESMA IMAGEM RENDERIZADA, logo cada
# objeto tem câmera e iluminação idênticas.

# Fonte de 5x7 pixels: legenda monocromática de estilo técnico.
GLYPHS = {
 'A':'01110/10001/10001/11111/10001/10001/10001',
 'B':'11110/10001/10001/11110/10001/10001/11110',
 'C':'01111/10000/10000/10000/10000/10000/01111',
 'D':'11110/10001/10001/10001/10001/10001/11110',
 'E':'11111/10000/10000/11110/10000/10000/11111',
 'F':'11111/10000/10000/11110/10000/10000/10000',
 'G':'01111/10000/10000/10111/10001/10001/01110',
 'H':'10001/10001/10001/11111/10001/10001/10001',
 'I':'11111/00100/00100/00100/00100/00100/11111',
 'J':'00111/00010/00010/00010/10010/10010/01100',
 'K':'10001/10010/10100/11000/10100/10010/10001',
 'L':'10000/10000/10000/10000/10000/10000/11111',
 'M':'10001/11011/10101/10101/10001/10001/10001',
 'N':'10001/11001/10101/10011/10001/10001/10001',
 'O':'01110/10001/10001/10001/10001/10001/01110',
 'P':'11110/10001/10001/11110/10000/10000/10000',
 'Q':'01110/10001/10001/10001/10101/10010/01101',
 'R':'11110/10001/10001/11110/10100/10010/10001',
 'S':'01111/10000/10000/01110/00001/00001/11110',
 'T':'11111/00100/00100/00100/00100/00100/00100',
 'U':'10001/10001/10001/10001/10001/10001/01110',
 'V':'10001/10001/10001/10001/10001/01010/00100',
 'W':'10001/10001/10001/10101/10101/10101/01010',
 'X':'10001/10001/01010/00100/01010/10001/10001',
 'Y':'10001/10001/01010/00100/00100/00100/00100',
 'Z':'11111/00001/00010/00100/01000/10000/11111',
 '0':'01110/10001/10011/10101/11001/10001/01110',
 '1':'00100/01100/00100/00100/00100/00100/01110',
 '2':'01110/10001/00001/00010/00100/01000/11111',
 '3':'11110/00001/00001/01110/00001/00001/11110',
 '4':'00010/00110/01010/10010/11111/00010/00010',
 '5':'11111/10000/10000/11110/00001/00001/11110',
 '6':'01110/10000/10000/11110/10001/10001/01110',
 '7':'11111/00001/00010/00100/01000/01000/01000',
 '8':'01110/10001/10001/01110/10001/10001/01110',
 '9':'01110/10001/10001/01111/00001/00001/01110',
 ' ':'00000/00000/00000/00000/00000/00000/00000',
 '-':'00000/00000/00000/11111/00000/00000/00000',
 '/':'00001/00001/00010/00100/01000/10000/10000',
 '.':'00000/00000/00000/00000/00000/01100/01100',
 ':':'00000/01100/01100/00000/01100/01100/00000',
 '=':'00000/11111/00000/11111/00000/00000/00000',
 '+':'00000/00100/00100/11111/00100/00100/00000',
}

def titulo_pixels(im, texto, x, y, esc=2, rgb=(.92,.96,1.0)):
    texto = texto.upper()
    for ch in texto:
        glyph = GLYPHS.get(ch, GLYPHS[' ']).split('/')
        for dy,linha in enumerate(glyph):
            for dx, bit in enumerate(linha):
                if bit == '1':
                    im[y+dy*esc:y+(dy+1)*esc,
                       x+dx*esc:x+(dx+1)*esc,0:3] = rgb
        x += esc*6

def preencher(im,x0,y0,x1,y1,rgb):
    im[y0:y1,x0:x1,0:3]=rgb
    im[y0:y1,x0:x1,3]=1.0

def ler_rgba_png_com_blender(arquivo):
    image = bpy.data.images.load(str(arquivo),check_existing=False)
    try:
        w,h=image.size
        px=np.empty(w*h*4,dtype=np.float32)
        image.pixels.foreach_get(px)
        return np.flipud(px.reshape((h,w,4))).copy()
    finally:
        bpy.data.images.remove(image)

def salvar_rgba_png_com_blender(arquivo,arr):
    h,w,_ = arr.shape
    imagem=bpy.data.images.new('AC04_TEMP_Comparacao_V3',width=w,height=h,alpha=True,float_buffer=False)
    try:
        # Pixel arrays do Blender usam origem inferior esquerda.
        imagem.pixels.foreach_set(np.ascontiguousarray(np.flipud(arr)).ravel())
        imagem.filepath_raw=str(arquivo)
        imagem.file_format='PNG'
        imagem.save()
    finally:
        bpy.data.images.remove(imagem)

def recortar(src, cx,cy,cw,ch):
    h,w,_=src.shape
    x0=max(0,round(cx-cw/2)); x1=min(w,round(cx+cw/2))
    y0=max(0,round(cy-ch/2)); y1=min(h,round(cy+ch/2))
    return src[y0:y1,x0:x1,:]

def encaixar_no_quadro(dest,source,x0,y0,largura,altura):
    sh,sw,_=source.shape
    if sh==0 or sw==0:return
    scale=min(largura/sw,altura/sh)
    ww=max(1,round(sw*scale)); hh=max(1,round(sh*scale))
    ys=(np.arange(hh)/scale).astype(np.int32).clip(0,sh-1)
    xs=(np.arange(ww)/scale).astype(np.int32).clip(0,sw-1)
    px=source[ys[:,None],xs[None,:]]
    xx=x0+(largura-ww)//2; yy=y0+(altura-hh)//2
    dest[yy:yy+hh,xx:xx+ww,:]=px

def criar_comparacao(arquivo_render,arquivo_comparacao):
    from bpy_extras.object_utils import world_to_camera_view
    origem=ler_rgba_png_com_blender(arquivo_render)
    h,w,_=origem.shape
    painel=np.empty((900,1920,4),dtype=np.float32)
    painel[:,:,:3]=(.012,.024,.047); painel[:,:,3]=1.0
    preencher(painel,0,0,1920,108,(.026,.051,.085))
    titulo_pixels(painel,'AC04 / COMPARACAO DE MATERIAIS',50,27,3)
    titulo_pixels(painel,'MESMA CAMERA - MESMA LUZ - MESMO FRAME',52,75,2,(.60,.76,.87))

    itens=[
      ('01 / LAMBERT', 'PLATAFORMA', 'DIFUSO / SEM BRILHO', 'DIFFUSE BSDF',
       (0,0.55,.70),(.50,.50),(.52,.50),(.54,.70,.82)),
      ('02 / PHONG', 'PORTAL', 'RUGOSIDADE 0.20', 'IOR LEVEL 0.55',
       (0,1.5,4.12),(.44,.78),(.49,.52),(.22,.55,.97)),
      ('03 / BLINN-PHONG','TORRES','RUGOSIDADE 0.10','IOR LEVEL 0.85',
       (-6.33,.30,3.45),(.23,.82),(.20,.52),(1.0,.61,.21))
    ]
    # Centros e áreas de recorte dependem de coordenadas PROJETADAS pela câmera.
    # Portanto não são números fixos da captura e funcionam se a câmera mudar.
    for idx,(titulo,nome,linha1,linha2,ponto,frac,_,cor) in enumerate(itens):
        x0=42+idx*620
        preencher(painel,x0,131,x0+596,801,(.035,.057,.086))
        preencher(painel,x0,131,x0+596,137,cor)
        titulo_pixels(painel,titulo,x0+24,154,3,cor)
        titulo_pixels(painel,nome,x0+24,199,2,(.90,.95,1.0))
        preencher(painel,x0+15,246,x0+581,637,(.010,.019,.033))
        p=world_to_camera_view(scene,camera,Vector(ponto))
        cx=int(p.x*w);cy=int((1-p.y)*h)
        cw=int(frac[0]*w);ch=int(frac[1]*h)
        crop=recortar(origem,cx,cy,cw,ch)
        encaixar_no_quadro(painel,crop,x0+22,252,552,378)
        preencher(painel,x0+23,656,x0+573,659,cor)
        titulo_pixels(painel,linha1,x0+26,683,2,(.91,.94,.97))
        titulo_pixels(painel,linha2,x0+26,728,2,(.69,.80,.88))

    titulo_pixels(painel,'PLATAFORMA = FOSCA   /   PORTAL = ESPECULAR   /   TORRES = BRILHO FORTE',
                  45,825,2,(.73,.84,.94))
    titulo_pixels(painel,'PHONG E BLINN-PHONG: APROXIMACOES PBR / NAO EQUACOES CLASSICAS',
                  45,866,2,(.53,.71,.81))
    salvar_rgba_png_com_blender(arquivo_comparacao,painel)

# =================== 6. GERAR IMAGENS E PROJETO ==========================
scene['AC04_V3_Aplicado']=True
scene['AC04_V3_Foco']='Marca desobstruida; comparacao em 3 recortes do mesmo render'
scene['AC04_V3_Iluminacao']='Area key 3750 W / disco 2.3m; fill 350 W / disco 7.5m'
scene['AC04_V3_Objetos_Autorais']='Obj_PlataformaAscensao; Obj_PortalFuturo; Obj_TorresConexao'

saida_blend=escolher_nome_saida(PASTA, 'AC04_HenriqueSartori.blend')
render_final=PASTA/'AC04_RenderFinal.png'
render_base=PASTA/'AC04_TEMP_BaseComparacao.png'
render_comparacao=PASTA/'AC04_Comparacao.png'
relatorio=PASTA/'AC04_Relatorio.md'

# Salva tambem ANTES da renderizacao: se o render falhar, o .blend ja existe.
try:
    bpy.ops.file.pack_all()
except Exception as exc:
    print('[AC04] Aviso ao empacotar bibliotecas:', exc)
scene.render.filepath=str(render_final)
bpy.ops.wm.save_as_mainfile(filepath=str(saida_blend), check_existing=False)

if RENDERIZAR:
    print('[V3] Renderizando cena final com Ibmec...')
    scene.render.filepath=str(render_final)
    bpy.ops.render.render(write_still=True)
    print('[V3] Renderizando base da comparacao (sem ocultar nenhum objeto autoral)...')
    # Temporariamente oculta somente os caracteres da marca e sua sombra,
    # para ver o brilho do material do portal sem a marca cobrir suas superfícies.
    sombra=bpy.data.objects.get('AUX_Contorno_Da_Marca_NaoAutoral')
    ocultos=[(marca,marca.hide_render)]
    if sombra: ocultos.append((sombra,sombra.hide_render))
    try:
        for ob,_ in ocultos: ob.hide_render=True
        scene.render.filepath=str(render_base)
        bpy.ops.render.render(write_still=True)
    finally:
        for ob,anterior in ocultos: ob.hide_render=anterior
    if tuple((o.name,tuple(o.location),tuple(o.rotation_euler),o.data.energy,o.data.size,
              tuple(o.data.color)) for o in (key,fill))!=setup_luzes:
        raise RuntimeError('Uma luz mudou entre os renders; a comparacao foi cancelada.')
    try:
        criar_comparacao(render_base,render_comparacao)
        print('[V3] Comparação tripla criada:',render_comparacao)
        render_base.unlink(missing_ok=True)
    except Exception as exc:
        print('[V3] Falha ao montar o painel; render-base preservado:',render_base)
        raise RuntimeError('Falha ao gerar painel comparativo: '+str(exc)) from exc

# O .blend ja foi salvo apos todas as melhorias e com texturas empacotadas.
# As renderizacoes sao saidas externas; nao ha necessidade de salvar novamente,
# o que tambem evita criar backup .blend1 desnecessario.
scene.render.filepath=str(render_final)

relatorio.write_text(f'''# AC04 — Ibmec: Arquitetura do Futuro — V3

**Aluno:** Henrique Sartori  
**Software:** Blender 4.5 LTS  
**Arquivo:** `{saida_blend.name}`  
**Origem:** recriação procedural independente do conceito planejado para a AP1; não utiliza o arquivo .blend original da AP1.

## Conceito e composição da cena
A palavra Ibmec permanece legível no centro de uma composição tecnológica, emoldurada pelo portal, pelas torres simétricas e pelo pódio escalonado. A composição final reposiciona a antena de Kenney que ficaria entre as letras, amplia o portal e ajusta o enquadramento antes do primeiro render. A modelagem dos três objetos autorais foi preservada.

## Os três materiais e objetos

| Objeto autoral | Material | Shader | Cor RGB | Rugosidade | Especular/IOR Level |
|---|---|---|---|---|---|
| `Obj_PlataformaAscensao` | `MAT_Lambert` | Diffuse BSDF (apenas difuso) | (0.49, 0.61, 0.73) | 0 no nó Diffuse | Não se aplica: sem componente especular |
| `Obj_PortalFuturo` | `MAT_Phong` | Principled BSDF | (0.11, 0.32, 0.71) | 0.20 | 0.55 |
| `Obj_TorresConexao` | `MAT_BlinnPhong` | Principled BSDF | (0.73, 0.45, 0.13) | 0.10 | 0.85 |

Lambert foi representado diretamente pelo nó Diffuse BSDF. **Phong e Blinn-Phong são aproximações visuais por Principled BSDF**: esse nó não implementa literalmente suas equações de iluminação. O controle usado no Blender 4.5 é *IOR Level*, associado à resposta especular do shader.

## Iluminação padronizada
- Luz principal: Area Disk, **3750 W**, cor RGB **(1, 0.93, 0.85)**, localização **(-5.6, -8, 10.6)**, tamanho **2.3 m**.
- Preenchimento: Area Disk, **350 W**, RGB **(0.64, 0.80, 1)**, localização **(7.8, -5.2, 7.3)**, tamanho **7.5 m**.
- A **mesma câmera**, as **mesmas luzes** e o **frame 360** foram usados para os três objetos.
- A imagem comparativa mostra **três recortes de uma única renderização**, sem mover a câmera ou alterar as fontes de luz. A palavra Ibmec e seu contorno foram temporariamente ocultados nessa captura auxiliar para permitir observar o material do portal; nenhum objeto autoral foi ocultado ou modificado.

## Comparação dos modelos
- **Lambert / plataforma:** prevalece a variação de iluminação por orientação das faces. A superfície apresenta difusão sem ponto especular concentrado.
- **Phong / portal:** o shader é mais polido e pode produzir realces especulares nas superfícies curvas do aro, devido à rugosidade 0.20 e IOR Level 0.55.
- **Blinn-Phong / torres:** a rugosidade menor (0.10) e IOR Level maior (0.85) favorecem um destaque especular mais concentrado quando as faces estão orientadas para a reflexão observável.
- **Ângulo de iluminação:** ao variar a posição da luz, alteram-se a distribuição da componente difusa e as regiões de highlight; as imagens finais foram geradas após fixar a luz em uma única configuração. Esta é a expectativa física, não uma afirmação de que um experimento manual com a luz foi realizado.

## Recursos externos
- **Kenney Space Kit:** três modelos de antenas GLB, licença CC0, usados como elementos auxiliares. A antena central foi deslocada para não comprometer a legibilidade da marca. Fonte: https://kenney.nl/assets/space-kit
- **Poly Haven Metal Plate:** mapas de cor, roughness e normal de metal, licença CC0, aplicados à placa auxiliar. Fonte: https://polyhaven.com/a/metal_plate
- A modelagem desses recursos não é contabilizada como autoral; os três modelos autorais estão identificados em coleção própria.

## Desafios e soluções
O principal desafio previsto foi a sobreposição visual entre uma antena central e a tipografia, somada à comparação que repetia o render com outra legenda. Na cena final, o objeto externo foi deslocado, a marca ganhou separação espacial e a comparação passou a apresentar três painéis de detalhe provenientes do mesmo render e sob a mesma iluminação.

**Antes de entregar:** examine os dois renders, descreva SOMENTE diferencas observadas e confira a fonte/cor da palavra Ibmec com a identidade institucional. Não foram usadas as equações clássicas de Phong e Blinn-Phong.
''',encoding='utf-8')

print('\n[V3] SUCESSO. Saídas:')
for f in [saida_blend,render_final,render_comparacao,relatorio]:
    print('    ',f)
print('[V3] Os três objetos autorais e seus materiais originais foram preservados.')
