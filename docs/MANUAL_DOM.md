# MANUAL DE AUTOMAÇÃO DE PHYSICAL DOMAINS (DOM) NO CISCO ACI

Este manual documenta os scripts Python desenvolvidos para automatizar o ciclo de vida de **Physical Domains** (Domínios Físicos) no Cisco ACI, permitindo a criação simples, criação com associação simultânea a **VLAN Pool** e **AAEP**, além da exclusão de domínios, suportando execução via linha de comando (CLI) ou arquivos de configuração (CSV/TXT).

---

## 1. Estrutura de Scripts na Pasta `dom`

- **`create-phys-dom-prod.py`**: Criação simples de um Physical Domain.
- **`create-phys-dom-with-vlanpool-prod.py`**: Criação de um Physical Domain com associação a um VLAN Pool e vinculação a um AAEP existente.
- **`delete-phys-dom-prod.py`**: Exclusão de um Physical Domain.

---

## 2. Como Utilizar

Todos os scripts aceitam duas formas de entrada: **Parâmetros via CLI** ou **Arquivo CSV**.

### A. Criação Simples de Physical Domain
#### Via CLI:
```bash
python3 dom/create-phys-dom-prod.py --dom-name JASONX1-DOM
```
#### Via CSV (`dom/input_create.csv`):
```csv
DOM_NAME
JASONX1-DOM
```
```bash
python3 dom/create-phys-dom-prod.py --arquivo dom/input_create.csv
```

---

### B. Criação com Associação (VLAN Pool + AAEP)
Cria o domínio, amarra ao VLAN Pool e associa ao AAEP de forma idempotente (`created,modified`).

#### Via CLI:
```bash
python3 dom/create-phys-dom-with-vlanpool-prod.py --dom-name JASONX2-DOM --pool-name JASONX1-POOL --aaep-name JASONX1-AAEP
```
#### Via CSV (`dom/input_assoc.csv`):
```csv
DOM_NAME,POOL_NAME,AAEP_NAME
JASONX2-DOM,JASONX1-POOL,JASONX1-AAEP
```
```bash
python3 dom/create-phys-dom-with-vlanpool-prod.py --arquivo dom/input_assoc.csv
```

---

### C. Deleção de Physical Domain
*(Nota: Ao deletar o Physical Domain pai no ACI, as amarrações filhas são removidas automaticamente).*

#### Via CLI:
```bash
python3 dom/delete-phys-dom-prod.py --dom-name JASONX2-DOM
```
#### Via CSV (`dom/input_delete.csv`):
```csv
DOM_NAME
JASONX2-DOM
```
```bash
python3 dom/delete-phys-dom-prod.py --arquivo dom/input_delete.csv
```

---

## 3. Autenticação
- Caso os argumentos `--user` ou `--pass` não sejam informados, o script solicitará interativamente as credenciais de acesso ao APIC.
- Comunicação via HTTPS REST API utilizando tokens de sessão (Cookies).
