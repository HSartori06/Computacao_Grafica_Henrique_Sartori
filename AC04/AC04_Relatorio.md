# AC04 — Ibmec: Arquitetura do Futuro — V3

**Aluno:** Henrique Sartori  
**Software:** Blender 4.5 LTS  
**Arquivo:** `AC04_HenriqueSartori_FINAL.blend`  
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
