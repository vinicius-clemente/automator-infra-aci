# MANUAL - Exclusão de EPG e BD no Cisco ACI

Script: `delete-epg-bd-prod.py`

---

## 1. Visão geral

Este script deleta Endpoint Groups (EPGs) e opcionalmente seus Bridge Domains (BDs) associados no Cisco ACI.

## 2. Formato do arquivo de entrada (`delete-epg-bd.txt`)

```
tenant,app_profile,epg[,bd]
```

| Coluna | Campo | Obrigatório? | Descrição |
|--------|-------|--------------|-----------|
| 1 | tenant | Sim | Nome do Tenant |
| 2 | app_profile | Sim | Nome do Application Profile |
| 3 | epg | Sim | Nome do EPG |
| 4 | bd | Não | Nome do BD (apenas se quiser deletar o BD também) |

Exemplo:

```
TENANT_EXEMPLO,AP_DADOS,EPG_CLIENTES
TENANT_EXEMPLO,AP_DADOS,EPG_SERVIDORES,BD_SERVIDORES
OUTRO-TENANT,AP_GERENCIA,EPG_GER,BD_GER
```

## 3. Como executar

### Via arquivo (padrão `delete-epg-bd.txt`)

```powershell
python3 epg/delete-epg-bd-prod.py -v --log-file deletar.log
```

### Via linha de comando (sem arquivo)

**Deletar apenas o EPG (sem deletar BD):**
```powershell
python3 epg/delete-epg-bd-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG_CLIENTES -v
```

**Deletar vários EPGs (mesmo tenant/AP):**
```powershell
python3 epg/delete-epg-bd-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG1 --epg EPG2 -v
```

**Deletar EPG e o BD associado:**
```powershell
python3 epg/delete-epg-bd-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG_CLIENTES --bd BD_CLIENTES --deletar-bd -v
```

**Deletar vários EPGs e seus BDs:**
```powershell
python3 epg/delete-epg-bd-prod.py --tenant TENANT_EXEMPLO --ap AP_DADOS --epg EPG1 --epg EPG2 --bd BD1 --bd BD2 --deletar-bd -v
```

## 4. Parâmetros

| Parâmetro | Descrição |
|-----------|-----------|
| `--tenant` | Nome do tenant (modo simples) |
| `--ap` | Nome do Application Profile (modo simples) |
| `--epg` | Nome do EPG (repita para vários) |
| `--bd` | Nome do BD associado (repita para vários, deve bater com --epg) |
| `--deletar-bd` | Se informado, também deleta o BD após deletar o EPG |
| `--arquivo` | Arquivo de entrada (padrão: `delete-epg-bd.txt`) |
| `-v` | Modo verbose |
| `--log-file` | Salva log em arquivo |

## 5. Regras importantes

- O EPG é deletado primeiro, depois o BD (se `--deletar-bd` for usado).
- Se o EPG ou BD não existir, o script apenas informa "pulando" e continua.
- Se houver falha em um item, o script continua com os próximos e sai com código de erro no final.
- Credenciais são pedidas na tela (senha não aparece).
- `User-Agent` do navegador é usado para evitar bloqueio do antivírus do APIC.

---

Fim do manual.
