# 🧭 Plugin QGIS – Validador de Regras PostGIS

Plugin para o QGIS desenvolvido pelo 2º CGEO/DSG que permite aplicar validações topológicas e semânticas diretamente sobre dados vetoriais armazenados em bancos PostgreSQL/PostGIS.

---

## 📌 Visão Geral

Este plugin tem como objetivo principal **executar regras espaciais diretamente no banco de dados**, utilizando funções PL/pgSQL baseadas em regras extraídas e convertidas para formato relacional. Com isso, evita-se a ida e volta de shapefiles entre QGIS e outras plataformas, otimizando tempo e assegurando a integridade dos dados.

---

## 🚀 Funcionalidades

- Conexão com bancos PostgreSQL/PostGIS.
- Listagem de schemas e funções disponíveis.
- Execução direta de funções de validação definidas em Schema.
- Geração automática de camadas de erro (`aux_revisao_*`, etc.).
- Interface intuitiva com log e feedback de progresso.
---

## 🏗 Arquitetura do Sistema

### Banco de Dados

Para elaboração do banco é necessario criar uma tabela relacional de regras que devem ser respeitadas, em exemplo utilizamos a tabela `spatial_rules_ICIS` com os seguintes campos:

| Campo         | Descrição                                       |
|---------------|-------------------------------------------------|
| source_code   | Código da feição curva                          |
| target_code   | Código da feição superfície                     |
| rule_type     | Tipo de regra (E, O, etc.)                      |
| base          | Nome da tabela curva no banco                   |
| alvo          | Nome da tabela superfície no banco              |
| attribute_rule| Regra condicional em SQL (quando aplicável)     |

Em seguida são elaborados funções de validação escritas em PL/pgSQL, por exemplo:

```sql
SELECT schema.ICIS_validation_check_E(); -- Regras do tipo E
SELECT schema.ICIS_validation_check_O(); -- Regras do tipo O
```
----

## 🔧 Instalação

1. Clone este repositório:
   ```bash
   git clone https://github.com/2cgeodsg/ValidadorDeRegras.git
   ```

2. Copie a pasta do plugin para o diretório de plugins do QGIS:
   - Windows: `C:\Users\<seu-usuário>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

3. Reinicie o QGIS e ative o plugin via `Complementos > Gerenciar e Instalar Complementos`.

***Certifique que o nome da pasta em 'QGIS3\profiles\default\python\plugins\' é "validador_regras"***
---

## ▶️ Como Usar

1. **Conecte-se ao banco:** Clique em “Gerenciar Conexões” e configure o acesso ao banco PostgreSQL/PostGIS.
2. **Selecione o schema:** Escolha o schema onde estão as funções de validação.
3. **Escolha a função:** O plugin filtra e exibe apenas as funções sem parâmetros.
4. **Execute:** Clique em “Play” para iniciar a validação. Os erros detectados serão exibidos no QGIS como camadas auxiliares (`aux_revisao_*`, etc).
---

## 👥 Autores

Desenvolvido por:

- Raphael Perrut (Cap)
- Jean Michael Estevez Alvarez (2º Sgt)
- Raphael Godinho (3º Sgt)
---

## 🧠 Referência Técnica

Este plugin foi documentado no [Relatório Técnico N° 05/2025 – DGEO/2ºCGEO](#), contendo todos os detalhes da estrutura relacional, lógica de validação e integração ao ecossistema do Exército Brasileiro.

---
