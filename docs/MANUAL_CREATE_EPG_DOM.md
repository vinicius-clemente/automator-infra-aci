# MANUAL - Associação de EPG a Physical Domain no Cisco ACI

Este manual explica como usar os scripts de associação de Endpoint Groups (EPGs)
a Physical Domains no Cisco ACI via API REST do APIC.

Público-alvo: analistas juniores de rede/infraestrutura.

---

## 1. Visão geral

A pasta `epg/` contém os seguintes scripts para associação EPG <-> Physical Domain:

| Script | Função | Arquivo de entrada padrão |
|--------|--------|---------------------------|
| `create-epg-to-dom-prod.py` | Associa um EPG a um Physical Domain | — (modo linha de comando) |
| `create-epgs-to-doms-prod.py` | Associa vários EPGs a Physical Domains | `epgs_doms.txt` (via `--arquivo`) |
| `delete-epg-from-dom-prod.py` | Desassocia EPGs de Physical Domains | `delete-epgs-doms.txt` (via `--arquivo`) |
| `config.ini` | Configurações padrão do APIC (URL, usuário, senha) | — |

O que os scripts de associação fazem:
1. Pedem **usuário e senha na tela** (a senha não aparece ao digitar).
2. Autenticam no APIC.
3. Verificam se o Tenant, Application Profile, EPG e Physical Domain **já existem**.
4. Verificam se a associação **já existe** antes de criar (pula se existir).
5. Criam a associação usando o objeto `fvRsDomAtt` com `tDn` apontando para `uni/phys-{domName}`.
6. Mostram um **relatório na tela** (associados, pulados, falhas) e opcionalmente salvam em arquivo de log (`--log-file`).

**Importante:** O Tenant, Application Profile, EPG e Physical Domain devem **já existir** no ACI antes de associar. Se algum não existir, o script informa o erro e não associa.

Nunca armazene senhas no código. Use o `config.ini` apenas para a URL do APIC (opcional).

---

## 2. Formato dos arquivos de entrada

Os arquivos de texto devem ter uma linha por associação.

### Formato aceito (associação e desassociação)

```
tenant,app_profile,epg,phys_domain
```

As colunas são:

| Coluna | Campo | Obrigatório? | Descrição |
|--------|-------|--------------|-----------|
| 1 | tenant | Sim | Nome do Tenant no ACI |
| 2 | app_profile | Sim | Nome do Application Profile |
| 3 | epg | Sim | Nome do Endpoint Group |
| 4 | phys_domain | Sim | Nome do Physical Domain |

Exemplo (`epgs_doms.txt`):

```
TENANT_EXEMPLO,AP_DADOS,EPG_CLIENTES,DOM_FISICO_01
TENANT_EXEMPLO,AP_DADOS,EPG_SERVIDORES,DOM_FISICO_01
OUTRO-TENANT,AP_GERENCIA,EPG_GER,DOM_GERENCIA
TERCEIRO,AP_DADOS,EPG_WEB,DOM_WEB
TERCEIRO,AP_DADOS,EPG_APP,DOM_APP
```

Exemplo (`delete-epgs-doms.txt`):

```
TENANT_EXEMPLO,AP_DADOS,EPG_CLIENTES,DOM_FISICO_01
OUTRO-TENANT,AP_GERENCIA,EPG_GER,DOM_GERENCIA
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
| `--tenant` (com `--ap`, `--epg`, `--dom`) | Usa **apenas** os dados informados na linha de comando e ignora o arquivo padrão |
| Somente `--arquivo` (ou nada) | Lê o arquivo padrão (`epgs_doms.txt` ou `delete-epgs-doms.txt`) |

---

### 3.1 Associar um EPG a um Physical Domain (modo simples)

```bash
python3 epg/create-epg-to-dom-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG_CLIENTES --dom DOM_FISICO_01 -v
```

Parâmetros:
- `--tenant` : nome do tenant (obrigatório)
- `--ap` : nome do Application Profile (obrigatório)
- `--epg` : nome do EPG (obrigatório)
- `--dom` : nome do Physical Domain (obrigatório)
- `-v` : modo verbose (mostra detalhes passo a passo)
- `--log-file nome.log` : salva o relatório também em arquivo

---

### 3.2 Associar vários EPGs a Physical Domains via arquivo (recomendado para produção)

```bash
python3 epg/create-epgs-to-doms-prod.py --arquivo epg/epgs_doms.txt -v --log-file associar.log
```

Cada linha do arquivo define seu próprio tenant, AP, EPG e Physical Domain.

---

### 3.3 Associar vários EPGs via linha de comando (modo simples)

Quando todos os EPGs são do mesmo tenant e mesmo AP:

```bash
python3 epg/create-epgs-to-doms-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG1 --epg EPG2 --epg EPG3 --dom DOM1 --dom DOM2 --dom DOM3 -v
```

**Regras:**
- A quantidade de `--epg` deve ser igual à quantidade de `--dom`
- Eles são associados em ordem: EPG1 com DOM1, EPG2 com DOM2, etc.

---

### 3.4 Desassociar um EPG de um Physical Domain (modo simples)

```bash
python3 epg/delete-epg-from-dom-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG_CLIENTES --dom DOM_FISICO_01 -v
```

---

### 3.5 Desassociar vários EPGs via arquivo (recomendado para produção)

```bash
python3 epg/delete-epg-from-dom-prod.py --arquivo epg/delete-epgs-doms.txt -v --log-file desassociar.log
```

---

### 3.6 Desassociar vários EPGs via linha de comando (modo simples)

```bash
python3 epg/delete-epg-from-dom-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG1 --epg EPG2 --dom DOM1 --dom DOM2 -v
```

---

## 4. Exemplos práticos

### Cenário A: Associar um EPG único a um Physical Domain

```bash
python3 epg/create-epg-to-dom-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG_CLIENTES --dom DOM_FISICO_01 -v
```

### Cenário B: Associar vários EPGs com Physical Domains diferentes

Arquivo `epgs_doms.txt`:

```
TENANT_PROD,AP_DADOS,EPG_WEB,DOM_WEB
TENANT_PROD,AP_DADOS,EPG_APP,DOM_APP
TENANT_PROD,AP_DADOS,EPG_DB,DOM_DB
TENANT_DEV,AP_GERENCIA,EPG_DEV,DOM_DEV
```

Execução:

```bash
python3 epg/create-epgs-to-doms-prod.py --arquivo epg/epgs_doms.txt -v --log-file associar_prod.log
```

### Cenário C: Desassociar um EPG de um Physical Domain

```bash
python3 epg/delete-epg-from-dom-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG_CLIENTES --dom DOM_FISICO_01 -v
```

### Cenário D: Desassociar vários EPGs de Physical Domains

Arquivo `delete-epgs-doms.txt`:

```
TENANT_DEV,AP_GERENCIA,EPG_DEV,DOM_DEV
TENANT_PROD,AP_DADOS,EPG_WEB,DOM_WEB
```

Execução:

```bash
python3 epg/delete-epg-from-dom-prod.py --arquivo epg/delete-epgs-doms.txt -v --log-file desassociar_dev.log
```

---

## 5. Interpretando o relatório

Exemplo de saída na tela (associação):

```
======================================================================
REPORT - ASSOCIAÇÃO DE EPGs A PHYSICAL DOMAINS
======================================================================
APIC   : https://172.30.104.5
Usuário: 80689851
Qtd associações: 3
----------------------------------------------------------------------
🔎 Verificando Tenant 'TENANT_EXEMPLO' -> encontrado
🔎 Verificando AP 'TENANT_EXEMPLO/AP_DADOS' -> encontrado
🔎 Verificando Physical Domain 'DOM_FISICO_01' -> encontrado
🔎 Verificando EPG 'TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES' -> encontrado
🔎 Verificando associação EPG/Dom 'TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES <-> DOM_FISICO_01' -> não encontrado
🔗 Associando EPG 'TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES' ao Physical Domain 'DOM_FISICO_01'... Status: 200
✅ EPG 'TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES' associado ao Physical Domain 'DOM_FISICO_01' com sucesso.
🔎 Verificando associação EPG/Dom 'TENANT_EXEMPLO/AP_DADOS/EPG_SERVIDORES <-> DOM_FISICO_01' -> encontrado
⚠️  EPG 'TENANT_EXEMPLO/AP_DADOS/EPG_SERVIDORES' já está associado ao Physical Domain 'DOM_FISICO_01'. Pulando.
----------------------------------------------------------------------
RESUMO
----------------------------------------------------------------------
Tenants processados: 1
  📦 TENANT_EXEMPLO
APs processados: 1
  📁 TENANT_EXEMPLO/AP_DADOS
Physical Domains processados: 1
  🌐 DOM_FISICO_01
Associações criadas : 1
  ✅ TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES <-> DOM_FISICO_01
Associações puladas : 1
  ⚠️  TENANT_EXEMPLO/AP_DADOS/EPG_SERVIDORES <-> DOM_FISICO_01
Falhas              : 0
======================================================================
```

Exemplo de saída na tela (desassociação):

```
======================================================================
REPORT - DESASSOCIAÇÃO DE EPGs DE PHYSICAL DOMAINS
======================================================================
APIC   : https://172.30.104.5
Usuário: 80689851
Qtd itens: 2
----------------------------------------------------------------------
🔎 Verificando associação EPG/Dom 'TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES <-> DOM_FISICO_01' -> encontrado
🔗 Desassociando EPG 'TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES' do Physical Domain 'DOM_FISICO_01'... Status: 200
✅ Associação EPG 'TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES' <-> Dom 'DOM_FISICO_01' removida com sucesso.
🔎 Verificando associação EPG/Dom 'TENANT_EXEMPLO/AP_DADOS/EPG_SERVIDORES <-> DOM_FISICO_01' -> não encontrado
⚠️  Associação 'TENANT_EXEMPLO/AP_DADOS/EPG_SERVIDORES' <-> 'DOM_FISICO_01' não existe. Pulando.
----------------------------------------------------------------------
RESUMO
----------------------------------------------------------------------
Tenants processados: 1
  📦 TENANT_EXEMPLO
APs processados: 1
  📁 TENANT_EXEMPLO/AP_DADOS
Physical Domains processados: 1
  🌐 DOM_FISICO_01
Associações removidas : 1
  🗑️  TENANT_EXEMPLO/AP_DADOS/EPG_CLIENTES <-> DOM_FISICO_01
Associações puladas   : 1
  ⚠️  TENANT_EXEMPLO/AP_DADOS/EPG_SERVIDORES <-> DOM_FISICO_01
Falhas                : 0
======================================================================
```

Significado dos status:
- ✅ **Associado/Removido com sucesso:** operação concluída no APIC.
- ⚠️ **Pulado:** a associação já existia (associação) ou não existia (desassociação). Nenhuma ação foi tomada.
- ❌ **Falha:** erro de rede, rejeição pelo APIC, ou algum componente não existe (Tenant, AP, EPG ou Physical Domain). Verifique o log e as credenciais.

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
├── create-epg-to-dom-prod.py        # Script novo: associar 1 EPG a 1 Dom
├── create-epgs-to-doms-prod.py      # Script novo: associar vários EPGs a vários Doms
├── delete-epg-from-dom-prod.py      # Script novo: desassociar EPGs de Doms
├── create-epg-to-bd-prod.py         # Script original: criar EPG + BD
├── create-epgs-to-bds-prod.py       # Script original: criar vários EPGs + BDs
├── delete-epg-bd-prod.py            # Script original: deletar EPG e/ou BD
├── create-epg-to-bd-prod.py         # Script original (referência)
├── create-epgs-to-bds-prod.py       # Script original (referência)
├── config.ini                       # Configurações padrão do APIC (opcional)
├── epgs.txt                         # Exemplo de entrada para criação EPG+BD
├── epgs_doms.txt                    # Exemplo de entrada para associação EPG+Dom
├── delete-epg-bd.txt                # Exemplo de entrada para exclusão EPG+BD
├── delete-epgs-doms.txt             # Exemplo de entrada para desassociação EPG+Dom
├── MANUAL_EPG.md                    # Manual de criação EPG+BD
├── MANUAL_DELETE_EPG_BD.md          # Manual de exclusão EPG+BD
└── MANUAL_CREATE_EPG_DOM.md         # Este manual (associação EPG+Dom)
```

---

## 8. Checklist antes de rodar em produção

- [ ] Verifique se o arquivo de entrada (`epgs_doms.txt` ou `delete-epgs-doms.txt`) está com o formato correto (`tenant,app_profile,epg,phys_domain`).
- [ ] Confirme se o Tenant, Application Profile, EPG e Physical Domain já existem no ACI. O script não cria esses componentes, apenas valida se existem.
- [ ] Rode primeiro com `-v` para ver o que será feito sem surpresas.
- [ ] Use `--log-file` para guardar evidência da execução.
- [ ] Nunca compartilhe arquivos de log que contenham senhas (os logs destes scripts não gravam senhas).

---

## 9. Dúvidas comuns

**Q: Posso associar EPGs de tenants diferentes na mesma execução?**
A: Sim. Use o arquivo de entrada (`--arquivo`) com linhas diferentes para cada tenant.

**Q: Posso associar um EPG a vários Physical Domains?**
A: Sim, basta criar múltiplas linhas no arquivo com o mesmo EPG e domínios diferentes, ou usar `--epg` e `--dom` repetidos na linha de comando.

**Q: O script cria o Tenant, AP, EPG ou Physical Domain se não existirem?**
A: Não. Ele apenas valida se existem. Se algum não existir, a associação não é feita e o script informa o erro.

**Q: A desassociação remove o EPG ou o Physical Domain?**
A: Não. A desassociação apenas remove o vínculo (`fvRsDomAtt`) entre o EPG e o Physical Domain. O EPG e o Physical Domain continuam existindo no ACI.

**Q: Esqueci a senha. O que faço?**
A: O script não armazena senha. Peça ao responsável de segurança ou use seu usuário pessoal do APIC.

---

Fim do manual.
