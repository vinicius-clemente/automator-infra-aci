# MANUAL - Automação de EPG (Endpoint Group) no Cisco ACI

Este manual explica como usar os scripts de criação de Endpoint Groups (EPGs)
associados a Bridge Domains (BDs) no Cisco ACI via API REST do APIC.

Público-alvo: analistas juniores de rede/infraestrutura.

---

## 1. Visão geral

A pasta `epg/` contém os seguintes scripts:

| Script | Função | Arquivo de entrada padrão |
|--------|--------|---------------------------|
| `create-epg-to-bd-prod.py` | Cria um EPG único associado a um BD | — (modo linha de comando) |
| `create-epgs-to-bds-prod.py` | Cria vários EPGs associados a BDs | `epgs.txt` (via `--arquivo`) |
| `config.ini` | Configurações padrão do APIC (URL, usuário, senha) | — |

O que os scripts fazem:
1. Pedem **usuário e senha na tela** (a senha não aparece ao digitar).
2. Autenticam no APIC.
3. Verificam se o Tenant, Application Profile e BD **já existem** antes de criar o EPG.
4. Verificam se o EPG **já existe** antes de criar (pula se existir).
5. Criam o EPG e o associam ao BD informado.
6. Mostram um **relatório na tela** (criados, pulados, falhas) e opcionalmente salvam em arquivo de log (`--log-file`).

**Importante:** O Tenant, Application Profile e BD devem **já existir** no ACI antes de criar o EPG. Se algum não existir, o script informa o erro e não cria o EPG.

Nunca armazene senhas no código. Use o `config.ini` apenas para a URL do APIC (opcional).

---

## 2. Formato dos arquivos de entrada

Os arquivos de texto devem ter uma linha por EPG.

### Formato aceito (criação)

```
tenant,app_profile,epg,bd
```

As colunas são:

| Coluna | Campo | Obrigatório? | Descrição |
|--------|-------|--------------|-----------|
| 1 | tenant | Sim | Nome do Tenant no ACI |
| 2 | app_profile | Sim | Nome do Application Profile |
| 3 | epg | Sim | Nome do Endpoint Group |
| 4 | bd | Sim | Nome do Bridge Domain associado |

Exemplo (`epgs.txt`):

```
TENANT_EXEMPLO,AP_DADOS,EPG_CLIENTES,BD_CLIENTES
TENANT_EXEMPLO,AP_DADOS,EPG_SERVIDORES,BD_SERVIDORES
OUTRO-TENANT,AP_GERENCIA,EPG_GER,BD_GER
TERCEIRO,AP_DADOS,EPG_WEB,BD_WEB
TERCEIRO,AP_DADOS,EPG_APP,BD_APP
TERCEIRO,AP_DADOS,EPG_DB,BD_DB
```

Regras:
- Linhas iniciando com `#` são ignoradas (comentários).
- Linhas em branco são ignoradas.
- Todas as 4 colunas são obrigatórias.

---

## 3. Como executar os scripts

### Pré-requisitos

- Python 3 instalado
- Biblioteca `requests` instalada (`pip install requests`)
- Acesso de rede ao APIC (exemplo: `https://172.30.104.5`)

### Prioridade: linha de comando vs arquivo

Os scripts aceitam tanto argumentos na linha de comando quanto arquivo de entrada. A regra de prioridade é:

| Se você passar... | O script faz... |
|-------------------|-----------------|
| `--tenant` (com `--ap`, `--epg`, `--bd`) | Usa **apenas** os dados informados na linha de comando e ignora o arquivo padrão |
| Somente `--arquivo` (ou nada) | Lê o arquivo padrão (`epgs.txt`) |

---

### 3.1 Criar um EPG único (modo simples)

```bash
python3 epg/create-epg-to-bd-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG_CLIENTES --bd BD_CLIENTES -v
```

Parâmetros:
- `--tenant` : nome do tenant (obrigatório)
- `--ap` : nome do Application Profile (obrigatório)
- `--epg` : nome do EPG (obrigatório)
- `--bd` : nome do Bridge Domain associado (obrigatório)
- `-v` : modo verbose (mostra detalhes passo a passo)
- `--log-file nome.log` : salva o relatório também em arquivo

---

### 3.2 Criar vários EPGs via arquivo (recomendado para produção)

```bash
python3 epg/create-epgs-to-bds-prod.py --arquivo epg/epgs.txt -v --log-file criar.log
```

Cada linha do arquivo define seu próprio tenant, AP, EPG e BD.

---

### 3.3 Criar vários EPGs via linha de comando (modo simples)

Quando todos os EPGs são do mesmo tenant e mesmo AP:

```bash
python3 epg/create-epgs-to-bds-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG1 --epg EPG2 --epg EPG3 --bd BD1 --bd BD2 --bd BD3 -v
```

**Regras:**
- A quantidade de `--epg` deve ser igual à quantidade de `--bd`
- Eles são associados em ordem: EPG1 com BD1, EPG2 com BD2, etc.

---

## 4. Exemplos práticos

### Cenário A: Criar um EPG único

```bash
python3 epg/create-epg-to-bd-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG_CLIENTES --bd BD_CLIENTES -v
```

### Cenário B: Criar vários EPGs com BDs diferentes

Arquivo `epgs.txt`:

```
TENANT_PROD,AP_DADOS,EPG_WEB,BD_WEB
TENANT_PROD,AP_DADOS,EPG_APP,BD_APP
TENANT_PROD,AP_DADOS,EPG_DB,BD_DB
TENANT_DEV,AP_GERENCIA,EPG_DEV,BD_DEV
```

Execução:

```bash
python3 epg/create-epgs-to-bds-prod.py --arquivo epg/epgs.txt -v --log-file criar_epgs.log
```

### Cenário V: Vários EPGs no mesmo AP via linha de comando

```bash
python3 epg/create-epgs-to-bds-prod.py --tenant TENANT_PROD --ap AP_DADOS --epg EPG_A --epg EPG_B --epg EPG_C --bd BD_A --bd BD_B --bd BD_C -v
```

---

## 5. Interpretando o relatório

Exemplo de saída na tela:

```
======================================================================
REPORT - CRIAÇÃO DE EPGs ASSOCIADOS A BDs
======================================================================
APIC   : https://172.30.104.5
Usuário: 80689851
Qtd EPG: 3
----------------------------------------------------------------------
🔎 Verificando Tenant 'TENANT_EXEMPLO' -> encontrado
🔎 Verificando AP 'TENANT_EXEMPLO/AP_DADOS' -> encontrado
🔎 Verificando BD 'TENANT_EXEMPLO/BD_CLIENTES' -> encontrado
🔎 Verificando EPG 'TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES' -> não encontrado
📦 Criando EPG 'TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES' associado ao BD 'BD_CLIENTES'... Status: 200
✅ EPG 'TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES' criado com sucesso e associado ao BD 'BD_CLIENTES'.
🔎 Verificando EPG 'TENANT_EXEMPLO/AP_DADOS/EPG_SERVIDORES' -> já encontrado
⚠️  EPG 'TENANT_EXEMPLO/AP_DADOS/EPG_SERVIDORES' já existe. Pulando.
----------------------------------------------------------------------
RESUMO
----------------------------------------------------------------------
Tenants processados: 1
  📦 TENANT_EXEMPLO
APs processados: 1
  📁 TENANT_EXEMPLO/AP_DADOS
EPGs criados : 1
  ✅ TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES (BD: BD_CLIENTES)
EPGs pulados : 1
  ⚠️  TENANT_EXEMPLO/AP_DADOS/EPG_SERVIDORES
Falhas       : 0
======================================================================
```

Significado dos status:
- ✅ **Criado com sucesso:** operação concluída no APIC.
- ⚠️ **Pulado:** o EPG já existia. Nenhuma ação foi tomada.
- ❌ **Falha:** erro de rede, rejeição pelo APIC, ou algum componente pai (Tenant, AP ou BD) não existe. Verifique o log e as credenciais.

---

## 6. Credenciais e segurança

- Os scripts **não contêm senha hardcoded**.
- Ao executar, você será perguntado:
  ```
  Usuário APIC: 80689851
  Senha APIC: <digite aqui, não aparece na tela>
  ```
- Você pode passar `--user` e `--pass` na linha de comando se quiser automatizar, mas o recomendado para uso manual é digitar na tela.
- O arquivo `config.ini` pode conter a URL do APIC. Usuário e senha nele são opcionais e não recomendados para produção.

---

## 7. Arquivos na pasta `epg/`

```
epg/
├── create-epg-to-bd-prod.py       # Script novo de criação de um EPG
├── create-epgs-to-bds-prod.py     # Script novo de criação de vários EPGs
├── create-epg-to-bd-prod.py       # Script original (manter como referência)
├── create-epgs-to-bds-prod.py     # Script original (manter como referência)
├── config.ini                     # Configurações padrão do APIC (opcional)
├── epgs.txt                       # Exemplo de entrada para criação
└── MANUAL_EPG.md                  # Este arquivo
```

---

## 8. Checklist antes de rodar em produção

- [ ] Verifique se o arquivo de entrada (`epgs.txt`) está com o formato correto (`tenant,app_profile,epg,bd`).
- [ ] Confirme se o Tenant, Application Profile e BD já existem no ACI. O script não cria esses componentes, apenas valida se existem.
- [ ] Rode primeiro com `-v` para ver o que será feito sem surpresas.
- [ ] Use `--log-file` para guardar evidência da execução.
- [ ] Nunca compartilhe arquivos de log que contenham senhas (os logs destes scripts não gravam senhas).

---

## 9. Dúvidas comuns

**Q: Posso criar EPGs em tenants diferentes na mesma execução?**
A: Sim. Use o arquivo de entrada (`--arquivo`) com linhas diferentes para cada tenant.

**Q: Posso criar um EPG sem informar o BD?**
A: Não. O BD é obrigatório, pois o EPG precisa ser associado a um Bridge Domain.

**Q: O script cria o Tenant, AP ou BD se não existirem?**
A: Não. Ele apenas valida se existem. Se algum não existir, o EPG não é criado e o script informa o erro.

**Q: Posso excluir EPGs com esses scripts?**
A: Não. Estes scripts só criam EPGs. Para exclusão, seria necessário criar um script separado de deleção.

**Q: Esqueci a senha. O que faço?**
A: O script não armazena senha. Peça ao responsável de segurança ou use seu usuário pessoal do APIC.

---

Fim do manual.
