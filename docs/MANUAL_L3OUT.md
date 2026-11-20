# MANUAL DE AUTOMAÇÃO DE L3OUT NO CISCO ACI

Este manual documenta o ecossistema de scripts Python desenvolvidos para automatizar a criação de **L3Outs** (tanto SVI tradicional quanto Floating IP) no Cisco ACI, abrangendo a criação de perfis de nós, interfaces, rotas estáticas, perfis externos (ExtEPG) e a divulgação automática de redes nos L3Outs do Tenant e do Common.

---

## 1. Estrutura de Diretórios e Scripts

Todos os scripts encontram-se na pasta de automação de l3out.

### Scripts de SVI Tradicional:
- **`create-l3out-route-svi-public-prod.py`**: SVI com IP/Rede SVI pública e com rota estática pública.
- **`create-l3out-route-svi-privado-prod.py`**: SVI com IP/Rede SVI privada, com rota estática, divulgando apenas a rota pública.
- **`create-l3out-svi-no-public-prod.py`**: SVI com IP SVI privado e rota estática pública.
- **`create-l3out-svi-no-route.py`** / **`create-l3out-no-route-svi-public-prod.py`**: SVI com IP público sem rota estática.

### Scripts de Floating IP (Interface Virtual):
- **`create-l3out-floating-public-prod.py`**: Floating IP com SVI pública e com rota estática.
- **`create-l3out-floating-no-public-prod.py`**: Floating IP com SVI privada e com rota estática pública.
- **`create-l3out-floating-public-no-route-prod.py`**: Floating IP com SVI pública e sem rota estática.

---

## 2. Funcionamento do Fluxo Automatizado

Cada script executa o seguinte fluxo de ponta a ponta em uma única execução:
1. **Autenticação:** Conecta na API REST do APIC via `aaaLogin` utilizando as credenciais fornecidas.
2. **Criação do L3Out:**
   - Associa o L3 Domain (`l3extRsL3DomAtt`) e a VRF (`l3extRsEctx`).
   - Cria o perfil de nós (`l3extLNodeP`) com os Router IDs dos Leafs e insere as rotas estáticas (se aplicável).
   - Cria o perfil de interface (`l3extLIfP`), configurando SVI Tradicional (`rspathL3OutAtt`) ou Floating IP (`l3extVirtualLIfP` com `l3extRsDynPathAtt` e `floatingAddr`).
   - Cria o External EPG (`l3extInstP`) com as subnets correspondentes e contratos de trânsito.
3. **Divulgação no L3Out do Tenant:** Adiciona automaticamente as subnets/rotas no ExtEPG do L3Out de exportação do Tenant com escopo `export-rtctrl` e Route Map de exportação.
4. **Divulgação no Common:** Publica as redes no ExtEPG compartilhado do Common.

---

## 3. Como Utilizar (Via Arquivo TXT/CSV)

O método recomendado para execução em produção é a utilização de um arquivo de configuração (TXT/CSV contendo cabeçalho na 1ª linha e os dados na 2ª linha).

### Exemplo de Estrutura do Arquivo de Entrada (`l3out_input.txt`):
```csv
TENANT_CREATE,L3OUT_CREATE_NAME,VRF_NAME,L3_DOMAIN_NAME,INTERFACE_VLAN,LEAF_NODES,LEAF_IP_A,LEAF_IP_B,VIP_IP,FLOATING_IP,PHYS_DOM_A,PHYS_DOM_B,SUBNETS,ROUTE_SUBNET,ROUTE_SUBNET_NAME,NEXTHOP_IP,ROUTER_ID_A,ROUTER_ID_B,PATH_EP_NAME,MAC_ADDRESS,MTU_VALUE,TENANT_L3OUT_EXPORT,TENANT_EXTEPG_EXPORT,EXPORT_ROUTE_MAP,COMMON_L3OUT_EXPORT,COMMON_EXTEPG_EXPORT
<TENANT>,<L3OUT_NAME>,<VRF>,<L3_DOM>,<VLAN>,201;202,<IP_A>,<IP_B>,<VIP>,<FLOATING_IP>,<DOM_A>,<DOM_B>,<SUBNET>,<ROUTE>,<ROUTE_NAME>,<NEXTHOP>,<RTR_ID_A>,<RTR_ID_B>,<PATH_NAME>,<MAC>,9216,<TENANT_EXPORT_L3OUT>,<TENANT_EXPORT_EXTEPG>,<ROUTE_MAP>,<COMMON_EXPORT_L3OUT>,<COMMON_EXPORT_EXTEPG>
```

### Comando de Execução:
```bash
python3 create-l3out-floating-public-prod.py --arquivo l3out_input.txt
```
*(O script solicitará apenas o usuário e a senha do APIC).*

---

## 4. Cuidados e Validações Importantes

1. **VLAN Pool:** Certifique-se de que a VLAN informada (`INTERFACE_VLAN`) está criada e liberada no **VLAN Pool** associado ao L3 Domain daquele L3Out. Caso contrário, a API retornará o erro code `105` (`encap is not in range with associated vlan pool`).
2. **Nomes de Domínios Físicos / Domínios L3:** Os nomes dos domínios passados nos parâmetros devem existir previamente no ACI.
3. **Segurança:** O script desliga os avisos de certificado auto-assinado (`InsecureRequestWarning`), comunicando-se via HTTPS com o APIC de forma segura através de tokens de sessão (Cookies).

