# MANUAL - Associação de Porta Estática VPC (vPC / Protected Ports) a EPG no Cisco ACI

Este manual explica como usar os scripts de associação e desassociação de portas estáticas VPC (Static Ports / `fvRsPathAtt` via *protected paths*) a Endpoint Groups (EPGs) no Cisco ACI via API REST do APIC.

Público-alvo: analistas juniores de rede/infraestrutura.

---

## 1. Visão geral

A pasta `epg/` contém os seguintes scripts para Static Ports **VPC**:

| Script | Função | Arquivo de entrada padrão |
|--------|--------|---------------------------|
| `create-static-port-vpc-to-epg-prod.py` | Associa 1 porta estática VPC a 1 EPG | — (modo linha de comando) |
| `create-statics-ports-vpc-to-epgs-prod.py` | Associa várias portas estáticas VPC a EPGs | `statics_ports_vpc.txt` (via `--arquivo`) |
| `delete-static-port-vpc-from-epg-prod.py` | Desassocia 1 porta estática VPC de 1 EPG | — (modo linha de comando) |
| `delete-statics-ports-vpc-from-epgs-prod.py` | Desassocia várias portas estáticas VPC de EPGs | `delete-statics-ports-vpc.txt` (via `--arquivo`) |

O que os scripts de associação fazem:
1. Pedem **usuário e senha na tela** (a senha não aparece ao digitar).
2. Autenticam no APIC.
3. Associam a porta estática VPC (`fvRsPathAtt`) ao EPG informado.
4. Mostram um **relatório na tela** (associadas, falhas) e opcionalmente salvam em arquivo de log (`--log-file`).

O que os scripts de desassociação fazem:
1. Pedem **usuário e senha na tela**.
2. Autenticam no APIC.
3. Removem a associação da porta estática VPC do EPG (`rspathAtt`).
4. Mostram um **relatório na tela** (removidas, falhas) e opcionalmente salvam em arquivo de log (`--log-file`).

**Importante:** Os scripts apenas associam/desassociam portas. Eles **não criam** Tenants, Application Profiles, EPGs, **nem o VPC (Interface Policy Group)**. O EPG, as interfaces e o VPC devem já existir no ACI.

Nunca armazene senhas no código. Use o `config.ini` apenas para a URL do APIC (opcional).

---

## 2. Diferença entre Static Port normal e Static Port VPC

A API usada é a mesma (`fvRsPathAtt`); o que muda é o **TDN** informado:

| Tipo | Formato do TDN | Exemplo |
|------|----------------|---------|
| Static Port (porta física) | `topology/pod-X/paths-ID/pathep-[interface]` | `topology/pod-1/paths-101/pathep-[eth1/24]` |
| Static Port **VPC** | `topology/pod-X/protpaths-IDA-IDB/pathep-[policy-group]` | `topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]` |

Onde, no caso VPC:
- `protpaths-IDA-IDB`: identificadores das **duas leafs** que formam o VPC (ex.: `101-102`).
- `pathep-[...]`: nome do **VPC Interface Policy Group** (ex.: `VPC_DADOS`) — **não** é o nome da interface física.

> Dica: para descobrir o TDN correto, no APIC vá em **Tenants > (seu tenant) > Application Profiles > (seu AP) > EPG > Static Ports** e copie o TDN existente, ou localize o VPC em **Fabric > Access Policies > Interfaces > Leaf Interfaces > Policy Groups > VPC Interface**.

---

## 3. Formato dos arquivos de entrada

Os arquivos de texto devem ter uma linha por porta estática VPC.

### Formato aceito (associação)

```
tenant,app_profile,epg,tdn,encap
```

| Coluna | Campo | Obrigatório? | Descrição |
|--------|-------|--------------|-----------|
| 1 | tenant | Sim | Nome do Tenant no ACI |
| 2 | app_profile | Sim | Nome do Application Profile |
| 3 | epg | Sim | Nome do Endpoint Group |
| 4 | tdn | Sim | Caminho da porta VPC (ex.: `topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]`) |
| 5 | encap | Sim | VLAN ou any (ex.: `vlan-100`, `vlan-200`, `any`) |

Exemplo (`statics_ports_vpc.txt`):

```
HUAWEI,AP_DADOS,EPG_CLIENTES,topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS],vlan-100
HUAWEI,AP_DADOS,EPG_SERVIDORES,topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS],vlan-200
OUTRO-TENANT,AP_GERENCIA,EPG_GER,topology/pod-1/protpaths-101-102/pathep-[VPC_GER],any
TERCEIRO,AP_DADOS,EPG_WEB,topology/pod-2/protpaths-105-106/pathep-[VPC_WEB],vlan-300
```

Regras:
- Linhas iniciando com `#` são ignoradas (comentários).
- Linhas em branco são ignoradas.
- Todas as 5 colunas são obrigatórias.
- O TDN deve seguir o padrão VPC do ACI (`protpaths-...`).
- O encap pode ser `vlan-N` ou `any`.

### Formato aceito (desassociação)

```
tenant,app_profile,epg,tdn
```

Exemplo (`delete-statics-ports-vpc.txt`):

```
HUAWEI,AP_DADOS,EPG_CLIENTES,topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]
HUAWEI,AP_DADOS,EPG_SERVIDORES,topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]
OUTRO-TENANT,AP_GERENCIA,EPG_GER,topology/pod-1/protpaths-101-102/pathep-[VPC_GER]
```

Regras:
- A coluna `encap` **não** é informada na desassociação (apenas `tenant,app_profile,epg,tdn`).
- Todas as 4 colunas são obrigatórias.

---

## 4. Como executar os scripts

### Pré-requisitos

- Python 3 instalado
- Biblioteca `requests` instalada (`pip install requests`)
- Acesso de rede ao APIC (exemplo: `https://172.30.104.5`)

### Prioridade: linha de comando vs arquivo

| Se você passar... | O script faz... |
|-------------------|-----------------|
| `--tenant` (com `--ap`, `--epg`, `--tdn`, `--encap`) | Usa **apenas** os dados informados na linha de comando e ignora o arquivo padrão |
| Somente `--arquivo` (ou nada) | Lê o arquivo padrão (`statics_ports_vpc.txt` ou `delete-statics-ports-vpc.txt`) |

---

### 4.1 Associar uma porta estática VPC (modo simples)

```bash
python3 epg/create-static-port-vpc-to-epg-prod.py --tenant HUAWEI --ap AP_DADOS --epg EPG_CLIENTES --tdn "topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]" --encap vlan-100 -v
```

Parâmetros:
- `--tenant` : nome do tenant (obrigatório)
- `--ap` : nome do Application Profile (obrigatório)
- `--epg` : nome do EPG (obrigatório)
- `--tdn` : caminho da porta VPC no ACI (obrigatório)
- `--encap` : VLAN ou any (obrigatório)
- `-v` : modo verbose
- `--log-file nome.log` : salva o relatório também em arquivo

---

### 4.2 Associar várias portas VPC via arquivo (recomendado para produção)

```bash
python3 epg/create-statics-ports-vpc-to-epgs-prod.py --arquivo epg/statics_ports_vpc.txt -v --log-file associar_vpc.log
```

Ou sem informar `--arquivo` (usa o padrão `statics_ports_vpc.txt`):

```bash
python3 epg/create-statics-ports-vpc-to-epgs-prod.py -v --log-file associar_vpc.log
```

---

### 4.3 Associar várias portas VPC via linha de comando (modo simples)

Quando todas as portas são do mesmo tenant e mesmo AP:

```bash
python3 epg/create-statics-ports-vpc-to-epgs-prod.py --tenant HUAWEI --ap AP_DADOS --epg EPG1 --epg EPG2 --tdn "topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]" --tdn "topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]" --encap vlan-100 --encap vlan-200 -v
```

**Regras:**
- A quantidade de `--epg`, `--tdn` e `--encap` deve ser igual.
- Eles são associados em ordem: EPG1 com TDN1/ENCAP1, EPG2 com TDN2/ENCAP2, etc.

---

### 4.4 Desassociar uma porta estática VPC (modo simples)

```bash
python3 epg/delete-static-port-vpc-from-epg-prod.py --tenant HUAWEI --ap AP_DADOS --epg EPG_CLIENTES --tdn "topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]" -v
```

---

### 4.5 Desassociar várias portas VPC via arquivo

```bash
python3 epg/delete-statics-ports-vpc-from-epgs-prod.py --arquivo epg/delete-statics-ports-vpc.txt -v --log-file desassociar_vpc.log
```

Ou sem informar `--arquivo` (usa o padrão `delete-statics-ports-vpc.txt`):

```bash
python3 epg/delete-statics-ports-vpc-from-epgs-prod.py -v --log-file desassociar_vpc.log
```

---

### 4.6 Desassociar várias portas VPC via linha de comando (modo simples)

```bash
python3 epg/delete-statics-ports-vpc-from-epgs-prod.py --tenant HUAWEI --ap AP_DADOS --epg EPG1 --epg EPG2 --tdn "topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]" --tdn "topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]" -v
```

---

## 5. Exemplos práticos

### Cenário A: Associar uma porta VPC única

```bash
python3 epg/create-static-port-vpc-to-epg-prod.py --tenant HUAWEI --ap AP_DADOS --epg EPG_CLIENTES --tdn "topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]" --encap vlan-100 -v
```

### Cenário B: Associar várias portas VPC com VLANs diferentes

Arquivo `statics_ports_vpc.txt`:

```
TENANT_PROD,AP_DADOS,EPG_WEB,topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS],vlan-100
TENANT_PROD,AP_DADOS,EPG_APP,topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS],vlan-200
TENANT_PROD,AP_DADOS,EPG_DB,topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS],vlan-300
TENANT_DEV,AP_GERENCIA,EPG_DEV,topology/pod-2/protpaths-105-106/pathep-[VPC_GER],any
```

Execução:

```bash
python3 epg/create-statics-ports-vpc-to-epgs-prod.py --arquivo epg/statics_ports_vpc.txt -v --log-file associar_vpc.prod.log
```

### Cenário C: Desassociar portas VPC

```bash
python3 epg/delete-statics-ports-vpc-from-epgs-prod.py --arquivo epg/delete-statics-ports-vpc.txt -v --log-file desassociar_vpc.log
```

---

## 6. Interpretando o relatório

Exemplo de saída na tela (associação):

```
======================================================================
REPORT - ASSOCIAÇÃO DE PORTAS ESTÁTICAS VPC A EPGs
======================================================================
APIC   : https://172.30.104.5
Usuário: 80689851
Qtd portas: 2
----------------------------------------------------------------------
🔗 Associando porta VPC 'topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]' (encap 'vlan-100') ao EPG 'HUAWEI/AP_DADOS/EPG_CLIENTES'... Status: 200
✅ Porta VPC 'topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS]' associada ao EPG 'HUAWEI/AP_DADOS/EPG_CLIENTES' com sucesso.
----------------------------------------------------------------------
RESUMO
----------------------------------------------------------------------
Portas VPC associadas : 2
  ✅ HUAWEI/AP_DADOS/EPG_CLIENTES <- topology/pod-1/protpaths-101-102/pathep-[VPC_DADOS] (vlan-100)
Falhas            : 0
======================================================================
```

Significado dos status:
- ✅ **Associado/Removido com sucesso:** operação concluída no APIC.
- ❌ **Falha:** erro de rede ou rejeição pelo APIC. Verifique o TDN, encap e credenciais.

---

## 7. Credenciais e segurança

- Os scripts **não contêm senha hardcoded**.
- Ao executar, você será perguntado:
  ```
  Usuário APIC: 80689851
  Senha APIC: <digite aqui, não aparece na tela>
  ```
- Você pode passar `--user` e `--pass` na linha de comando para automatizar, mas o recomendado para uso manual é digitar na tela.
- O arquivo `config.ini` pode conter a URL do APIC. Usuário e senha nele são opcionais e não recomendados para produção.

---

## 8. Arquivos VPC na pasta `epg/`

```
epg/
├── create-static-port-vpc-to-epg-prod.py        # Associar 1 porta estática VPC
├── create-statics-ports-vpc-to-epgs-prod.py     # Associar várias portas VPC
├── delete-static-port-vpc-from-epg-prod.py      # Desassociar 1 porta estática VPC
├── delete-statics-ports-vpc-from-epgs-prod.py   # Desassociar várias portas VPC
├── statics_ports_vpc.txt                        # Exemplo de entrada para associação VPC
├── delete-statics-ports-vpc.txt                 # Exemplo de entrada para desassociação VPC
└── MANUAL_STATIC_PORTS_VPC.md                   # Este manual
```

---

## 9. Checklist antes de rodar em produção

- [ ] Verifique se o arquivo de entrada (`statics_ports_vpc.txt` ou `delete-statics-ports-vpc.txt`) está com o formato correto.
- [ ] Confirme se o TDN da VPC está correto no ACI (formato `topology/pod-X/protpaths-IDA-IDB/pathep-[policy-group]`).
- [ ] Confirme se o nome do VPC Interface Policy Group está correto (não é o nome da interface física).
- [ ] Confirme se o encap (VLAN) está correto.
- [ ] Rode primeiro com `-v` para ver o que será feito sem surpresas.
- [ ] Use `--log-file` para guardar evidência da execução.
- [ ] Nunca compartilhe arquivos de log que contenham senhas (os logs destes scripts não gravam senhas).

---

## 10. Dúvidas comuns

**Q: Qual a diferença entre rodar o script normal e o script VPC?**
A: O formato do TDN. Em VPC usa-se `protpaths-IDA-IDB/pathep-[policy-group]`; em porta física usa-se `paths-ID/pathep-[interface]`. A chamada à API é a mesma.

**Q: Posso associar portas de tenants diferentes na mesma execução?**
A: Sim. Use o arquivo de entrada (`--arquivo`) com linhas diferentes para cada tenant.

**Q: Posso associar várias portas ao mesmo EPG?**
A: Sim, basta criar múltiplas linhas no arquivo com o mesmo EPG e TDNs/encaps diferentes.

**Q: O script cria o VPC / Interface Policy Group se não existir?**
A: Não. Ele apenas associa a porta VPC ao EPG. O VPC e as interfaces devem já existir no ACI.

**Q: A desassociação remove o VPC?**
A: Não. A desassociação apenas remove o vínculo (`fvRsPathAtt`) entre o EPG e a porta VPC. O VPC continua existindo no ACI.

**Q: Esqueci a senha. O que faço?**
A: O script não armazena senha. Peça ao responsável de segurança ou use seu usuário pessoal do APIC.

---

Fim do manual.
