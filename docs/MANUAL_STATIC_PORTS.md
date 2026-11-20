# MANUAL - Associação de Porta Estática (Static Port) a EPG no Cisco ACI

Este manual explica como usar os scripts de associação e desassociação de portas estáticas (Static Ports / fvRsPathAtt) a Endpoint Groups (EPGs) no Cisco ACI via API REST do APIC.

Público-alvo: analistas juniores de rede/infraestrutura.

---

## 1. Visão geral

A pasta `epg/` contém os seguintes scripts para Static Ports:

| Script | Função | Arquivo de entrada padrão |
|--------|--------|---------------------------|
| `create-static-port-to-epg-prod.py` | Associa 1 porta estática a 1 EPG | — (modo linha de comando) |
| `create-statics-ports-to-epgs-prod.py` | Associa várias portas estáticas a EPGs | `statics_ports.txt` (via `--arquivo`) |
| `delete-static-port-from-epg-prod.py` | Desassocia 1 porta estática de 1 EPG | — (modo linha de comando) |
| `delete-statics-ports-from-epgs-prod.py` | Desassocia várias portas estáticas de EPGs | `delete-statics-ports.txt` (via `--arquivo`) |
| `config.ini` | Configurações padrão do APIC (URL, usuário, senha) | — |

O que os scripts de associação fazem:
1. Pedem **usuário e senha na tela** (a senha não aparece ao digitar).
2. Autenticam no APIC.
3. Associam a porta estática (`fvRsPathAtt`) ao EPG informado.
4. Mostram um **relatório na tela** (associadas, falhas) e opcionalmente salvam em arquivo de log (`--log-file`).

O que os scripts de desassociação fazem:
1. Pedem **usuário e senha na tela**.
2. Autenticam no APIC.
3. Removem a associação da porta estática do EPG (`rspathAtt`).
4. Mostram um **relatório na tela** (removidas, falhas) e opcionalmente salvam em arquivo de log (`--log-file`).

**Importante:** Os scripts apenas associam/desassociam portas. Eles **não criam** Tenants, Application Profiles, EPGs, nem configuram VLANs. O EPG e a porta devem já existir no ACI.

Nunca armazene senhas no código. Use o `config.ini` apenas para a URL do APIC (opcional).

---

## 2. Formato dos arquivos de entrada

Os arquivos de texto devem ter uma linha por porta estática.

### Formato aceito (associação)

```
tenant,app_profile,epg,tdn,encap
```

As colunas são:

| Coluna | Campo | Obrigatório? | Descrição |
|--------|-------|--------------|-----------|
| 1 | tenant | Sim | Nome do Tenant no ACI |
| 2 | app_profile | Sim | Nome do Application Profile |
| 3 | epg | Sim | Nome do Endpoint Group |
| 4 | tdn | Sim | Caminho físico da porta (ex: `topology/pod-1/paths-101/pathep-[eth1/24]`) |
| 5 | encap | Sim | VLAN ou any (ex: `vlan-100`, `vlan-200`, `any`) |

Exemplo (`statics_ports.txt`):

```
HUAWEI,AP_DADOS,EPG_CLIENTES,topology/pod-1/paths-101/pathep-[eth1/24],vlan-100
HUAWEI,AP_DADOS,EPG_SERVIDORES,topology/pod-1/paths-101/pathep-[eth1/25],vlan-200
OUTRO-TENANT,AP_GERENCIA,EPG_GER,topology/pod-1/paths-102/pathep-[eth1/30],any
TERCEIRO,AP_DADOS,EPG_WEB,topology/pod-2/paths-101/pathep-[eth1/10],vlan-300
```

Regras:
- Linhas iniciando com `#` são ignoradas (comentários).
- Linhas em branco são ignoradas.
- Todas as 5 colunas são obrigatórias.
- O TDN deve seguir o padrão do ACI para portas físicas.
- O encap pode ser `vlan-N` ou `any`.

### Formato aceito (desassociação)

```
tenant,app_profile,epg,tdn
```

Exemplo (`delete-statics-ports.txt`):

```
HUAWEI,AP_DADOS,EPG_CLIENTES,topology/pod-1/paths-101/pathep-[eth1/24]
HUAWEI,AP_DADOS,EPG_SERVIDORES,topology/pod-1/paths-101/pathep-[eth1/25]
OUTRO-TENANT,AP_GERENCIA,EPG_GER,topology/pod-1/paths-102/pathep-[eth1/30]
```

Regras:
- A coluna `encap` **não** é informada na desassociação (apenas `tenant,app_profile,epg,tdn`).
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
| `--tenant` (com `--ap`, `--epg`, `--tdn`, `--encap`) | Usa **apenas** os dados informados na linha de comando e ignora o arquivo padrão |
| Somente `--arquivo` (ou nada) | Lê o arquivo padrão (`statics_ports.txt` ou `delete-statics-ports.txt`) |

---

### 3.1 Associar uma porta estática (modo simples)

```bash
python3 epg/create-static-port-to-epg-prod.py --tenant HUAWEI --ap AP_DADOS --epg EPG_CLIENTES --tdn "topology/pod-1/paths-101/pathep-[eth1/24]" --encap vlan-100 -v
```

Parâmetros:
- `--tenant` : nome do tenant (obrigatório)
- `--ap` : nome do Application Profile (obrigatório)
- `--epg` : nome do EPG (obrigatório)
- `--tdn` : caminho da porta no ACI (obrigatório)
- `--encap` : VLAN ou any (obrigatório)
- `-v` : modo verbose
- `--log-file nome.log` : salva o relatório também em arquivo

---

### 3.2 Associar várias portas via arquivo (recomendado para produção)

```bash
python3 epg/create-statics-ports-to-epgs-prod.py --arquivo epg/statics_ports.txt -v --log-file associar.log
```

Ou sem informar `--arquivo` (usa o padrão):

```bash
python3 epg/create-statics-ports-to-epgs-prod.py -v --log-file associar.log
```

---

### 3.3 Associar várias portas via linha de comando (modo simples)

Quando todas as portas são do mesmo tenant e mesmo AP:

```bash
python3 epg/create-statics-ports-to-epgs-prod.py --tenant HUAWEI --ap AP_DADOS --epg EPG1 --epg EPG2 --tdn "topology/pod-1/paths-101/pathep-[eth1/24]" --tdn "topology/pod-1/paths-101/pathep-[eth1/25]" --encap vlan-100 --encap vlan-200 -v
```

**Regras:**
- A quantidade de `--epg`, `--tdn` e `--encap` deve ser igual.
- Eles são associados em ordem: EPG1 com TDN1/ENCAP1, EPG2 com TDN2/ENCAP2, etc.

---

### 3.4 Desassociar uma porta estática (modo simples)

```bash
python3 epg/delete-static-port-from-epg-prod.py --tenant HUAWEI --ap AP_DADOS --epg EPG_CLIENTES --tdn "topology/pod-1/paths-101/pathep-[eth1/24]" -v
```

---

### 3.5 Desassociar várias portas via arquivo (recomendado para produção)

```bash
python3 epg/delete-statics-ports-from-epgs-prod.py --arquivo epg/delete-statics-ports.txt -v --log-file desassociar.log
```

Ou sem informar `--arquivo` (usa o padrão):

```bash
python3 epg/delete-statics-ports-from-epgs-prod.py -v --log-file desassociar.log
```

---

### 3.6 Desassociar várias portas via linha de comando (modo simples)

```bash
python3 epg/delete-statics-ports-from-epgs-prod.py --tenant HUAWEI --ap AP_DADOS --epg EPG1 --epg EPG2 --tdn "topology/pod-1/paths-101/pathep-[eth1/24]" --tdn "topology/pod-1/paths-101/pathep-[eth1/25]" -v
```

---

## 4. Exemplos práticos

### Cenário A: Associar uma porta estática única

```bash
python3 epg/create-static-port-to-epg-prod.py --tenant HUAWEI --ap AP_DADOS --epg EPG_CLIENTES --tdn "topology/pod-1/paths-101/pathep-[eth1/24]" --encap vlan-100 -v
```

### Cenário B: Associar várias portas com VLANs diferentes

Arquivo `statics_ports.txt`:

```
TENANT_PROD,AP_DADOS,EPG_WEB,topology/pod-1/paths-101/pathep-[eth1/10],vlan-100
TENANT_PROD,AP_DADOS,EPG_APP,topology/pod-1/paths-101/pathep-[eth1/11],vlan-200
TENANT_PROD,AP_DADOS,EPG_DB,topology/pod-1/paths-101/pathep-[eth1/12],vlan-300
TENANT_DEV,AP_GERENCIA,EPG_DEV,topology/pod-2/paths-102/pathep-[eth1/20],any
```

Execução:

```bash
python3 epg/create-statics-ports-to-epgs-prod.py --arquivo epg/statics_ports.txt -v --log-file associar_prod.log
```

### Cenário C: Desassociar portas estáticas

Arquivo `delete-statics-ports.txt`:

```
TENANT_DEV,AP_GERENCIA,EPG_DEV,topology/pod-2/paths-102/pathep-[eth1/20]
TENANT_PROD,AP_DADOS,EPG_WEB,topology/pod-1/paths-101/pathep-[eth1/10]
```

Execução:

```bash
python3 epg/delete-statics-ports-from-epgs-prod.py --arquivo epg/delete-statics-ports.txt -v --log-file desassociar_dev.log
```

---

## 5. Interpretando o relatório

Exemplo de saída na tela (associação):

```
======================================================================
REPORT - ASSOCIAÇÃO DE PORTAS ESTÁTICAS A EPGs
======================================================================
APIC   : https://172.30.104.5
Usuário: 80689851
Qtd portas: 3
----------------------------------------------------------------------
🔗 Associando porta 'topology/pod-1/paths-101/pathep-[eth1/24]' (encap 'vlan-100') ao EPG 'HUAWEI/AP_DADOS/EPG_CLIENTES'... Status: 200
✅ Porta 'topology/pod-1/paths-101/pathep-[eth1/24]' associada ao EPG 'HUAWEI/AP_DADOS/EPG_CLIENTES' com sucesso.
🔗 Associando porta 'topology/pod-1/paths-101/pathep-[eth1/25]' (encap 'vlan-200') ao EPG 'HUAWEI/AP_DADOS/EPG_SERVIDORES'... Status: 200
✅ Porta 'topology/pod-1/paths-101/pathep-[eth1/25]' associada ao EPG 'HUAWEI/AP_DADOS/EPG_SERVIDORES' com sucesso.
----------------------------------------------------------------------
RESUMO
----------------------------------------------------------------------
Portas associadas : 2
  ✅ HUAWEI/AP_DADOS/EPG_CLIENTES <- topology/pod-1/paths-101/pathep-[eth1/24] (vlan-100)
  ✅ HUAWEI/AP_DADOS/EPG_SERVIDORES <- topology/pod-1/paths-101/pathep-[eth1/25] (vlan-200)
Falhas            : 0
======================================================================
```

Exemplo de saída na tela (desassociação):

```
======================================================================
REPORT - DESASSOCIAÇÃO DE PORTAS ESTÁTICAS DE EPGs
======================================================================
APIC   : https://172.30.104.5
Usuário: 80689851
Qtd itens: 2
----------------------------------------------------------------------
🔗 Desassociando porta 'topology/pod-1/paths-101/pathep-[eth1/24]' do EPG 'HUAWEI/AP_DADOS/EPG_CLIENTES'... Status: 200
✅ Porta 'topology/pod-1/paths-101/pathep-[eth1/24]' desassociada do EPG 'HUAWEI/AP_DADOS/EPG_CLIENTES' com sucesso.
----------------------------------------------------------------------
RESUMO
----------------------------------------------------------------------
Portas desassociadas : 1
  🗑️  HUAWEI/AP_DADOS/EPG_CLIENTES <- topology/pod-1/paths-101/pathep-[eth1/24]
Falhas               : 0
======================================================================
```

Significado dos status:
- ✅ **Associado/Removido com sucesso:** operação concluída no APIC.
- ❌ **Falha:** erro de rede ou rejeição pelo APIC. Verifique o TDN, encap e credenciais.

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
├── create-static-port-to-epg-prod.py       # Script novo: associar 1 porta estática
├── create-statics-ports-to-epgs-prod.py    # Script novo: associar várias portas estáticas
├── delete-static-port-from-epg-prod.py     # Script novo: desassociar 1 porta estática
├── delete-statics-ports-from-epgs-prod.py  # Script novo: desassociar várias portas estáticas
├── create-epg-to-dom-prod.py               # Script: associar EPG a Physical Domain
├── create-epgs-to-doms-prod.py             # Script: associar vários EPGs a Domains
├── delete-epg-from-dom-prod.py             # Script: desassociar EPGs de Domains
├── create-epg-to-bd-prod.py                # Script original: criar EPG + BD
├── create-epgs-to-bds-prod.py              # Script original: criar vários EPGs + BDs
├── delete-epg-bd-prod.py                   # Script original: deletar EPG e/ou BD
├── config.ini                              # Configurações padrão do APIC (opcional)
├── statics_ports.txt                       # Exemplo de entrada para associação
├── delete-statics-ports.txt                # Exemplo de entrada para desassociação
├── epgs.txt                                # Exemplo de entrada para criação EPG+BD
├── epgs_doms.txt                           # Exemplo de entrada para associação EPG+Dom
├── delete-epg-bd.txt                       # Exemplo de entrada para exclusão EPG+BD
├── delete-epgs-doms.txt                    # Exemplo de entrada para desassociação EPG+Dom
├── MANUAL_EPG.md                           # Manual de criação EPG+BD
├── MANUAL_DELETE_EPG_BD.md                 # Manual de exclusão EPG+BD
├── MANUAL_CREATE_EPG_DOM.md                # Manual de associação EPG+Dom
└── MANUAL_STATIC_PORTS.md                  # Este manual
```

---

## 8. Checklist antes de rodar em produção

- [ ] Verifique se o arquivo de entrada (`statics_ports.txt` ou `delete-statics-ports.txt`) está com o formato correto (`tenant,app_profile,epg,tdn,encap`).
- [ ] Confirme se o TDN da porta está correto no ACI (formato `topology/pod-X/paths-Y/pathep-[ethA/B]`).
- [ ] Confirme se o encap (VLAN) está correto.
- [ ] Rode primeiro com `-v` para ver o que será feito sem surpresas.
- [ ] Use `--log-file` para guardar evidência da execução.
- [ ] Nunca compartilhe arquivos de log que contenham senhas (os logs destes scripts não gravam senhas).

---

## 9. Dúvidas comuns

**Q: Posso associar portas de tenants diferentes na mesma execução?**
A: Sim. Use o arquivo de entrada (`--arquivo`) com linhas diferentes para cada tenant.

**Q: Posso associar várias portas ao mesmo EPG?**
A: Sim, basta criar múltiplas linhas no arquivo com o mesmo EPG e TDNs/encaps diferentes.

**Q: O script cria o EPG ou o Physical Domain se não existirem?**
A: Não. Ele apenas associa a porta ao EPG. O EPG e a porta física devem já existir no ACI.

**Q: A desassociação remove a porta física?**
A: Não. A desassociação apenas remove o vínculo (`fvRsPathAtt`) entre o EPG e a porta. A porta física continua existindo no ACI.

**Q: Qual o formato correto do TDN?**
A: O padrão do ACI para portas físicas é: `topology/pod-{numero}/paths-{numero}/pathep-[{interface}]`. Exemplo: `topology/pod-1/paths-101/pathep-[eth1/24]`.

**Q: Esqueci a senha. O que faço?**
A: O script não armazena senha. Peça ao responsável de segurança ou use seu usuário pessoal do APIC.

---

Fim do manual.
