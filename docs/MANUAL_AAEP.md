# MANUAL DE AUTOMAÇÃO DE AAEP NO CISCO ACI

Este manual documenta os scripts Python desenvolvidos para automatizar a criação e a exclusão de **AAEPs (Attachable Access Entity Profiles)** no Cisco ACI, suportando execução via linha de comando (CLI) ou arquivos de configuração (CSV/TXT).

---

## 1. Estrutura de Scripts na Pasta `aaep`

- **`create-aaep-prod.py`**: Cria o AAEP no escopo de infraestrutura do ACI (`uni/infra`).
- **`delete-aaep-prod.py`**: Deleta o AAEP especificado no APIC.

---

## 2. Como Utilizar

Ambos os scripts aceitam duas formas de entrada: **Parâmetros via CLI** ou **Arquivo CSV**.

### A. Criação de AAEP

#### Opção 1: Via Linha de Comando (CLI)
```bash
python3 aaep/create-aaep-prod.py --aaep-name JASONX1-AAEP
```

#### Opção 2: Via Arquivo CSV/TXT
Crie um arquivo (ex: `aaep/input_create.csv`) com o seguinte conteúdo:
```csv
AAEP_NAME
JASONX1-AAEP
```
Execute o comando passando o arquivo:
```bash
python3 aaep/create-aaep-prod.py --arquivo aaep/input_create.csv
```

---

### B. Deleção de AAEP

#### Opção 1: Via Linha de Comando (CLI)
```bash
python3 aaep/delete-aaep-prod.py --aaep-name JASONX1-AAEP
```

#### Opção 2: Via Arquivo CSV/TXT
Crie um arquivo (ex: `aaep/input_delete.csv`) com o seguinte conteúdo:
```csv
AAEP_NAME
JASONX1-AAEP
```
Execute o comando passando o arquivo:
```bash
python3 aaep/delete-aaep-prod.py --arquivo aaep/input_delete.csv
```

---

## 3. Autenticação
- Caso os argumentos `--user` ou `--pass` não sejam informados, o script solicitará interativamente as credenciais de acesso ao APIC.
- Comunicação via HTTPS REST API utilizando tokens de sessão (Cookies).
