# MANUAL DE AUTOMAÇÃO DE L3OUT DOMAIN PROFILES (L3OUT-DOM) NO CISCO ACI

Este manual documenta os scripts Python desenvolvidos para automatizar o ciclo de vida de **L3out Domain Profiles** no Cisco ACI, permitindo a criação simples, criação com associação simultânea a **VLAN Pool** e **AAEP**, além da exclusão de domínios, suportando execução via linha de comando (CLI) ou arquivos de configuração (CSV/TXT).

---

## 1. Estrutura de Scripts na Pasta `L3out-dom`

- **`create-l3out-dom-prod.py`**: Criação simples de um L3out Domain Profile.
- **`create-l3out-dom-with-vlanpool-prod.py`**: Criação de um L3out Domain Profile com associação a um VLAN Pool e vinculação a um AAEP existente.
- **`delete-l3out-dom-prod.py`**: Exclusão de um L3out Domain Profile.

---

## 2. Como Utilizar

Todos os scripts acebem duas formas de entrada: **Parâmetros via CLI** ou **Arquivo CSV**.

### A. Criação Simples de L3out Domain Profile
#### Via CLI:
```bash
python3 L3out-dom/create-l3out-dom-prod.py --dom-name JASONX1-L3OUT-DOM
```
#### Via CSV (`L3out-dom/l3out_input.txt`):
```csv
DOM_NAME
JASONX1-L3OUT-DOM
```
```bash
python3 L3out-dom/create-l3out-dom-prod.py --arquivo L3out-dom/l3out_input.txt
```

---

### B. Criação com Associação (VLAN Pool + AAEP)
Cria o domínio, amarra ao VLAN Pool e associa ao AAEP de forma idempotente (`created,modified`).

#### Via CLI:
```bash
python3 L3out-dom/create-l3out-dom-with-vlanpool-prod.py --dom-name JASONX2-L3OUT-DOM --pool-name JASONX1-POOL --aaep-name JASONX1-AAEP
```
#### Via CSV (`L3out-dom/l3out_vlanpool_aaep_input.txt`):
```csv
DOM_NAME,POOL_NAME,AAEP_NAME
JASONX2-L3OUT-DOM,JASONX1-POOL,JASONX1-AAEP
```
```bash
python3 L3out-dom/create-l3out-dom-with-vlanpool-prod.py --arquivo L3out-dom/l3out_vlanpool_aaep_input.txt
```

---

### C. Deleção de L3out Domain Profile
*(Nota: Ao deletar o L3out Domain Profile pai no ACI, as amarrações filhas são removidas automaticamente).*

#### Via CLI:
```bash
python3 L3out-dom/delete-l3out-dom-prod.py --dom-name JASONX2-L3OUT-DOM
```
#### Via CSV (`L3out-dom/l3out_delete.txt`):
```csv
DOM_NAME
JASONX2-L3OUT-DOM
```
```bash
python3 L3out-dom/delete-l3out-dom-prod.py --arquivo L3out-dom/l3out_delete.txt
```

---

## 3. Autenticação
- Caso os argumentos `--user` ou `--pass` não sejam informados, o script solicitará interativamente as credenciais de acesso ao APIC.
- Comunicação via HTTPS REST API utilizando tokens de sessão (Cookies).