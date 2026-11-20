# MANUAL - Automação de Tenant e VRF no Cisco ACI

Este manual explica como usar os scripts de criação e exclusão de Tenants e VRFs
no Cisco ACI via API REST do APIC.

Público-alvo: analistas juniores de rede/infraestrutura.

---

## 1. Visão geral

A pasta `tenant/` contém os seguintes scripts:

| Script | Função | Arquivo de entrada padrão |
|--------|--------|---------------------------|
| `create-tenant-vrf-prod.py` | Cria Tenants, VRFs e Application Profiles | `tenant-vrf.txt` (via `--arquivo`) |
| `delete-tenant-vrf-prod.py` | Deleta VRFs e Tenants | `delete-tenant-vrf.txt` (padrão automático) |
| `config.ini` | Configurações padrão do APIC (URL, usuário, senha) | — |

O que os scripts fazem:
1. Pedem **usuário e senha na tela** (a senha não aparece ao digitar).
2. Autenticam no APIC.
3. Verificam se cada Tenant/VRF **já existe** antes de criar ou excluir.
4. Criam ou deletam os Tenants/VRFs solicitados.
5. Mostram um **relatório na tela** (criados, pulados, falhas) e opcionalmente salvam em arquivo de log (`--log-file`).

Nunca armazene senhas no código. Use o `config.ini` apenas para a URL do APIC (opcional).

---

## 2. Formato dos arquivos de entrada

Os arquivos de texto devem ter uma linha por Tenant/VRF.

### Formato aceito (criação)

```
tenant,vrf,ap1,ap2
```

As colunas são:

| Coluna | Campo | Obrigatório? | Descrição |
|--------|-------|--------------|-----------|
| 1 | tenant | Sim | Nome do Tenant no ACI |
| 2 | vrf | Sim | Nome da VRF associada ao tenant |
| 3 | ap1 | Não | Primeiro Application Profile (ex: AP_DADOS) |
| 4 | ap2 | Não | Segundo Application Profile (ex: AP_GERENCIA) |

Se omitir as colunas de AP, nenhum Application Profile será criado.

Exemplo (`tenant-vrf.txt`):

```
HUAWEI,VRF_DCS_HUAWEI,AP_DADOS,AP_GERENCIA
OUTRO-TENANT,VRF_DEV,AP_DADOS
TERCEIRO,VRF_PROD
QUARTO,VRF_TESTE,AP_CUSTOM01
```

Regras:
- Linhas iniciando com `#` são ignoradas (comentários).
- Linhas em branco são ignoradas.
- Você pode informar quantos APs quiser nas colunas 3 em diante.

### Formato aceito (exclusão)

```
tenant,vrf
```

Ou apenas o tenant (se quiser deletar só o tenant sem especificar VRF):

```
tenant
```

Exemplo (`delete-tenant-vrf.txt`):

```
HUAWEI,VRF_DCS_HUAWEI
OUTRO-TENANT,VRF_DEV
TERCEIRO
```

Regras:
- **Coluna 1:** nome do Tenant.
- **Coluna 2 (opcional):** nome da VRF. Se omitir, o script tenta deletar apenas o Tenant.
- Na exclusão, a VRF é deletada primeiro e depois o Tenant.

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
| `--tenant` (com ou sem `--vrf`) | Usa **apenas** o tenant informado na linha de comando e ignora o arquivo padrão |
| Somente `--arquivo` (ou nada) | Lê o arquivo padrão (`tenant-vrf.txt` ou `delete-tenant-vrf.txt`) |

Isso significa que se você quer deletar/criar um tenant específico, use `--tenant` diretamente. Se quer processar vários de uma vez, use o arquivo.

### 3.1 Criar Tenant + VRF + Application Profile (modo simples)

Todos os exemplos abaixo usam linha de comando direta (sem arquivo):

**Criar Tenant + VRF (sem Application Profile):**
```bash
python3 tenant/create-tenant-vrf-prod.py --tenant HUAWEI --vrf VRF_DCS_HUAWEI -v
```

**Criar Tenant + VRF + apenas 1 AP:**
```bash
python3 tenant/create-tenant-vrf-prod.py --tenant HUAWEI --vrf VRF_DCS_HUAWEI --ap AP_DADOS -v
```

**Criar Tenant + VRF + 2 APs (padrão):**
```bash
python3 tenant/create-tenant-vrf-prod.py --tenant HUAWEI --vrf VRF_DCS_HUAWEI --ap AP_DADOS --ap AP_GERENCIA -v
```

**Criar Tenant + VRF + AP com nome customizado:**
```bash
python3 tenant/create-tenant-vrf-prod.py --tenant NOVO-TENANT --vrf VRF_NOVO --ap AP_MEU_PROJETO -v
```

Parâmetros:
- `--tenant` : nome do tenant
- `--vrf` : nome da VRF
- `--ap` : nome do Application Profile (opcional, repita para vários)
- `-v` : modo verbose (mostra detalhes passo a passo)
- `--log-file nome.log` : salva o relatório também em arquivo

### 3.2 Criar vários Tenants + VRFs + APs via arquivo (recomendado para produção)

```bash
python3 tenant/create-tenant-vrf-prod.py --arquivo tenant/tenant-vrf.txt -v --log-file criar.log
```

Cada linha do arquivo define seu próprio tenant, VRF e Application Profiles opcionais.

### 3.3 Excluir VRF + Tenant via arquivo

O script procura por padrão o arquivo `delete-tenant-vrf.txt` na pasta `tenant/`.

```bash
python3 tenant/delete-tenant-vrf-prod.py -v --log-file deletar.log
```

Ou informe outro nome de arquivo:

```bash
python3 tenant/delete-tenant-vrf-prod.py --arquivo tenant/minha-lista-delete.txt -v
```

### 3.4 Excluir Tenant e/ou VRF (modo simples)

Todos os exemplos abaixo usam linha de comando direta (sem arquivo):

**Deletar apenas o Tenant (sem especificar VRF):**
```bash
python3 tenant/delete-tenant-vrf-prod.py --tenant HUAWEI -v
```

**Deletar VRF específica + Tenant:**
```bash
python3 tenant/delete-tenant-vrf-prod.py --tenant HUAWEI --vrf VRF_DCS_HUAWEI -v
```

O que acontece na exclusão:
1. Se você informou `--vrf`: o script tenta deletar a VRF primeiro
2. Depois o script tenta deletar o Tenant
3. Se o Tenant ou VRF não existirem, o script apenas informa "pulando" e continua

---

---

## 4. Exemplos práticos

### Cenário A: Criar vários Tenants com suas VRFs e Application Profiles

Arquivo `tenant-vrf.txt`:

```
TENANT_PROD,VRF_PROD,AP_DADOS,AP_GERENCIA
TENANT_DEV,VRF_DEV,AP_DADOS
TENANT_HOMOLOG,VRF_HOMOLOG
```

Execução:

```bash
python3 tenant/create-tenant-vrf-prod.py --arquivo tenant/tenant-vrf.txt -v --log-file criar_prod.log
```

### Cenário B: Excluir apenas VRFs específicas

Arquivo `delete-tenant-vrf.txt`:

```
TENANT_DEV,VRF_DEV_ANTIGA
TENANT_HOMOLOG,VRF_HOMOLOG_ANTIGA
```

Execução:

```bash
python3 tenant/delete-tenant-vrf-prod.py -v --log-file deletar_antigas.log
```

---

## 5. Interpretando o relatório

Exemplo de saída na tela (criação):

```
======================================================================
REPORT - CRIAÇÃO DE TENANT E VRF
======================================================================
APIC   : https://172.30.104.5
Usuário: 80689851
Qtd itens: 2
----------------------------------------------------------------------
🔎 Verificando Tenant 'HUAWEI' -> não encontrado
🧱 Criando Tenant 'HUAWEI'... Status: 200
✅ Tenant 'HUAWEI' criado com sucesso.
🔎 Verificando VRF 'HUAWEI/VRF_DCS_HUAWEI' -> não encontrado
🌐 Criando VRF 'HUAWEI/VRF_DCS_HUAWEI'... Status: 200
✅ VRF 'HUAWEI/VRF_DCS_HUAWEI' criada com sucesso.
🔎 Verificando AP 'HUAWEI/AP_DADOS' -> não encontrado
📦 Criando AP 'HUAWEI/AP_DADOS'... Status: 200
✅ AP 'HUAWEI/AP_DADOS' criado com sucesso.
🔎 Verificando AP 'HUAWEI/AP_GERENCIA' -> não encontrado
📦 Criando AP 'HUAWEI/AP_GERENCIA'... Status: 200
✅ AP 'HUAWEI/AP_GERENCIA' criado com sucesso.
----------------------------------------------------------------------
RESUMO
----------------------------------------------------------------------
Tenants processados: 1
  📦 HUAWEI
Tenants criados : 1
  ✅ HUAWEI
Tenants pulados : 0
VRFs criadas    : 1
  ✅ HUAWEI/VRF_DCS_HUAWEI
VRFs puladas    : 0
APs criados     : 2
  ✅ HUAWEI/AP_DADOS
  ✅ HUAWEI/AP_GERENCIA
APs pulados     : 0
Falhas          : 0
======================================================================
```

Exemplo de saída na tela (exclusão):

```
======================================================================
REPORT - EXCLUSÃO DE TENANT E VRF
======================================================================
APIC   : https://172.30.104.5
Usuário: 80689851
Qtd itens: 2
----------------------------------------------------------------------
🔎 Verificando VRF 'HUAWEI/VRF_DCS_HUAWEI' -> encontrado
🗑️  Deletando VRF 'HUAWEI/VRF_DCS_HUAWEI'... Status: 200
✅ VRF 'HUAWEI/VRF_DCS_HUAWEI' deletada com sucesso.
🔎 Verificando Tenant 'HUAWEI' -> encontrado
🗑️  Deletando Tenant 'HUAWEI'... Status: 200
✅ Tenant 'HUAWEI' deletado com sucesso.
----------------------------------------------------------------------
RESUMO
----------------------------------------------------------------------
Tenants processados: 1
  📦 HUAWEI
VRFs deletadas   : 1
  🗑️  HUAWEI/VRF_DCS_HUAWEI
VRFs puladas     : 0
Tenants deletados: 1
  🗑️  HUAWEI
Tenants pulados  : 0
Falhas           : 0
======================================================================
```

Significado dos status:
- ✅ **Criado/Deletado com sucesso:** operação concluída no APIC.
- ⚠️ **Pulado:** o Tenant/VRF já existia (criação) ou não existia (exclusão). Nenhuma ação foi tomada.
- ❌ **Falha:** erro de rede ou rejeição pelo APIC. Verifique o log e as credenciais.

---

## 6. Ordem de exclusão

Ao excluir, o script segue esta ordem:
1. Primeiro tenta deletar a **VRF** (se informada no arquivo).
2. Depois tenta deletar o **Tenant**.

Isso é importante porque um Tenant com VRFs associadas pode rejeitar a exclusão até que as VRFs sejam removidas.

---

## 7. Credenciais e segurança

- Os scripts **não contêm senha hardcoded**.
- Ao executar, você será perguntado:
  ```
  Usuário APIC: 80689851
  Senha APIC: <digite aqui, não aparece na tela>
  ```
- Você pode passar `--user` e `--pass` na linha de comando se quiser automatizar, mas o recomendado para uso manual é digitar na tela.
- O arquivo `config.ini` pode conter a URL do APIC. Usuário e senha nele são opcionais e não recomendados para produção.

---

## 8. Arquivos na pasta `tenant/`

```
tenant/
├── create-tenant-to-ap-profile-prod.py        # Script original (manter como referência)
├── create-tenant-to-vrf-ap-profile-prod.py   # Script original (manter como referência)
├── create-tenant-vrf-prod.py                  # Script novo de criação (recomendado)
├── delete-tenant-vrf-prod.py                  # Script novo de exclusão
├── config.ini                                 # Configurações padrão do APIC (opcional)
├── tenant-vrf.txt                     # Exemplo de entrada para criação
├── delete-tenant-vrf.txt                      # Exemplo de entrada para exclusão
└── MANUAL_TENANT_VRF.md                       # Este arquivo
```

---

## 9. Checklist antes de rodar em produção

- [ ] Verifique se o arquivo de entrada está com o formato correto (`tenant,vrf` ou `tenant,vrf,ap1,ap2`).
- [ ] Confirme os nomes dos Tenants e VRFs no APIC antes de rodar.
- [ ] Rode primeiro com `-v` para ver o que será feito.
- [ ] Use `--log-file` para guardar evidência da execução.
- [ ] Nunca compartilhe arquivos de log que contenham senhas (os logs destes scripts não gravam senhas).
- [ ] Ao excluir, lembre-se: deletar um Tenant remove tudo dentro dele (Application Profiles, BDs, etc.). Tenha certeza antes de executar.

---

## 10. Dúvidas comuns

**Q: Posso criar VRFs em tenants diferentes na mesma execução?**
A: Sim. Use o arquivo de entrada (`--arquivo`) com linhas diferentes para cada tenant.

**Q: Posso excluir uma VRF que não existe?**
A: Sim. O script verifica antes e apenas informa que não existe (pulado), não gera erro.

**Q: O script deleta Application Profiles ou BDs dentro do Tenant?**
A: Não diretamente. Ao deletar o Tenant, o APIC remove tudo que está dentro dele (VRFs, Application Profiles, BDs, etc.). Se quiser deletar só a VRF, informe apenas `--vrf` sem deletar o tenant.

**Q: Posso criar Application Profiles com nomes diferentes de AP_DADOS e AP_GERENCIA?**
A: Sim. Use `--ap NOME_CUSTOM` na linha de comando ou informe o nome na coluna 3+ do arquivo de entrada.

**Q: Posso criar apenas o Tenant sem VRF nem AP?**
A: Não neste script. O `--vrf` é obrigatório. Se quiser criar só o Tenant, informe qualquer VRF e ela será criada junto.

**Q: O script de exclusão deleta Application Profiles?**
A: Não. O `delete-tenant-vrf-prod.py` deleta apenas VRFs e Tenants. Ao deletar um Tenant, o APIC remove tudo dentro dele (incluindo APs e BDs).

**Q: Esqueci a senha. O que faço?**
A: O script não armazena senha. Peça ao responsável de segurança ou use seu usuário pessoal do APIC.

---

Fim do manual.
