import argparse
import configparser
import getpass
import logging
import os
import sys
import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

DEFAULT_APIC_URL = "https://172.30.104.5"


def carregar_config():
    config = configparser.ConfigParser()
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding="utf-8")
        if config.has_section("apic"):
            return {
                "url": config.get("apic", "url", fallback=DEFAULT_APIC_URL),
                "user": config.get("apic", "user", fallback=None),
                "password": config.get("apic", "password", fallback=None),
            }
    return {"url": DEFAULT_APIC_URL, "user": None, "password": None}


CFG = carregar_config()
APIC_URL = os.getenv("APIC_URL", CFG["url"] or DEFAULT_APIC_URL)

logger = logging.getLogger("verify-vpc")


def autenticar(apic_url, username, password, verbose=False):
    url = f"{apic_url}/api/aaaLogin.json"
    payload = {"aaaUser": {"attributes": {"name": username, "pwd": password}}}
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        response.raise_for_status()
        return response.cookies
    except requests.RequestException as e:
        logger.error(f"❌ Falha na autenticação: {e}")
        sys.exit(1)


def listar_rspathAtt(apic_url, tenant, ap, epg, cookies, verbose=False):
    url = f"{apic_url}/api/mo/uni/tn-{tenant}/ap-{ap}/epg-{epg}.json?query-target=children&target-filter=fvRsPathAtt"
    try:
        response = requests.get(url, cookies=cookies, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()
        imdata = data.get("imdata", [])
        if verbose:
            logger.info(f"🔍 EPG {tenant}/{ap}/{epg}: found {len(imdata)} path attachments")
        return imdata
    except requests.RequestException as e:
        logger.error(f"❌ Erro ao listar rspathAtt: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Verifica associações VPC ativas em EPGs")
    parser.add_argument("--tenant", required=True, help="Nome do tenant")
    parser.add_argument("--ap", required=True, help="Nome do Application Profile")
    parser.add_argument("--epg", action="append", default=[], help="Nome do EPG (repetir para vários)")
    parser.add_argument("--apic", default=APIC_URL, help="URL do APIC")
    parser.add_argument("--user", default=None, help="Usuário APIC")
    parser.add_argument("--pass", dest="password", default=None, help="Senha APIC")
    parser.add_argument("-v", "--verbose", action="store_true", help="Saída detalhada")
    args = parser.parse_args()

    setup_logging = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=setup_logging, format="%(asctime)s - %(levelname)s - %(message)s")

    usuario = args.user or input("Usuário APIC: ").strip()
    senha = args.password or getpass.getpass("Senha APIC: ")

    cookies = autenticar(args.apic, usuario, senha, verbose=args.verbose)

    if not args.epg:
        logger.error("❌ Informe pelo menos um --epg")
        sys.exit(1)

    for epg_name in args.epg:
        imdata = listar_rspathAtt(args.apic, args.tenant, args.ap, epg_name, cookies, verbose=args.verbose)
        if imdata:
            for item in imdata:
                attrs = item.get("fvRsPathAtt", {}).get("attributes", {})
                tdn = attrs.get("tDn", "N/A")
                encap = attrs.get("encap", "N/A")
                status = attrs.get("status", "N/A")
                logger.info(f"  🔗 EPG: {args.tenant}/{args.ap}/{epg_name}")
                logger.info(f"     TDN: {tdn}")
                logger.info(f"     Encap: {encap}")
                logger.info(f"     Status: {status}")
                logger.info("-" * 50)
        else:
            logger.info(f"ℹ️  Nenhuma associação VPC encontrada no EPG {args.tenant}/{args.ap}/{epg_name}")


if __name__ == "__main__":
    main()