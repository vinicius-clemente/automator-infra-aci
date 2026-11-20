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
            "VIP_IP": r.get("VIP_IP"),
            # Subnets locais/privadas da SVI criadas no ExtEPG do L3Out (não são divulgadas nos L3Outs de exportação)
            "SUBNETS": [s.strip() for s in r.get("SUBNETS", "").split(";") if s.strip()],
            "ROUTE_SUBNET": r.get("ROUTE_SUBNET"),
            "ROUTE_SUBNET_NAME": r.get("ROUTE_SUBNET_NAME", "subnet_publica"),
            "NEXTHOP_IP": r.get("NEXTHOP_IP"),
            "ROUTER_ID_A": r.get("ROUTER_ID_A"),
            "ROUTER_ID_B": r.get("ROUTER_ID_B"),
            "PATH_EP_NAME": r.get("PATH_EP_NAME"),
            "MTU_VALUE": r.get("MTU_VALUE", "9216"),
            # Parâmetros de exportação / divulgação (apenas a rota pública será divulgada)
            "TENANT_L3OUT_EXPORT": r.get("TENANT_L3OUT_EXPORT", "DADOS-L3OUT"),
            "TENANT_EXTEPG_EXPORT": r.get("TENANT_EXTEPG_EXPORT", "Dados_L3Out_ExtEPG"),
            "EXPORT_ROUTE_MAP": r.get("EXPORT_ROUTE_MAP", "EXPORT_TO_TAMBORE"),
            "COMMON_L3OUT_EXPORT": r.get("COMMON_L3OUT_EXPORT", "ACI_INET_SHARED"),
            "COMMON_EXTEPG_EXPORT": r.get("COMMON_EXTEPG_EXPORT", "SHARED_INET_CONT")
        }

def parse_args():
    parser = argparse.ArgumentParser(description="Criação de L3Out SVI Privado com Rota Estática Pública (Cisco ACI)")
    parser.add_argument("--arquivo", help="Caminho para arquivo CSV com variáveis")
    parser.add_argument("--tenant", default="DADOS", help="Nome do Tenant")
    parser.add_argument("--l3out", help="Nome do L3Out")
    parser.add_argument("--vrf", default="VRF_DADOS", help="Nome da VRF")
    parser.add_argument("--l3dom", help="Nome do L3 Domain")
    parser.add_argument("--vlan", help="VLAN ID")
    parser.add_argument("--leaf-a", help="IP do Leaf A")
    parser.add_argument("--leaf-b", help="IP do Leaf B")
    parser.add_argument("--vip", help="IP VIP")
    parser.add_argument("--subnets", help="Subnets SVI privadas separadas por ponto e vírgula (;)")
    parser.add_argument("--route", help="Sub-rede da rota estática pública")
    parser.add_argument("--route-name", default="subnet_publica", help="Nome da sub-rede / rota")
    parser.add_argument("--nexthop", help="IP do Nexthop")
    parser.add_argument("--router-a", help="Router ID do Leaf A")
    parser.add_argument("--router-b", help="Router ID do Leaf B")
    parser.add_argument("--path", help="Nome do Path / VPC")
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
            "VIP_IP": args.vip,
            "SUBNETS": subnets,
            "ROUTE_SUBNET": args.route,
            "ROUTE_SUBNET_NAME": args.route_name,
            "NEXTHOP_IP": args.nexthop,
            "ROUTER_ID_A": args.router_a,
            "ROUTER_ID_B": args.router_b,
            "PATH_EP_NAME": args.path,
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

def criar_l3out_privado_public_route(cfg, cookies):
    apic_ip = cfg["APIC_IP"]
    tenant = cfg["TENANT_CREATE"]
    l3out_name = cfg["L3OUT_CREATE_NAME"]
    vrf = cfg["VRF_NAME"]
    l3dom = cfg["L3_DOMAIN_NAME"]
    vlan = cfg["INTERFACE_VLAN"]
    leaf_nodes = cfg["LEAF_NODES"]
    leaf_ip_a = cfg["LEAF_IP_A"]
    leaf_ip_b = cfg["LEAF_IP_B"]
    vip = cfg["VIP_IP"]
    subnets = cfg["SUBNETS"]
    route_subnet = cfg["ROUTE_SUBNET"]
    route_name = cfg["ROUTE_SUBNET_NAME"]
    nexthop = cfg["NEXTHOP_IP"]
    rtr_id_a = cfg["ROUTER_ID_A"]
    rtr_id_b = cfg["ROUTER_ID_B"]
    path_name = cfg["PATH_EP_NAME"]
    mtu = cfg["MTU_VALUE"]

    leaf_pair_dn = f"topology/pod-1/protpaths-{leaf_nodes[0]}-{leaf_nodes[1]}/pathep-[{path_name}]"
    url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant}/out-{l3out_name}.json"

    # Montar subnets do ExtEPG do próprio L3Out novo (divulgando a rota pública / subnets públicas, e NÃO a SVI privada)
    extepg_children = [
        {
            "fvRsProv": {"attributes": {"tnVzBrCPName": "TRANSIT_ROUTING_ALL", "status": "created,modified"}},
        },
        {
            "fvRsCons": {"attributes": {"tnVzBrCPName": "TRANSIT_ROUTING_ALL", "status": "created,modified"}},
        }
    ]
    
    subnets_para_extepg = []
    if route_subnet:
        subnets_para_extepg.append(route_subnet)
    
    for idx, sub in enumerate(subnets_para_extepg):
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

    # Montar nós e rotas estáticas públicas se houver nexthop / route_subnet
    node_a_children = []
    node_b_children = []
    
    if route_subnet and nexthop:
        route_payload = {
            "ipRouteP": {
                "attributes": {"ip": route_subnet, "name": route_name, "descr": route_name, "status": "created"},
                "children": [
                    {
                        "ipNexthopP": {
                            "attributes": {"nhAddr": nexthop, "status": "created"}
                        }
                    }
                ]
            }
        }
        node_a_children.append(route_payload)
        node_b_children.append(route_payload)

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
                                    },
                                    "children": node_a_children
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
                                    },
                                    "children": node_b_children
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
                                            "l3extRsPathL3OutAtt": {
                                                "attributes": {
                                                    "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/lifp-{l3out_name}_vpcIpv4/rspathL3OutAtt-[{leaf_pair_dn}]",
                                                    "tDn": leaf_pair_dn,
                                                    "ifInstT": "ext-svi",
                                                    "mtu": mtu,
                                                    "encap": f"vlan-{vlan}",
                                                    "status": "created"
                                                },
                                                "children": [
                                                    {
                                                        "l3extMember": {
                                                            "attributes": {
                                                                "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/lifp-{l3out_name}_vpcIpv4/rspathL3OutAtt-[{leaf_pair_dn}]/mem-A",
                                                                "addr": leaf_ip_a,
                                                                "status": "created"
                                                            },
                                                            "children": [
                                                                {
                                                                    "l3extIp": {
                                                                        "attributes": {
                                                                            "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/lifp-{l3out_name}_vpcIpv4/rspathL3OutAtt-[{leaf_pair_dn}]/mem-A/addr-[{vip}]",
                                                                            "addr": vip,
                                                                            "status": "created"
                                                                        }
                                                                    }
                                                                }
                                                            ]
                                                        }
                                                    },
                                                    {
                                                        "l3extMember": {
                                                            "attributes": {
                                                                "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/lifp-{l3out_name}_vpcIpv4/rspathL3OutAtt-[{leaf_pair_dn}]/mem-B",
                                                                "side": "B",
                                                                "addr": leaf_ip_b,
                                                                "status": "created"
                                                            },
                                                            "children": [
                                                                {
                                                                    "l3extIp": {
                                                                        "attributes": {
                                                                            "dn": f"uni/tn-{tenant}/out-{l3out_name}/lnodep-{l3out_name}_nodeProfile/lifp-{l3out_name}_vpcIpv4/rspathL3OutAtt-[{leaf_pair_dn}]/mem-B/addr-[{vip}]",
                                                                            "addr": vip,
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
            ]
        }
    }

    print(f"🚀 [1/3] Criando L3Out SVI Privado com Rota Pública ({l3out_name}) no Tenant ({tenant})...")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    try:
        r = requests.post(url, json=payload, headers=headers, cookies=cookies, verify=False, timeout=15)
        r.raise_for_status()
        print(f"✅ L3Out '{l3out_name}' criado com sucesso!")
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

    # 2. Divulgar APENAS a rota estática pública no L3Out principal do Tenant (ex: DADOS-L3OUT)
    print(f"🚀 [2/3] Divulgando APENAS a rota estática pública no L3Out do Tenant ({tenant_l3out} / {tenant_extepg})...")
    if route_subnet:
        route_sub_url = f"https://{apic_ip}/api/node/mo/uni/tn-{tenant}/out-{tenant_l3out}/instP-{tenant_extepg}/extsubnet-[{route_subnet}].json"
        route_sub_payload = {
            "l3extSubnet": {
                "attributes": {
                    "dn": f"uni/tn-{tenant}/out-{tenant_l3out}/instP-{tenant_extepg}/extsubnet-[{route_subnet}]",
                    "ip": route_subnet,
                    "name": f"{route_name}_exp",
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
            r_rsub = requests.post(route_sub_url, json=route_sub_payload, headers=headers, cookies=cookies, verify=False, timeout=15)
            r_rsub.raise_for_status()
            print(f"  ✅ Rota Pública {route_subnet} divulgada com sucesso em {tenant_l3out}.")
        except requests.RequestException as e:
            print(f"  ⚠️ Erro ao divulgar rota pública {route_subnet} em {tenant_l3out}: {e}")
    else:
        print("  ℹ️ Nenhuma rota estática pública configurada para divulgar no Tenant.")

    # 3. Divulgar APENAS a rota estática pública no L3Out do Common (ex: out-ACI_INET_SHARED / SHARED_INET_CONT)
    common_l3out = cfg["COMMON_L3OUT_EXPORT"]
    common_extepg = cfg["COMMON_EXTEPG_EXPORT"]

    print(f"🚀 [3/3] Divulgando APENAS a rota estática pública no Tenant Common (out-{common_l3out} / {common_extepg})...")
    if route_subnet:
        common_url = f"https://{apic_ip}/api/node/mo/uni/tn-common/out-{common_l3out}/instP-{common_extepg}/extsubnet-[{route_subnet}].json"
        common_payload = {
            "l3extSubnet": {
                "attributes": {
                    "dn": f"uni/tn-common/out-{common_l3out}/instP-{common_extepg}/extsubnet-[{route_subnet}]",
                    "ip": route_subnet,
                    "name": f"{route_name}_comm",
                    "scope": "export-rtctrl",
                    "aggregate": "",
                    "status": "created"
                }
            }
        }
        try:
            r_comm = requests.post(common_url, json=common_payload, headers=headers, cookies=cookies, verify=False, timeout=15)
            r_comm.raise_for_status()
            print(f"  ✅ Rota Pública {route_subnet} divulgada com sucesso no Common.")
        except requests.RequestException as e:
            print(f"  ⚠️ Erro ao divulgar rota pública {route_subnet} no Common: {e}")
    else:
        print("  ℹ️ Nenhuma rota estática pública configurada para divulgar no Common.")

    print(f"🎉 Fluxo completo do L3Out Privado com Rota Pública '{l3out_name}' executado com sucesso!")

def main():
    args = parse_args()
    cfg = get_config(args)
    cookies = login(cfg["APIC_IP"], cfg["USERNAME"], cfg["PASSWORD"])
    criar_l3out_privado_public_route(cfg, cookies)

if __name__ == "__main__":
    main()
