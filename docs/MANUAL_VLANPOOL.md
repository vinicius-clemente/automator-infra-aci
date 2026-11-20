# MANUAL DE AUTOMAÇÃO DE VLAN POOLS NO CISCO ACI

Este manual documenta os scripts Python desenvolvidos para automatizar a criação e a exclusão de **VLAN Pools** e blocos de encapsulamento no Cisco ACI, suportando execução via linha de comando (CLI) ou arquivos de configuração (CSV/TXT).

---

## 1. Estrutura de Scripts na Pasta `vlanpool`

- **`create-vlanpool-prod.py`**: Cria o VLAN Pool (modo estático, dinâmico ou inherit) e adiciona o bloco de VLANs correspondente.
- **`delete-vlanpool-prod.py`**: Deleta o VLAN Pool especificado no APIC.

---

## 2. Como Utilizar

Ambos os scripts permitem duas formas de entrada de dados: **Parâmetros diretos via CLI** ou **Arquivo CSV**.

### A. Criação de VLAN Pool

#### Opção 1: Via Linha de Comando (CLI)
```bash
python3 vlanpool/create-vlanpool-prod.py --pool-name JASONX1-POOL --alloc-mode static --vlan-from 11 --vlan-to 11
```

#### Opção 2: Via Arquivo CSV/TXT
Crie um arquivo (ex: `vlanpool/input_create.csv`) com o seguinte conteúdo:
```csv
POOL_NAME,ALLOC_MODE,VLAN_FROM,VLAN_TO
JASONX1-POOL,static,11,11
```
Execute o comando passando o arquivo:
```bash
python3 vlanpool/create-vlanpool-prod.py --arquivo vlanpool/input_create.csv
```

---

### B. Deleção de VLAN Pool

#### Opção 1: Via Linha de Comando (CLI)
```bash
python3 vlanpool/delete-vlanpool-prod.py --pool-name JASONX1-POOL --alloc-mode static
```

#### Opção 2: Via Arquivo CSV/TXT
Crie um arquivo (ex: `vlanpool/input_delete.csv`) com o seguinte conteúdo:
```csv
POOL_NAME,ALLOC_MODE
JASONX1-POOL,static
```
Execute o comando passando o arquivo:
```bash
python3 vlanpool/delete-vlanpool-prod.py --arquivo vlanpool/input_delete.csv
```

---

## 3. Autenticação e Segurança
- Durante a execução, caso os argumentos `--user` ou `--pass` não sejam passados, o script solicitará interativamente as credenciais de acesso ao APIC.
- Os scripts realizam autenticação segura via token de sessão (Cookies) utilizando a API REST do Cisco ACI.
