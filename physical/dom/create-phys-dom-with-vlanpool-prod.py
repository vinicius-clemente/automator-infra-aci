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
            "DOM_NAME": r.get("DOM_NAME"),
            "POOL_NAME": r.get("POOL_NAME"),
            "AAEP_NAME": r.get("AAEP_NAME")
        }

def parse_args():
    parser = argparse.ArgumentParser(description="Criação de Physical Domain, Associação com VLAN Pool e Vinculação ao AAEP no Cisco ACI (via CLI ou CSV)")
    parser.add_argument("--arquivo", help="Caminho para arquivo CSV com variáveis")
    parser.add_argument("--dom-name", help="Nome do Physical Domain (ex: JASONX2-DOM)")
    parser.add_argument("--pool-name", help="Nome do VLAN Pool (ex: JASONX1-POOL)")
    parser.add_argument("--aaep-name", help="Nome do AAEP (ex: JASONX1-AAEP)")
    parser.add_argument("--apic", default=DEFAULT_APIC_IP, help="IP do APIC")
    parser.add_argument("--user", default=None, help="Usuário do APIC")
    parser.add_argument("--pass", dest="password", default=None, help="Senha do APIC")
    return parser.parse_args()

def get_config(args):
    if args.arquivo:
        print(f"📄 Lendo configurações do arquivo: {args.arquivo}")
        cfg = load_vars_from_csv(args.arquivo)
    else:
        if not args.dom_name:
            print("❌ Erro: O argumento --dom-name é obrigatório se não usar --arquivo.")
            sys.exit(1)
        cfg = {
            "DOM_NAME": args.dom_name,
            "POOL_NAME": args.pool_name,
            "AAEP_NAME": args.aaep_name
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

def criar_phys_dom_completo(cfg, cookies):
    apic_ip = cfg["APIC_IP"]
    dom_name = cfg["DOM_NAME"]
    pool_name = cfg["POOL_NAME"]
    aaep_name = cfg["AAEP_NAME"]

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    # 1. Criar o Physical Domain e associar ao VLAN Pool (se informado)
    url_dom = f"https://{apic_ip}/api/node/mo/uni/phys-{dom_name}.json"

    dom_children = []
    if pool_name:
        vlan_pool_dn = f"uni/infra/vlanns-[{pool_name}]-static"
        dom_children.append({
            "infraRsVlanNs": {
                "attributes": {
                    "tDn": vlan_pool_dn,
                    "status": "created"
                },
                "children": []
            }
        })

    payload_dom = {
        "physDomP": {
            "attributes": {
                "dn": f"uni/phys-{dom_name}",
                "name": dom_name,
                "rn": f"phys-{dom_name}",
                "status": "created"
            },
            "children": dom_children
        }
    }

    print(f"🚀 [1/2] Criando Physical Domain '{dom_name}' e associando ao VLAN Pool...")
    try:
        r = requests.post(url_dom, json=payload_dom, headers=headers, cookies=cookies, verify=False, timeout=15)
        r.raise_for_status()
        print(f"✅ Physical Domain '{dom_name}' criado com sucesso!")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erro HTTP ao criar Physical Domain: {e}")
        try:
            print(f"Resposta APIC: {json.dumps(r.json(), indent=4)}")
        except Exception:
            print(f"Resposta texto: {r.text}")
        sys.exit(1)

    # 2. Associar o Physical Domain ao AAEP (se informado)
    if aaep_name:
        url_aaep = f"https://{apic_ip}/api/node/mo/uni/infra/attentp-{aaep_name}/rsdomP-[uni/phys-{dom_name}].json"
        payload_aaep = {
            "infraRsDomP": {
                "attributes": {
                    "dn": f"uni/infra/attentp-{aaep_name}/rsdomP-[uni/phys-{dom_name}]",
                    "tDn": f"uni/phys-{dom_name}",
                    "status": "created,modified"
                },
                "children": []
            }
        }

        print(f"🚀 [2/2] Associando Physical Domain '{dom_name}' ao AAEP '{aaep_name}'...")
        try:
            r_aaep = requests.post(url_aaep, json=payload_aaep, headers=headers, cookies=cookies, verify=False, timeout=15)
            r_aaep.raise_for_status()
            print(f"✅ Physical Domain associado ao AAEP '{aaep_name}' com sucesso!")
        except requests.exceptions.HTTPError as e:
            print(f"❌ Erro HTTP ao associar ao AAEP: {e}")
            try:
                print(f"Resposta APIC: {json.dumps(r_aaep.json(), indent=4)}")
            except Exception:
                print(f"Resposta texto: {r_aaep.text}")
            sys.exit(1)

    print(f"🎉 Fluxo completo do Physical Domain '{dom_name}' executado com sucesso!")

def main():
    args = parse_args()
    cfg = get_config(args)
    cookies = login(cfg["APIC_IP"], cfg["USERNAME"], cfg["PASSWORD"])
    criar_phys_dom_completo(cfg, cookies)

if __name__ == "__main__":
    main()
