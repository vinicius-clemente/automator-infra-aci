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

# Caminho do arquivo de configuração ao lado deste script (opcional)
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")

# Valores padrão (fallback se não houver nada configurado)
DEFAULT_APIC_URL = "https://X.X.X.X"


def carregar_config():
    """Lê credenciais do config.ini, se existir."""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding="utf-8")
        if config.has_section("apic"):
            return {
                "url": config.get("apic", "url", fallback=DEFAULT_APIC_URL),
                "user": config.get("apic", "user", fallback=None),
                "password": config.get("apic", "password", fallback=None),
            }
    return {
        "url": DEFAULT_APIC_URL,
        "user": None,
        "password": None,
    }


CFG = carregar_config()
APIC_URL = os.getenv("APIC_URL", CFG["url"] or DEFAULT_APIC_URL)

logger = logging.getLogger("create-static-port")

# Cabeçalhos para evitar bloqueio por antivírus/firewall do APIC
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# Delay entre requisições para evitar rate limiting do antivírus do APIC
REQUEST_DELAY = 1.0


def request_delay():
    """Pequena pausa entre requisições para evitar bloqueio por antivírus."""
    time.sleep(REQUEST_DELAY)


def solicitar_credenciais(user_forcado=None, senha_forcada=None):
    """Pede usuário e senha na tela se não foram fornecidos por argumento."""
    usuario = user_forcado
    senha = senha_forcada

    if not usuario:
        usuario = input("Usuário APIC: ").strip()
        while not usuario:
            usuario = input("Usuário APIC (obrigatório): ").strip()

    if not senha:
        senha = getpass.getpass("Senha APIC: ")

    return usuario, senha


def setup_logging(verbose=False, log_file=None):
    level = logging.DEBUG if verbose else logging.INFO
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def autenticar(apic_url, username, password, verbose=False):
    url = f"{apic_url}/api/aaaLogin.json"
    payload = {
        "aaaUser": {
            "attributes": {
                "name": username,
                "pwd": password,
            }
        }
    }
    try:
        request_delay()
        response = requests.post(url, json=payload, headers=HEADERS, verify=False, timeout=10)
        response.raise_for_status()
        if verbose:
            logger.info("✅ Autenticação bem-sucedida.")
        return response.cookies
    except requests.RequestException as e:
        logger.error(f"❌ Falha na autenticação: {e}")
        sys.exit(1)


def associar_static_port(apic_url, tenant_name, ap_name, epg_name, tdn, encap, cookies, verbose=False):
    """Associa uma porta estática (static port) a um EPG."""
    url = f"{apic_url}/api/mo/uni/tn-{tenant_name}/ap-{ap_name}/epg-{epg_name}.json"
    payload = {
        "fvAEPg": {
            "attributes": {
                "name": epg_name,
            },
            "children": [
                {
                    "fvRsPathAtt": {
                        "attributes": {
                            "tDn": tdn,
                            "encap": encap,
                        }
                    }
                }
            ],
        }
    }
    try:
        request_delay()
        response = requests.post(url, json=payload, headers=HEADERS, cookies=cookies, verify=False, timeout=10)
    except requests.RequestException as e:
        if verbose:
            logger.error(f"❌ Erro de rede ao associar porta '{tdn}' ao EPG '{tenant_name}/{ap_name}/{epg_name}': {e}")
        return False, str(e), None

    if verbose:
        logger.info(f"🔗 Associando porta '{tdn}' (encap '{encap}') ao EPG '{tenant_name}/{ap_name}/{epg_name}'... Status: {response.status_code}")
        logger.debug(f"   Resposta: {response.text}")

    if response.status_code in (200, 201):
        if verbose:
            logger.info(f"✅ Porta '{tdn}' associada ao EPG '{tenant_name}/{ap_name}/{epg_name}' com sucesso.")
        return True, None, response.text
    else:
        if verbose:
            logger.error(f"❌ Erro ao associar porta '{tdn}' ao EPG '{tenant_name}/{ap_name}/{epg_name}': {response.text}")
        return False, response.text, response.text


def ler_arquivo_ports(caminho):
    """Lê arquivo texto com formato: tenant,app_profile,epg,tdn,encap (uma por linha).
    Retorna lista de dicionários."""
    itens = []
    if not os.path.exists(caminho):
        logger.error(f"❌ Arquivo não encontrado: {caminho}")
        sys.exit(1)

    with open(caminho, "r", encoding="utf-8") as f:
        for linha_num, linha in enumerate(f, start=1):
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            partes = [p.strip() for p in linha.split(",")]
            if len(partes) < 5:
                logger.warning(f"⚠️  Linha {linha_num} ignorada (formato inválido, esperado: tenant,app_profile,epg,tdn,encap): {linha}")
                continue
            tenant = partes[0]
            ap_name = partes[1]
            epg_name = partes[2]
            tdn = partes[3]
            encap = partes[4]
            if not tenant or not ap_name or not epg_name or not tdn:
                logger.warning(f"⚠️  Linha {linha_num} ignorada (campos obrigatórios vazios): {linha}")
                continue
            itens.append({
                "tenant": tenant,
                "ap": ap_name,
                "epg": epg_name,
                "tdn": tdn,
                "encap": encap,
            })

    if not itens:
        logger.error("❌ Nenhum item válido encontrado no arquivo.")
        sys.exit(1)

    return itens


def main():
    parser = argparse.ArgumentParser(
        description="Associa uma porta estática (static port) a um EPG no Cisco ACI."
    )
    parser.add_argument("--tenant", required=True, help="Nome do tenant")
    parser.add_argument("--ap", required=True, help="Nome do Application Profile")
    parser.add_argument("--epg", required=True, help="Nome do EPG")
    parser.add_argument("--tdn", required=True, help="Caminho da porta (ex: topology/pod-1/paths-101/pathep-[eth1/24])")
    parser.add_argument("--encap", required=True, help="Encap (ex: vlan-100 ou any)")
    parser.add_argument("--apic", default=APIC_URL, help="URL do APIC")
    parser.add_argument("--user", default=None, help="Usuário do APIC (se omitir, pedirá na tela)")
    parser.add_argument("--pass", dest="password", default=None, help="Senha do APIC (se omitir, pedirá na tela)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Saída detalhada")
    parser.add_argument("--log-file", help="Caminho para arquivo de log")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose, log_file=args.log_file)

    # Solicita credenciais na tela se não foram passadas por argumento
    usuario, senha = solicitar_credenciais(args.user, args.password)

    logger.info("=" * 70)
    logger.info("REPORT - ASSOCIAÇÃO DE PORTA ESTÁTICA A EPG")
    logger.info("=" * 70)
    logger.info(f"APIC   : {args.apic}")
    logger.info(f"Usuário: {usuario}")
    logger.info(f"Tenant : {args.tenant}")
    logger.info(f"AP     : {args.ap}")
    logger.info(f"EPG    : {args.epg}")
    logger.info(f"TDN    : {args.tdn}")
    logger.info(f"Encap  : {args.encap}")
    logger.info("-" * 70)

    cookies = autenticar(args.apic, usuario, senha, verbose=args.verbose)

    sucesso, erro, resposta = associar_static_port(
        args.apic, args.tenant, args.ap, args.epg, args.tdn, args.encap, cookies, verbose=args.verbose
    )
    if sucesso:
        logger.info("Status: ASSOCIADO com sucesso")
    else:
        logger.error(f"Status: FALHA - {erro}")
        sys.exit(1)

    logger.info("=" * 70)


if __name__ == "__main__":
    main()
