import argparse
import csv
import json
import os
import sys
import getpass
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_APIC_IP = "X.X.X.X"

def load_vars_from_csv(csv_file):
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo CSV não encontrado: {csv_file}")
        sys.exit(1)
    with open(csv_file, newline="", encoding="utf-8") as f:
        lines = [line for line in f if not line.lstrip().startswith("#")]
        reader = csv.DictReader(lines)
        rows = list(reader)
        if len(rows) != 1:
            raise ValueError("O CSV deve conter exatamente 1 linha de dados válida")
        r = {k: (v or "").strip() for k, v in rows[0].items()}
        return {
            "TENANT_CREATE": r.get("TENANT_CREATE", "DADOS"),
            "L3OUT_CREATE_NAME": r.get("L3OUT_CREATE_NAME"),
            "VRF_NAME": r.get("VRF_NAME", "VRF_DADOS"),
            "L3_DOMAIN_NAME": r.get("L3_DOMAIN_NAME"),
            "INTERFACE_VLAN": r.get("INTERFACE_VLAN"),
            "LEAF_NODES": [n.strip() for n in r.get("LEAF_NODES", "201;202").split(";") if n.strip()],
            "LEAF_IP_A": r.get("LEAF_IP_A"),
            "LEAF_IP_B": r.get("LEAF_IP_B"),
            "FLOATING_IP": r.get("FLOATING_IP"),
            "PHYS_DOM_A": r.get("PHYS_DOM_A"),
            "PHYS_DOM_B": r.get("PHYS_DOM_B"),
            # Subnets públicas da SVI (sem rota) que serão divulgadas no Tenant e Common
            "SUBNETS": [s.strip() for s in r.get("SUBNETS", "").split(";") if s.strip()],
            "ROUTER_ID_A": r.get("ROUTER_ID_A"),
            "ROUTER_ID_B": r.get("ROUTER_ID_B"),
            "MAC_ADDRESS": r.get("MAC_ADDRESS", "00:22:BD:F8:19:FF"),
            "MTU_VALUE": r.get("MTU_VALUE", "9216"),
            "TENANT_L3OUT_EXPORT": r.get("TENANT_L3OUT_EXPORT", "DADOS-L3OUT"),
            "TENANT_EXTEPG_EXPORT": r.get("TENANT_EXTEPG_EXPORT", "Dados_L3Out_ExtEPG"),
            "EXPORT_ROUTE_MAP": r.get("EXPORT_ROUTE_MAP", "EXPORT_TO_TAMBORE"),
            "COMMON_L3OUT_EXPORT": r.get("COMMON_L3OUT_EXPORT", "ACI_INET_SHARED"),
            "COMMON_EXTEPG_EXPORT": r.get("COMMON_EXTEPG_EXPORT", "SHARED_INET_CONT")
        }

def parse_args():
    parser = argparse.ArgumentParser(description="Criação de L3Out Floating IP Público sem rota (Cisco ACI)")
    parser.add_argument("--arquivo", help="Caminho para arquivo CSV com variáveis")
    parser.add_argument("--tenant", default="DADOS", help="Nome do Tenant")
    parser.add_argument("--l3out", help="Nome do L3Out")
    parser.add_argument("--vrf", default="VRF_DADOS", help="Nome da VRF")
    parser.add_argument("--l3dom", help="Nome do L3 Domain")
    parser.add_argument("--vlan", help="VLAN ID")
    parser.add_argument("--leaf-a", help="IP do Leaf A")
    parser.add_argument("--leaf-b", help="IP do Leaf B")
    parser.add_argument("--floating-ip", help="Floating IP")
    parser.add_argument("--phys-dom-a", help="Physical Domain do Leaf A")
    parser.add_argument("--phys-dom-b", help="Physical Domain do Leaf B")
    parser.add_argument("--subnets", help="Subnets públicas separadas por ponto e vírgula (;)")
    parser.add_argument("--router-a", help="Router ID do Leaf A")
    parser.add_argument("--router-b", help="Router ID do Leaf B")
    parser.add_argument("--mac", default="00:22:BD:F8:19:FF", help="Endereço MAC")
    parser.add_argument("--mtu", default="9216", help="MTU")
    parser.add_argument("--apic", default=DEFAULT_APIC_IP, help="IP do APIC")
    parser.add_argument("--user", default=None, help="Usuário do APIC")
    parser.add_argument("--pass", dest="password", default=None, help="Senha do APIC")
    return parser.parse_args()

def get_config(args):
    if args.arquivo:
        print(f"📄 Lendo configurações do arquivo: {args.arquivo}")
        cfg = load_vars_from_csv(args.arquivo)
    else:
        subnets = [s.strip() for s in (args.subnets or "").split(";") if s.strip()]
        cfg = {
            "TENANT_CREATE": args.tenant,
            "L3OUT_CREATE_NAME": args.l3out,
            "VRF_NAME": args.vrf,
            "L3_DOMAIN_NAME": args.l3dom,
            "INTERFACE_VLAN": args.vlan,
            "LEAF_NODES": ["201", "202"],
            "LEAF_IP_A": args.leaf_a,
            "LEAF_IP_B": args.leaf_b,
            "FLOATING_IP": args.floating_ip,
            "PHYS_DOM_A": args.phys_dom_a,
            "PHYS_DOM_B": args.phys_dom_b,
            "SUBNETS": subnets,
            "ROUTER_ID_A": args.router_a,
            "ROUTER_ID_B": args.router_b,
            "MAC_ADDRESS": args.mac,
            "MTU_VALUE": args.mtu,
            "TENANT_L3OUT_EXPORT": "DADOS-L3OUT",
            "TENANT_EXTEPG_EXPORT": "Dados_L3Out_ExtEPG",
            "EXPORT_ROUTE_MAP": "EXPORT_TO_TAMBORE",
            "COMMON_L3OUT_EXPORT": "ACI_INET_SHARED",
            "COMMON_EXTEPG_EXPORT": "SHARED_INET_CONT"
        }
    
    user = args.user
    password = args.password
    if not user:
        user = input("Usuário APIC: ").strip()
        while not user:
            user = input("Usuário APIC (obrigatório): ").strip()
    if not password:
        password = getpass.getpass("Senha APIC: ")

    cfg["APIC_IP"] = args.apic
    cfg["USERNAME"] = user
    cfg["PASSWORD"] = password
    return cfg

def login(apic_ip, username, password):
    login_url = f"https://{apic_ip}/api/aaaLogin.json"
    payload = {"aaaUser": {"attributes": {"name": username, "pwd": password}}}
    print(f"🔑 Autenticando em https://{apic_ip}...")
    try:
        r = requests.post(login_url, json=payload, verify=False, timeout=10)
        r.raise_for_status()
        print("✅ Autenticação realizada com sucesso.")
        return r.cookies
    except requests.RequestException as e:
        print(f"❌ Erro na autenticação: {e}")
        sys.exit(1)

def criar_l3out_floating_public_no_route(cfg, cookies):
    apic_ip = cfg["APIC_IP"]
    tenant = cfg["TENANT_CREATE"]
    l3out_name = cfg["L3OUT_CREATE_NAME"]
    vrf = cfg["VRF_NAME"]
    l3dom = cfg["L3_DOMAIN_NAME"]
    vlan = cfg["INTERFACE_VLAN"]
    leaf_nodes = cfg["LEAF_NODES"]
    leaf_ip_a = cfg["LEAF_IP_A"]
    leaf_ip_b = cfg["LEAF_IP_B"]
    floating_ip = cfg["FLOATING_IP"]
    phys_dom_a = cfg["PHYS_DOM_A"]
    phys_dom_b = cfg["PHYS_DOM_B"]
    subnets = cfg["SUBNETS"]
    rtr_id_a = cfg["ROUTER_ID_A"]
    rtr_id_b = cfg["ROUTER_ID_B"]
    mac = cfg["MAC_ADDRESS"]
    mtu = cfg["MTU_VALUE"]

    url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant}/out-{l3out_name}.json"

    # Montar subnets do ExtEPG do próprio L3Out novo
    extepg_children = [
        {
            "fvRsProv": {"attributes": {"tnVzBrCPName": "TRANSIT_ROUTING_ALL", "status": "created,modified"}},
        },
        {
            "fvRsCons": {"attributes": {"tnVzBrCPName": "TRANSIT_ROUTING_ALL", "status": "created,modified"}},
        }
    ]
    for idx, sub in enumerate(subnets):
        s_name = f"{l3out_name}_pub_{idx+1}"
        extepg_children.append({
            "l3extSubnet": {
                "attributes": {
                    "ip": sub,
                    "name": s_name,
                    "scope": "import-security,shared-security,shared-rtctrl",
                    "aggregate": "",
                    "status": "created"
                }
            }
        })

    payload = {
        "l3extOut": {
            "attributes": {
                "dn": f"uni/tn-{tenant}/out-{l3out_name}",
                "name": l3out_name,
                "status": "created"
            },
            "children": [
                {"l3extRsL3DomAtt": {"attributes": {"tDn": f"uni/l3dom-{l3dom}", "status": "created"}}},
                {"l3extRsEctx": {"attributes": {"tnFvCtxName": vrf, "status": "created,modified"}}},
                {
                    "l3extInstP": {
                        "attributes": {
                            "dn": f"uni/tn-{tenant}/out-{l3out_name}/instP-{l3out_name}_ExtPG",
                            "name": f"{l3out_name}_ExtPG",
                            "status": "created"
                        },
                        "children": extepg_children
                    }
                },
                {
                    "l3extLNodeP": {
                        "attributes": {
                            "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile",
                            "name": f"{l3out_name}_nodeProfile",
                            "status": "created"
                        },
                        "children": [
                            {
                                "l3extRsNodeL3OutAtt": {
                                    "attributes": {
                                        "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/rsnodeL3OutAtt-[topology/pod-1/node-{leaf_nodes[0]}]",
                                        "tDn": f"topology/pod-1/node-{leaf_nodes[0]}",
                                        "rtrId": rtr_id_a,
                                        "rtrIdLoopBack": "false",
                                        "status": "created"
                                    }
                                }
                            },
                            {
                                "l3extRsNodeL3OutAtt": {
                                    "attributes": {
                                        "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/rsnodeL3OutAtt-[topology/pod-1/node-{leaf_nodes[1]}]",
                                        "tDn": f"topology/pod-1/node-{leaf_nodes[1]}",
                                        "rtrId": rtr_id_b,
                                        "rtrIdLoopBack": "false",
                                        "status": "created"
                                    }
                                }
                            },
                            {
                                "l3extLIfP": {
                                    "attributes": {
                                        "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/lifp-{l3out_name}_vpcIpv4",
                                        "name": f"{l3out_name}_vpcIpv4",
                                        "status": "created,modified"
                                    },
                                    "children": [
                                        {
                                            "l3extVirtualLIfP": {
                                                "attributes": {
                                                    "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/lifp-{l3out_name}_vpcIpv4/vlifp-[topology/pod-1/node-{leaf_nodes[0]}]-[vlan-{vlan}]",
                                                    "mac": mac,
                                                    "ifInstT": "ext-svi",
                                                    "nodeDn": f"topology/pod-1/node-{leaf_nodes[0]}",
                                                    "addr": leaf_ip_a,
                                                    "encap": f"vlan-{vlan}",
                                                    "mtu": mtu,
                                                    "status": "created"
                                                },
                                                "children": [
                                                    {
                                                        "l3extRsDynPathAtt": {
                                                            "attributes": {
                                                                "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/lifp-{l3out_name}_vpcIpv4/vlifp-[topology/pod-1/node-{leaf_nodes[0]}]-[vlan-{vlan}]/rsdynPathAtt-[{phys_dom_a}]",
                                                                "tDn": phys_dom_a,
                                                                "floatingAddr": floating_ip,
                                                                "encap": f"vlan-{vlan}",
                                                                "status": "created"
                                                            }
                                                        }
                                                    }
                                                ]
                                            }
                                        },
                                        {
                                            "l3extVirtualLIfP": {
                                                "attributes": {
                                                    "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/lifp-{l3out_name}_vpcIpv4/vlifp-[topology/pod-1/node-{leaf_nodes[1]}]-[vlan-{vlan}]",
                                                    "mac": mac,
                                                    "ifInstT": "ext-svi",
                                                    "nodeDn": f"topology/pod-1/node-{leaf_nodes[1]}",
                                                    "addr": leaf_ip_b,
                                                    "encap": f"vlan-{vlan}",
                                                    "mtu": mtu,
                                                    "status": "created"
                                                },
                                                "children": [
                                                    {
                                                        "l3extRsDynPathAtt": {
                                                            "attributes": {
                                                                "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/lifp-{l3out_name}_vpcIpv4/vlifp-[topology/pod-1/node-{leaf_nodes[1]}]-[vlan-{vlan}]/rsdynPathAtt-[{phys_dom_b}]",
                                                                "tDn": phys_dom_b,
                                                                "floatingAddr": floating_ip,
                                                                "encap": f"vlan-{vlan}",
                                                                "status": "created"
                                                            }
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    print(f"🚀 [1/3] Criando L3Out Floating IP Público sem rota ({l3out_name}) no Tenant ({tenant})...")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    try:
        r = requests.post(url, json=payload, headers=headers, cookies=cookies, verify=False, timeout=15)
        r.raise_for_status()
        print(f"✅ L3Out Floating Público sem rota '{l3out_name}' criado com sucesso!")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erro HTTP ao criar L3Out: {e}")
        try:
            print(f"Resposta APIC: {json.dumps(r.json(), indent=4)}")
        except Exception:
            print(f"Resposta texto: {r.text}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        sys.exit(1)

    tenant_l3out = cfg["TENANT_L3OUT_EXPORT"]
    tenant_extepg = cfg["TENANT_EXTEPG_EXPORT"]
    export_route_map = cfg["EXPORT_ROUTE_MAP"]

    # 2. Divulgar subnets públicas no L3Out do Tenant
    print(f"🚀 [2/3] Divulgando subnets públicas no L3Out do Tenant ({tenant_l3out} / {tenant_extepg})...")
    for idx, sub in enumerate(subnets):
        sub_name = f"{l3out_name}_exp_{idx+1}"
        sub_url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant}/out-{tenant_l3out}/instP-{tenant_extepg}/extsubnet-[{sub}].json"
        sub_payload = {
            "l3extSubnet": {
                "attributes": {
                    "dn": f"uni/tn-{tenant}/out-{tenant_l3out}/instP-{tenant_extepg}/extsubnet-[{sub}]",
                    "ip": sub,
                    "name": sub_name,
                    "scope": "export-rtctrl",
                    "aggregate": "",
                    "status": "created"
                },
                "children": [
                    {
                        "l3extRsSubnetToProfile": {
                            "attributes": {
                                "tnRtctrlProfileName": export_route_map,
                                "direction": "export",
                                "status": "created"
                            }
                        }
                    }
                ]
            }
        }
        try:
            r_sub = requests.post(sub_url, json=sub_payload, headers=headers, cookies=cookies, verify=False, timeout=15)
            r_sub.raise_for_status()
            print(f"  ✅ Subnet pública {sub} divulgada com sucesso em {tenant_l3out}.")
        except requests.RequestException as e:
            print(f"  ⚠️ Erro ao divulgar subnet pública {sub} em {tenant_l3out}: {e}")

    # 3. Divulgar subnets públicas no Common
    common_l3out = cfg["COMMON_L3OUT_EXPORT"]
    common_extepg = cfg["COMMON_EXTEPG_EXPORT"]

    print(f"🚀 [3/3] Divulgando subnets públicas no Tenant Common (out-{common_l3out} / {common_extepg})...")
    for idx, sub in enumerate(subnets):
        sub_name = f"{l3out_name}_comm_{idx+1}"
        common_url = f"https://{apic_ip}/api/node/mo/uni/tn-common/out-{common_l3out}/instP-{common_extepg}/extsubnet-[{sub}].json"
        common_payload = {
            "l3extSubnet": {
                "attributes": {
                    "dn": f"uni/tn-common/out-{common_l3out}/instP-{common_extepg}/extsubnet-[{sub}]",
                    "ip": sub,
                    "name": sub_name,
                    "scope": "export-rtctrl",
                    "aggregate": "",
                    "status": "created"
                }
            }
        }
        try:
            r_comm = requests.post(common_url, json=common_payload, headers=headers, cookies=cookies, verify=False, timeout=15)
            r_comm.raise_for_status()
            print(f"  ✅ Subnet pública {sub} divulgada com sucesso no Common.")
        except requests.RequestException as e:
            print(f"  ⚠️ Erro ao divulgar subnet pública {sub} no Common: {e}")

    print(f"🎉 Fluxo completo Floating IP Público sem rota '{l3out_name}' executado com sucesso!")

def main():
    args = parse_args()
    cfg = get_config(args)
    cookies = login(cfg["APIC_IP"], cfg["USERNAME"], cfg["PASSWORD"])
    criar_l3out_floating_public_no_route(cfg, cookies)

if __name__ == "__main__":
    main()
