# MANUAL - Automação de Bridge Domain (BD) no Cisco ACI

Este manual explica como usar os scripts de criação e exclusão de Bridge Domains
no Cisco ACI via API REST do APIC.

Público-alvo: analistas juniores de rede/infraestrutura.

---

## 1. Visão geral

A pasta `bd/` contém os seguintes scripts:

| Script | Função | Arquivo de entrada padrão |
|--------|--------|---------------------------|
| `create-bds-prod.py` | Cria um ou vários Bridge Domains | `bds.txt` (via `--arquivo`) |
| `delete-bds-prod.py` | Deleta um ou vários Bridge Domains | `delete-bds.txt` (padrão automático) |
| `config.ini` | Configurações padrão do APIC (URL, usuário, senha) | — |

O que os scripts fazem:
1. Pedem **usuário e senha na tela** (a senha não aparece ao digitar).
2. Autenticam no APIC.
3. Verificam se cada BD **já existe** antes de criar ou excluir.
4. Criam ou deletam os BDs solicitados.
5. Mostram um **relatório na tela** (criados, pulados, falhas) e opcionalmente salvam em arquivo de log (`--log-file`).

Nunca armazene senhas no código. Use o `config.ini` apenas para a URL do APIC (opcional).

---

## 2. Formato dos arquivos de entrada

Os arquivos de texto devem ter uma linha por Bridge Domain.

### Formato aceito (criação e exclusão)

```
tenant,vrf,bd
```

Exemplo (`bds.txt` para criação):

```
HUAWEI,VRF_DCS_HUAWEI,TESTE-BD10
HUAWEI,VRF_DCS_HUAWEI,TESTE-BD11
OUTRO-TENANT,VRF_DEV,TESTE-BD12
TERCEIRO,VRF_PROD,BD_A01
```

Exemplo (`delete-bds.txt` para exclusão):

```
HUAWEI,VRF_DCS_HUAWEI,TESTE-BD10
OUTRO-TENANT,VRF_DEV,TESTE-BD12
```

Regras:
- **Coluna 1:** nome do Tenant no ACI.
- **Coluna 2:** nome da VRF (usado apenas na criação; ignorado na exclusão).
- **Coluna 3:** nome do Bridge Domain.
- Linhas iniciando com `#` são ignoradas (comentários).
- Linhas em branco são ignoradas.
- Você também pode usar apenas 2 colunas (`tenant,bd`) na exclusão.

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
| `--tenant` + `--bd` | Usa **apenas** os BDs informados na linha de comando e ignora o arquivo padrão |
| Somente `--arquivo` (ou nada) | Lê o arquivo padrão (`bds.txt` ou `delete-bds.txt`) |

Isso significa que se você quer criar/deletar BDs específicos, use `--tenant` + `--bd` diretamente. Se quer processar vários de uma vez, use o arquivo.

### 3.1 Criar um ou vários BDs (modo simples)

Útil quando todos os BDs têm o mesmo tenant e mesma VRF.

**Criar 1 BD único:**
```bash
python3 bd/create-bds-prod.py --tenant HUAWEI --vrf VRF_DCS_HUAWEI --bd TESTE-BD10 -v
```

**Criar vários BDs (mesmo tenant e mesma VRF):**
```bash
python3 bd/create-bds-prod.py --tenant HUAWEI --vrf VRF_DCS_HUAWEI --bd TESTE-BD10 --bd TESTE-BD11 --bd TESTE-BD12 -v
```

Parâmetros:
- `--tenant` : nome do tenant
- `--vrf` : nome da VRF associada
- `--bd` : nome do BD (repita o parâmetro para vários BDs)
- `-v` : modo verbose (mostra detalhes passo a passo)
- `--log-file nome.log` : salva o relatório também em arquivo

### 3.2 Criar vários BDs via arquivo (recomendado para produção)

```bash
python3 bd/create-bds-prod.py --arquivo bd/bds.txt -v --log-file criar.log
```

Cada linha do arquivo define seu próprio tenant, VRF e BD.

### 3.3 Excluir um ou vários BDs (modo simples)

**Excluir 1 BD único:**
```bash
python3 bd/delete-bds-prod.py --tenant HUAWEI --bd TESTE-BD10 -v
```

**Excluir vários BDs (mesmo tenant):**
```bash
python3 bd/delete-bds-prod.py --tenant HUAWEI --bd TESTE-BD10 --bd TESTE-BD11 --bd TESTE-BD12 -v
```

### 3.4 Excluir vários BDs via arquivo

O script procura por padrão o arquivo `delete-bds.txt` na pasta `bd/`.

```bash
python3 bd/delete-bds-prod.py -v --log-file deletar.log
```

Ou informe outro nome de arquivo:

```bash
python3 bd/delete-bds-prod.py --arquivo bd/minha-lista-delete.txt -v
```

---

## 4. Exemplos práticos

### Cenário A: Criar 5 BDs em uma VRF, 4 BDs em outra VRF, tenants diferentes

Arquivo `bds.txt`:

```
TENANT_PROD,VRF_PROD,BD_PROD01
TENANT_PROD,VRF_PROD,BD_PROD02
TENANT_PROD,VRF_PROD,BD_PROD03
TENANT_PROD,VRF_PROD,BD_PROD04
TENANT_PROD,VRF_PROD,BD_PROD05
TENANT_DEV,VRF_DEV,BD_DEV01
TENANT_DEV,VRF_DEV,BD_DEV02
TENANT_DEV,VRF_DEV,BD_DEV03
TENANT_DEV,VRF_DEV,BD_DEV04
```

Execução:

```bash
python3 bd/create-bds-prod.py --arquivo bd/bds.txt -v --log-file criar_prod.log
```

### Cenário B: Excluir apenas os BDs que não servem mais

Arquivo `delete-bds.txt`:

```
TENANT_DEV,VRF_DEV,BD_DEV01
TENANT_DEV,VRF_DEV,BD_DEV02
```

Execução:

```bash
python3 bd/delete-bds-prod.py -v --log-file deletar_dev.log
```

### Cenário C: Criar um BD único rápido

```bash
python3 bd/create-bds-prod.py --tenant HUAWEI --vrf VRF_DCS_HUAWEI --bd BD_NOVO -v
```

---

## 5. Interpretando o relatório

Exemplo de saída na tela:

```
======================================================================
REPORT - CRIAÇÃO DE BRIDGE DOMAINS (LOTE)
======================================================================
APIC   : https://172.30.104.5
Usuário: 80689851
Qtd BD : 4
----------------------------------------------------------------------
🔎 Verificando 'HUAWEI/TESTE-BD10' -> não encontrado
📡 Criando 'HUAWEI/TESTE-BD10' (VRF 'VRF_DCS_HUAWEI')... Status: 200
✅ BD 'HUAWEI/TESTE-BD10' criado com sucesso.
✅ 'HUAWEI/TESTE-BD10' (VRF 'VRF_DCS_HUAWEI') criado com sucesso.
🔎 Verificando 'HUAWEI/TESTE-BD11' -> encontrado
⚠️  'HUAWEI/TESTE-BD11' já existe. Pulando.
----------------------------------------------------------------------
RESUMO
----------------------------------------------------------------------
Tenants processados: 1
  📦 HUAWEI
Criados : 1
  ✅ HUAWEI/TESTE-BD10
Pulados : 1 (já existiam)
  ⚠️  HUAWEI/TESTE-BD11
Falhas  : 0
======================================================================
```

Significado dos status:
- ✅ **Criado/Deletado com sucesso:** operação concluída no APIC.
- ⚠️ **Pulado:** o BD já existia (criação) ou não existia (exclusão). Nenhuma ação foi tomada.
- ❌ **Falha:** erro de rede ou rejeição pelo APIC. Verifique o log e as credenciais.

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

## 7. Arquivos na pasta `bd/`

```
bd/
├── create-bds-prod.py      # Script de criação (recomendado)
├── create-bd-prod.py       # Script de criação de um único BD (alternativa simples)
├── delete-bds-prod.py      # Script de exclusão
├── delete-bd-prod.py       # (se existir) exclusão de um único BD
├── config.ini              # Configurações padrão do APIC (opcional)
├── bds.txt                 # Exemplo de entrada para criação
├── delete-bds.txt          # Exemplo de entrada para exclusão
└── MANUAL.md               # Este arquivo
```

---

## 8. Checklist antes de rodar em produção

- [ ] Verifique se o arquivo de entrada (`bds.txt` ou `delete-bds.txt`) está com o formato correto (`tenant,vrf,bd`).
- [ ] Confirme os nomes dos Tenants, VRFs e BDs no APIC antes de rodar.
- [ ] Rode primeiro com `-v` para ver o que será feito sem surpresas.
- [ ] Use `--log-file` para guardar evidência da execução.
- [ ] Nunca compartilhe arquivos de log que contenham senhas (os logs destes scripts não gravam senhas, mas podem conter nomes de tenants/BDs).

---

## 9. Dúvidas comuns

**Q: Posso criar BDs em tenants diferentes na mesma execução?**
A: Sim. Use o arquivo de entrada (`--arquivo`) com linhas diferentes para cada tenant.

**Q: Posso excluir um BD que não existe?**
A: Sim. O script verifica antes e apenas informa que não existe (pulado), não gera erro.

**Q: O script deleta VRFs ou Tenants?**
A: Não. Ele só deleta os Bridge Domains listados no arquivo ou parâmetro `--bd`.

**Q: Esqueci a senha. O que faço?**
A: O script não armazena senha. Peça ao responsável de segurança ou use seu usuário pessoal do APIC.

---

Fim do manual.
