Suíte modular de automação em Python para provisionamento, alteração e descomissionamento ponta a ponta de infraestrutura **Cisco ACI (Application Centric Infrastructure)** via API REST do APIC.

A ferramenta suporta execução **interativa via linha de comando (CLI)** para demandas pontuais e **processamento em lote via arquivos de entrada (`.txt`/`.csv`)** para entregas em escala, com validações idempotentes, relatórios detalhados e autenticação em tempo de execução (sem credenciais armazenadas em código).

## Arquitetura e Módulos

O projeto está dividido em 4 módulos principais que cobrem todo o ciclo de vida lógico e físico do fabric:

- **`tenant/`** — Criação e exclusão de **Tenants**, **VRFs** e **Application Profiles (APs)**.
- **`bd/`** — Provisionamento, vinculação a VRFs e remoção de **Bridge Domains (BDs)**.
- **`epg/`** — Criação e exclusão de **Endpoint Groups (EPGs)**, associação a **Bridge Domains** e **Physical Domains**, além de binding/unbinding de **Static Ports** (interfaces físicas `paths` e **vPC / Protected Paths** `protpaths`) e auditoria de associações vPC.
- **`l3out/`** — Provisionamento automatizado de conectividade externa **Layer 3 (L3Outs)** nos modos **SVI** e **Floating L3Out** (redes públicas com rota, públicas sem rota e privadas/internas).

## Documentação e Manuais Operacionais

Todos os guias passo a passo, parâmetros de CLI, layouts de arquivos em lote e checklists de produção estão centralizados na pasta [`docs/`](docs/):

| Módulo | Escopo da Operação | Manual |
| :--- | :--- | :--- |
| **Tenants & VRFs** | Criação e exclusão de Tenants, VRFs e Application Profiles | [MANUAL_TENANT_VRF.md](docs/MANUAL_TENANT_VRF.md) |
| **Bridge Domains** | Criação, associação a VRFs e exclusão de Bridge Domains | [MANUAL_BD.md](docs/MANUAL_BD.md) |
| **Endpoint Groups (EPGs)** | Criação de EPGs e vinculação aos Bridge Domains | [MANUAL_EPG.md](docs/MANUAL_EPG.md) |
| **Exclusão EPG / BD** | Remoção controlada de EPGs e Bridge Domains associados | [MANUAL_DELETE_EPG_BD.md](docs/MANUAL_DELETE_EPG_BD.md) |
| **Physical Domains** | Associação e desassociação de EPGs a Physical Domains | [MANUAL_CREATE_EPG_DOM.md](docs/MANUAL_CREATE_EPG_DOM.md) |
| **Static Ports (Físicas)** | Binding e unbinding de portas físicas (`paths`) aos EPGs | [MANUAL_STATIC_PORTS.md](docs/MANUAL_STATIC_PORTS.md) |
| **Static Ports (vPC)** | Binding e unbinding de portas protegidas (`protpaths`) aos EPGs | [MANUAL_STATIC_PORTS_VPC.md](docs/MANUAL_STATIC_PORTS_VPC.md) |
| **L3Outs (SVI & Floating)** | Provisionamento de conectividade externa Layer 3 | [MANUAL_L3OUT.md](docs/MANUAL_L3OUT.md) |

## Segurança e Boas Práticas

- **Zero Hardcoded Credentials:** Nenhuma senha, token ou IP de gerência é armazenado nos scripts ou arquivos de configuração.
- **Autenticação Interativa:** O endereço do APIC, usuário e senha (com entrada oculta no terminal) são solicitados no início de cada execução.
- **Idempotência:** Os scripts verificam a existência prévia dos objetos antes de aplicar alterações no fabric, evitando conflitos ou sobrescritas acidentais.
- **Evidências de Mudança:** Suporte nativo ao parâmetro `--log-file` e modo detalhado (`-v`) para auditoria e controle de GMUD.

## Requisitos e Instalação

1. Clone o repositório:

       git clone https://github.com/vinicius-clemente/automator-infra-aci.git
       cd automator-infra-aci

2. Instale a dependência principal (`requests`):

       pip install -r requirements.txt

3. Consulte o manual do módulo desejado na pasta `docs/` ou execute qualquer script com `--help`:

       python3 tenant/create-tenant-vrf-prod.py --help

## Licença

Este projeto está licenciado sob a licença MIT — veja o arquivo [LICENSE](LICENSE) para detalhes.
