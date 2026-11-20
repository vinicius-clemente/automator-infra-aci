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
            "POOL_NAME": r.get("POOL_NAME"),
            "ALLOC_MODE": r.get("ALLOC_MODE", "static"),
            "VLAN_FROM": r.get("VLAN_FROM"),
            "VLAN_TO": r.get("VLAN_TO")
        }

def parse_args():
    parser = argparse.ArgumentParser(description="Criação de VLAN Pool e Bloco de VLANs no Cisco ACI (via CLI ou CSV)")
    parser.add_argument("--arquivo", help="Caminho para arquivo CSV com variáveis")
    parser.add_argument("--pool-name", help="Nome do VLAN Pool (ex: JASONX1-POOL)")
    parser.add_argument("--alloc-mode", default="static", help="Modo de alocação (static ou dynamic)")
    parser.add_argument("--vlan-from", help="VLAN inicial (ex: 11)")
    parser.add_argument("--vlan-to", help="VLAN final (ex: 11 ou 100)")
    parser.add_argument("--apic", default=DEFAULT_APIC_IP, help="IP do APIC")
    parser.add_argument("--user", default=None, help="Usuário do APIC")
    parser.add_argument("--pass", dest="password", default=None, help="Senha do APIC")
    return parser.parse_args()

def get_config(args):
    if args.arquivo:
        print(f"📄 Lendo configurações do arquivo: {args.arquivo}")
        cfg = load_vars_from_csv(args.arquivo)
    else:
        if not args.pool_name or not args.vlan_from or not args.vlan_to:
            print("❌ Erro: Os argumentos --pool-name, --vlan-from e --vlan-to são obrigatórios se não usar --arquivo.")
            sys.exit(1)
        cfg = {
            "POOL_NAME": args.pool_name,
            "ALLOC_MODE": args.alloc_mode,
            "VLAN_FROM": args.vlan_from,
            "VLAN_TO": args.vlan_to
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

def criar_vlan_pool(cfg, cookies):
    apic_ip = cfg["APIC_IP"]
    pool_name = cfg["POOL_NAME"]
    alloc_mode = cfg["ALLOC_MODE"]
    vlan_from = cfg["VLAN_FROM"]
    vlan_to = cfg["VLAN_TO"]

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    # 1. Criar VLAN Pool
    url_pool = f"https://{apic_ip}/api/node/mo/uni/infra/vlanns-[{pool_name}]-{alloc_mode}.json"
    payload_pool = {
        "fvnsVlanInstP": {
            "attributes": {
                "dn": f"uni/infra/vlanns-[{pool_name}]-{alloc_mode}",
                "name": pool_name,
                "allocMode": alloc_mode,
                "rn": f"vlanns-[{pool_name}]-{alloc_mode}",
                "status": "created"
            },
            "children": []
        }
    }

    print(f"🚀 Criando VLAN Pool '{pool_name}' ({alloc_mode})...")
    try:
        r = requests.post(url_pool, json=payload_pool, headers=headers, cookies=cookies, verify=False, timeout=15)
        r.raise_for_status()
        print(f"✅ VLAN Pool '{pool_name}' criado com sucesso!")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erro HTTP ao criar VLAN Pool: {e}")
        try:
            print(f"Resposta APIC: {json.dumps(r.json(), indent=4)}")
        except Exception:
            print(f"Resposta texto: {r.text}")
        sys.exit(1)

    # 2. Adicionar Bloco de VLANs (suportando allocMode: static, dynamic ou inherit)
    url_block = f"https://{apic_ip}/api/node/mo/uni/infra/vlanns-[{pool_name}]-{alloc_mode}/from-[vlan-{vlan_from}]-to-[vlan-{vlan_to}].json"
    payload_block = {
        "fvnsEncapBlk": {
            "attributes": {
                "dn": f"uni/infra/vlanns-[{pool_name}]-{alloc_mode}/from-[vlan-{vlan_from}]-to-[vlan-{vlan_to}]",
                "name": f"block_{vlan_from}_{vlan_to}",
                "from": f"vlan-{vlan_from}",
                "to": f"vlan-{vlan_to}",
                "allocMode": alloc_mode,
                "rn": f"from-[vlan-{vlan_from}]-to-[vlan-{vlan_to}]",
                "status": "created"
            },
            "children": []
        }
    }

    print(f"🚀 Adicionando bloco de VLANs (vlan-{vlan_from} até vlan-{vlan_to}) ao pool '{pool_name}'...")
    try:
        r_block = requests.post(url_block, json=payload_block, headers=headers, cookies=cookies, verify=False, timeout=15)
        r_block.raise_for_status()
        print(f"✅ Bloco de VLANs adicionado com sucesso ao pool '{pool_name}'!")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erro HTTP ao adicionar bloco de VLANs: {e}")
        try:
            print(f"Resposta APIC: {json.dumps(r_block.json(), indent=4)}")
        except Exception:
            print(f"Resposta texto: {r_block.text}")
        sys.exit(1)

def main():
    args = parse_args()
    cfg = get_config(args)
    cookies = login(cfg["APIC_IP"], cfg["USERNAME"], cfg["PASSWORD"])
    criar_vlan_pool(cfg, cookies)

if __name__ == "__main__":
    main()
