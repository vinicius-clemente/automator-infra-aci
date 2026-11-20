# Automator Infra Cisco ACI

Suíte modular em **Python** para automação *end-to-end* de provisionamento, alteração e descomissionamento de infraestrutura em fabrics **Cisco ACI** diretamente via **APIC REST API**.

O projeto organiza os fluxos operacionais por domínio funcional (Fabric Access Policies, Tenant/VRF, Bridge Domains, EPGs, Static Ports/vPC e L3Outs), suportando execução interativa via CLI e operações em lote (*batch* via CSV/TXT) com validação prévia de estado e tratamento de erros.

---

## 📁 Estrutura do Repositório

```text
automator-infra-aci/
├── tenant/       # Provisionamento de Tenants e VRFs
├── bd/           # Criação e configuração de Bridge Domains e Subnets
├── epg/          # Gestão de Application Profiles, EPGs, Static Ports (Access/vPC) e limpeza
├── l3out/        # Automação de L3Outs e conectividade externa
├── physical/     # Fabric Access Policies: VLAN Pools, AAEPs e Physical Domains
└── docs/         # Manuais operacionais detalhados por módulo

🚀 Módulos e FuncionalidadesFabric Access Policies (physical/):
Criação de VLAN Pools (alocação estática/dinâmica e faixas de VLAN).
Provisionamento de AAEPs (Attachable Access Entity Profiles).
Criação de Physical Domains completos ou criação de novos domínios com associação direta a VLAN Pools e AAEPs pré-existentes.

Tenant & VRF (tenant/):
Criação automatizada de Tenants e VRFs associados.

Bridge Domains (bd/):
Provisionamento de Bridge Domains, associação à VRF, configuração de gateways (Subnets) e flags de encaminhamento L2/L3.

EPGs & Port Bindings (epg/):
Criação de EPGs com vínculo a Bridge Domains e Physical Domains.
Deploy em lote de Static Ports (interfaces individuais/Port-Channel) e Static Ports vPC (Virtual Port-Channel).
Rotina segura de exclusão/descomissionamento de EPGs e Bridge Domains.

L3Out (l3out/):
Automação de conectividade Layer 3 externa.

📚 Documentação Operacional (docs/)
Cada fluxo possui um guia técnico detalhado com estrutura de arquivos de entrada, parâmetros e exemplos de execução:

Módulo / Operação				                      Manual
VLAN Pool (Criação e faixas)			            docs/MANUAL_VLANPOOL.md
AAEP (Attachable Access Entity Profile)		    docs/MANUAL_AAEP.md
Physical Domain (Criação e associação)		    docs/MANUAL_DOM.md
Tenant & VRF					                        docs/MANUAL_TENANT_VRF.md
Bridge Domain (BD)				                    docs/MANUAL_BD.md
Endpoint Group (EPG)				                  docs/MANUAL_EPG.md
Criação Integrada (EPG + Domain)		          docs/MANUAL_CREATE_EPG_DOM.md
Static Ports (Access / Port-Channel)		      docs/MANUAL_STATIC_PORTS.md
Static Ports vPC				                      docs/MANUAL_STATIC_PORTS_VPC.md
L3Out						                              docs/MANUAL_L3OUT.md
Descomissionamento (Delete EPG / BD)		      docs/MANUAL_DELETE_EPG_BD.md

⚙️ Pré-requisitos e InstalaçãoPython 3.8+
Acesso HTTPS (porta 443) ao Cisco APIC com usuário habilitado para chamadas REST API.

Clone o repositório:
Bash
git clone [https://github.com/vinicius-clemente/automator-infra-aci.git](https://github.com/vinicius-clemente/automator-infra-aci.git)
cd automator-infra-aci

Instale as dependências necessárias:
Bash
pip install requests urllib3

Navegue até o diretório do módulo desejado (ex.: physical/, tenant/, bd/, epg/, l3out/) e execute o script correspondente conforme o manual em docs/.

📄 Licença
Este projeto está licenciado sob a licença MIT — veja o arquivo LICENSE para detalhes.
EOF

git add README.md
git commit -m "Add formatted README with module overview and documentation links"
git push


Depois do `git push`, basta dar F5 na página do `automator-infra-aci` no GitHub que a tabela, os blocos de código e todos os 11 links dos manuais já vão aparecer formatados.
