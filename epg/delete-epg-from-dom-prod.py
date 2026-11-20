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

logger = logging.getLogger("delete-epg-dom")

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


def desassociar_epg_dom(apic_url, tenant_name, ap_name, epg_name, dom_name, cookies, verbose=False):
    """Remove a associação de um EPG a um Physical Domain (apenas desassocia, sem validações)."""
    dn = f"uni/tn-{tenant_name}/ap-{ap_name}/epg-{epg_name}/rsdomAtt-[uni/phys-{dom_name}]"
    url = f"{apic_url}/api/mo/{dn}.json"
    try:
        request_delay()
        response = requests.delete(url, cookies=cookies, headers=HEADERS, verify=False, timeout=10)
    except requests.RequestException as e:
        if verbose:
            logger.error(f"❌ Erro de rede ao desassociar EPG '{tenant_name}/{ap_name}/{epg_name}' do Dom '{dom_name}': {e}")
        return False, str(e), None

    if verbose:
        logger.info(f"🔗 Desassociando EPG '{tenant_name}/{ap_name}/{epg_name}' do Physical Domain '{dom_name}'... Status: {response.status_code}")
        logger.debug(f"   Resposta: {response.text}")

    if response.status_code in (200, 201, 204):
        if verbose:
            logger.info(f"✅ Associação EPG '{tenant_name}/{ap_name}/{epg_name}' <-> Dom '{dom_name}' removida com sucesso.")
        return True, None, response.text
    else:
        if verbose:
            logger.error(f"❌ Erro ao desassociar EPG '{tenant_name}/{ap_name}/{epg_name}' do Dom '{dom_name}': {response.text}")
        return False, response.text, response.text


def ler_arquivo_epgs_doms(caminho):
    """Lê arquivo texto com formato: tenant,app_profile,epg,phys_domain (uma por linha)."""
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
            if len(partes) < 4:
                logger.warning(f"⚠️  Linha {linha_num} ignorada (formato inválido): {linha}")
                continue
            tenant = partes[0]
            ap_name = partes[1]
            epg_name = partes[2]
            dom_name = partes[3]
            if not tenant or not ap_name or not epg_name or not dom_name:
                logger.warning(f"⚠️  Linha {linha_num} ignorada (campos vazios): {linha}")
                continue
            itens.append({
                "tenant": tenant,
                "ap": ap_name,
                "epg": epg_name,
                "dom": dom_name,
            })

    if not itens:
        logger.error("❌ Nenhum item válido encontrado no arquivo.")
        sys.exit(1)

    return itens


def main():
    parser = argparse.ArgumentParser(
        description="Desassocia um EPG existente de um Physical Domain existente no Cisco ACI."
    )
    parser.add_argument("--arquivo", default="delete-epgs-doms.txt", help="Arquivo texto com lista (padrão: delete-epgs-doms.txt)")
    parser.add_argument("--tenant", help="Nome do tenant (modo simples)")
    parser.add_argument("--ap", help="Nome do Application Profile (modo simples)")
    parser.add_argument("--epg", action="append", help="Nome do EPG (modo simples, repita para vários)")
    parser.add_argument("--dom", action="append", help="Nome do Physical Domain (modo simples, repita para vários)")
    parser.add_argument("--apic", default=APIC_URL, help="URL do APIC")
    parser.add_argument("--user", default=None, help="Usuário do APIC (se omitir, pedirá na tela)")
    parser.add_argument("--pass", dest="password", default=None, help="Senha do APIC (se omitir, pedirá na tela)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Saída detalhada")
    parser.add_argument("--log-file", help="Caminho para arquivo de log")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose, log_file=args.log_file)

    # Solicita credenciais na tela se não foram passadas por argumento
    usuario, senha = solicitar_credenciais(args.user, args.password)

    # Define a lista de EPG/Dom a processar
    itens = []

    # Prioridade: se passou --tenant na linha de comando, usa modo simples
    if args.tenant:
        if not args.ap:
            logger.error("❌ Informe --ap quando usar --tenant")
            sys.exit(1)
        if not args.epg:
            logger.error("❌ Informe pelo menos um --epg quando usar --tenant")
            sys.exit(1)
        if not args.dom:
            logger.error("❌ Informe pelo menos um --dom quando usar --tenant")
            sys.exit(1)

        if len(args.epg) != len(args.dom):
            logger.error("❌ A quantidade de --epg deve ser igual à quantidade de --dom")
            sys.exit(1)

        for epg_name, dom_name in zip(args.epg, args.dom):
            itens.append({
                "tenant": args.tenant,
                "ap": args.ap,
                "epg": epg_name,
                "dom": dom_name,
            })
        logger.info(f"🎯 Modo linha de comando: {len(itens)} desassociação(ões) no AP '{args.ap}' do Tenant '{args.tenant}'")
    else:
        # Tenta usar arquivo padrão delete-epgs-doms.txt
        arquivo_para_usar = args.arquivo
        if not os.path.exists(arquivo_para_usar):
            caminho_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), arquivo_para_usar)
            if os.path.exists(caminho_script):
                arquivo_para_usar = caminho_script
            else:
                arquivo_para_usar = None

        if arquivo_para_usar:
            itens = ler_arquivo_epgs_doms(arquivo_para_usar)
            logger.info(f"📄 Lidos {len(itens)} itens do arquivo: {arquivo_para_usar}")
        else:
            logger.error("❌ Informe --arquivo OU use --tenant --ap --epg --dom")
            sys.exit(1)

    logger.info("=" * 70)
    logger.info("REPORT - DESASSOCIAÇÃO DE EPGs DE PHYSICAL DOMAINS")
    logger.info("=" * 70)
    logger.info(f"APIC   : {args.apic}")
    logger.info(f"Usuário: {usuario}")
    logger.info(f"Qtd itens: {len(itens)}")
    logger.info("-" * 70)

    cookies = autenticar(args.apic, usuario, senha, verbose=args.verbose)

    desassociados = []
    falhas = []

    for item in itens:
        tenant = item["tenant"]
        ap_name = item["ap"]
        epg_name = item["epg"]
        dom_name = item["dom"]

        sucesso, erro, resposta = desassociar_epg_dom(
            args.apic, tenant, ap_name, epg_name, dom_name, cookies, verbose=args.verbose
        )
        if sucesso:
            logger.info(f"✅ '{tenant}/{ap_name}/{epg_name}' desassociado do Dom '{dom_name}'.")
            desassociados.append(f"{tenant}/{ap_name}/{epg_name} <-> {dom_name}")
        else:
            logger.error(f"❌ '{tenant}/{ap_name}/{epg_name}' <-> {dom_name} falhou: {erro}")
            falhas.append(f"{tenant}/{ap_name}/{epg_name} <-> {dom_name} -> {erro}")

    logger.info("-" * 70)
    logger.info("RESUMO")
    logger.info("-" * 70)
    logger.info(f"Associações removidas : {len(desassociados)}")
    for d in desassociados:
        logger.info(f"  🗑️  {d}")
    logger.info(f"Falhas                : {len(falhas)}")
    for f in falhas:
        logger.info(f"  ❌ {f}")
    logger.info("=" * 70)

    if falhas:
        sys.exit(1)


if __name__ == "__main__":
    main()
