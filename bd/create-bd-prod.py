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

logger = logging.getLogger("create-bd")


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


def authenticate(apic_url, username, password, verbose=False):
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


def bridge_domain_existe(apic_url, tenant_name, bd_name, cookies, verbose=False):
    """Retorna True se o BD já existir no tenant."""
    url = (
        f"{apic_url}/api/node/mo/uni/tn-{tenant_name}/BD-{bd_name}.json"
        f"?query-target=self"
    )
    try:
        request_delay()
        response = requests.get(url, cookies=cookies, headers=HEADERS, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()
        imdata = data.get("imdata", [])
        if verbose:
            status = "encontrado" if imdata else "não encontrado"
            logger.info(f"🔎 Verificando existência de '{bd_name}' -> {status}")
        return len(imdata) > 0
    except requests.RequestException as e:
        logger.warning(f"⚠️  Erro ao verificar existência de '{bd_name}': {e}")
        return False


def criar_bridge_domain(apic_url, tenant_name, bd_name, vrf_name, cookies, verbose=False):
    url = f"{apic_url}/api/mo/uni/tn-{tenant_name}/BD-{bd_name}.json"
    payload = {
        "fvBD": {
            "attributes": {
                "name": bd_name,
                "arpFlood": "true",
                "unkMacUcastAct": "flood",
                "multiDstPktAct": "bd-flood",
            },
            "children": [
                {
                    "fvRsCtx": {
                        "attributes": {
                            "tnFvCtxName": vrf_name,
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
            logger.error(f"❌ Erro de rede ao criar BD '{bd_name}': {e}")
        return False, str(e)

    if verbose:
        logger.info(f"📡 Criando Bridge Domain '{bd_name}'...")
        logger.info(f"   Status Code: {response.status_code}")
        logger.debug(f"   Resposta: {response.text}")

    if response.status_code in (200, 201):
        if verbose:
            logger.info(
                f"✅ BD '{bd_name}' criado com sucesso no Tenant '{tenant_name}' "
                f"(VRF '{vrf_name}')."
            )
        return True, None
    else:
        if verbose:
            logger.error(f"❌ Erro ao criar BD '{bd_name}': {response.text}")
        return False, response.text


def main():
    parser = argparse.ArgumentParser(
        description="Cria um Bridge Domain no Cisco ACI."
    )
    parser.add_argument("--tenant", required=True, help="Nome do tenant")
    parser.add_argument("--bd", required=True, help="Nome do Bridge Domain")
    parser.add_argument("--vrf", required=True, help="Nome da VRF associada")
    parser.add_argument("--apic", default=APIC_URL, help="URL do APIC")
    parser.add_argument("--user", default=None, help="Usuário do APIC (se omitir, pedirá na tela)")
    parser.add_argument("--pass", dest="password", default=None, help="Senha do APIC (se omitir, pedirá na tela)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Saída detalhada")
    parser.add_argument("--log-file", help="Caminho para arquivo de log")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose, log_file=args.log_file)

    # Solicita credenciais na tela se não foram passadas por argumento
    usuario, senha = solicitar_credenciais(args.user, args.password)

    logger.info("=" * 60)
    logger.info("REPORT - CRIAÇÃO DE BRIDGE DOMAIN")
    logger.info("=" * 60)
    logger.info(f"Tenant : {args.tenant}")
    logger.info(f"BD     : {args.bd}")
    logger.info(f"VRF    : {args.vrf}")
    logger.info(f"APIC   : {args.apic}")
    logger.info(f"Usuário: {usuario}")
    logger.info("-" * 60)

    cookies = authenticate(args.apic, usuario, senha, verbose=args.verbose)

    if bridge_domain_existe(args.apic, args.tenant, args.bd, cookies, verbose=args.verbose):
        logger.warning(f"⚠️  BD '{args.bd}' já existe no tenant '{args.tenant}'. Pulando criação.")
        logger.info("Status: PULADO (já existe)")
    else:
        sucesso, erro = criar_bridge_domain(
            args.apic, args.tenant, args.bd, args.vrf, cookies, verbose=args.verbose
        )
        if sucesso:
            logger.info("Status: CRIADO com sucesso")
        else:
            logger.error(f"Status: FALHA - {erro}")
            sys.exit(1)

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
