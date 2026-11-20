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
            "ALLOC_MODE": r.get("ALLOC_MODE", "static")
        }

def parse_args():
    parser = argparse.ArgumentParser(description="Deleção de VLAN Pool no Cisco ACI (via CLI ou CSV)")
    parser.add_argument("--arquivo", help="Caminho para arquivo CSV com variáveis")
    parser.add_argument("--pool-name", help="Nome do VLAN Pool a ser deletado (ex: JASONX1-POOL)")
    parser.add_argument("--alloc-mode", default="static", help="Modo de alocação (static ou dynamic)")
    parser.add_argument("--apic", default=DEFAULT_APIC_IP, help="IP do APIC")
    parser.add_argument("--user", default=None, help="Usuário do APIC")
    parser.add_argument("--pass", dest="password", default=None, help="Senha do APIC")
    return parser.parse_args()

def get_config(args):
    if args.arquivo:
        print(f"📄 Lendo configurações do arquivo: {args.arquivo}")
        cfg = load_vars_from_csv(args.arquivo)
    else:
        if not args.pool_name:
            print("❌ Erro: O argumento --pool-name é obrigatório se não usar --arquivo.")
            sys.exit(1)
        cfg = {
            "POOL_NAME": args.pool_name,
            "ALLOC_MODE": args.alloc_mode
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

def deletar_vlan_pool(cfg, cookies):
    apic_ip = cfg["APIC_IP"]
    pool_name = cfg["POOL_NAME"]
    alloc_mode = cfg["ALLOC_MODE"]

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    url = f"https://{apic_ip}/api/node/mo/uni/infra/vlanns-[{pool_name}]-{alloc_mode}.json"
    
    payload = {
        "fvnsVlanInstP": {
            "attributes": {
                "dn": f"uni/infra/vlanns-[{pool_name}]-{alloc_mode}",
                "status": "deleted"
            }
        }
    }

    print(f"🗑️ Deletando VLAN Pool '{pool_name}' ({alloc_mode})...")
    try:
        r = requests.post(url, json=payload, headers=headers, cookies=cookies, verify=False, timeout=15)
        r.raise_for_status()
        print(f"✅ VLAN Pool '{pool_name}' deletado com sucesso!")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erro HTTP ao deletar VLAN Pool: {e}")
        try:
            print(f"Resposta APIC: {json.dumps(r.json(), indent=4)}")
        except Exception:
            print(f"Resposta texto: {r.text}")
        sys.exit(1)

def main():
    args = parse_args()
    cfg = get_config(args)
    cookies = login(cfg["APIC_IP"], cfg["USERNAME"], cfg["PASSWORD"])
    deletar_vlan_pool(cfg, cookies)

if __name__ == "__main__":
    main()
