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

logger = logging.getLogger("delete-bds")


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
            logger.info(f"🔎 Verificando '{tenant_name}/{bd_name}' -> {status}")
        return len(imdata) > 0
    except requests.RequestException as e:
        logger.warning(f"⚠️  Erro ao verificar existência de '{tenant_name}/{bd_name}': {e}")
        return False


def deletar_bridge_domain(apic_url, tenant_name, bd_name, cookies, verbose=False):
    url = f"{apic_url}/api/mo/uni/tn-{tenant_name}/BD-{bd_name}.json"
    try:
        request_delay()
        response = requests.delete(url, cookies=cookies, headers=HEADERS, verify=False, timeout=10)
    except requests.RequestException as e:
        if verbose:
            logger.error(f"❌ Erro de rede ao deletar BD '{tenant_name}/{bd_name}': {e}")
        return False, str(e), None

    if verbose:
        logger.info(f"🗑️  Deletando '{tenant_name}/{bd_name}'... Status: {response.status_code}")
        logger.debug(f"   Resposta: {response.text}")

    if response.status_code in (200, 201, 204):
        if verbose:
            logger.info(f"✅ BD '{tenant_name}/{bd_name}' deletado com sucesso.")
        return True, None, response.text
    else:
        if verbose:
            logger.error(f"❌ Erro ao deletar BD '{tenant_name}/{bd_name}': {response.text}")
        return False, response.text, response.text


def ler_arquivo_bds(caminho):
    """Lê arquivo texto com formato: tenant,bd ou tenant,vrf,bd (uma por linha).
    Retorna lista de dicionários com tenant e bd."""
    bds = []
    if not os.path.exists(caminho):
        logger.error(f"❌ Arquivo não encontrado: {caminho}")
        sys.exit(1)

    with open(caminho, "r", encoding="utf-8") as f:
        for linha_num, linha in enumerate(f, start=1):
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            partes = [p.strip() for p in linha.split(",")]
            if len(partes) < 2:
                logger.warning(f"⚠️  Linha {linha_num} ignorada (formato inválido): {linha}")
                continue
            tenant = partes[0]
            # Se tiver 3 colunas (tenant,vrf,bd), pega o BD da última coluna
            # Se tiver 2 colunas (tenant,bd), pega a segunda
            bd = partes[-1]
            if not tenant or not bd:
                logger.warning(f"⚠️  Linha {linha_num} ignorada (campos vazios): {linha}")
                continue
            bds.append({"tenant": tenant, "bd": bd})

    if not bds:
        logger.error("❌ Nenhum BD válido encontrado no arquivo.")
        sys.exit(1)

    return bds


def main():
    parser = argparse.ArgumentParser(
        description="Deleta Bridge Domains no Cisco ACI com relatório."
    )
    parser.add_argument("--arquivo", default="delete-bds.txt", help="Arquivo texto com lista de BDs (padrão: delete-bds.txt)")
    parser.add_argument("--tenant", help="Nome do tenant (modo simples, sem --arquivo)")
    parser.add_argument("--bd", action="append", help="Nome do Bridge Domain (modo simples, repita para vários)")
    parser.add_argument("--apic", default=APIC_URL, help="URL do APIC")
    parser.add_argument("--user", default=None, help="Usuário do APIC (se omitir, pedirá na tela)")
    parser.add_argument("--pass", dest="password", default=None, help="Senha do APIC (se omitir, pedirá na tela)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Saída detalhada")
    parser.add_argument("--log-file", help="Caminho para arquivo de log")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose, log_file=args.log_file)

    # Solicita credenciais na tela se não foram passadas por argumento
    usuario, senha = solicitar_credenciais(args.user, args.password)

    # Define a lista de BDs a deletar
    bds_para_deletar = []
    modo_arquivo = False

    # Tenta usar o arquivo especificado ou o padrão delete-bds.txt
    arquivo_para_usar = args.arquivo
    if not os.path.exists(arquivo_para_usar):
        # Se o padrão não existe, tenta ao lado do script
        caminho_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), arquivo_para_usar)
        if os.path.exists(caminho_script):
            arquivo_para_usar = caminho_script
        else:
            arquivo_para_usar = None

    if arquivo_para_usar:
        bds_para_deletar = ler_arquivo_bds(arquivo_para_usar)
        logger.info(f"📄 Lidos {len(bds_para_deletar)} BDs do arquivo: {arquivo_para_usar}")
        modo_arquivo = True
    else:
        if not args.tenant or not args.bd:
            logger.error("❌ Informe --arquivo OU use --tenant e pelo menos um --bd")
            sys.exit(1)
        for bd in args.bd:
            bds_para_deletar.append({"tenant": args.tenant, "bd": bd})

    logger.info("=" * 70)
    logger.info("REPORT - EXCLUSÃO DE BRIDGE DOMAINS")
    logger.info("=" * 70)
    logger.info(f"APIC   : {args.apic}")
    logger.info(f"Usuário: {usuario}")
    logger.info(f"Qtd BD : {len(bds_para_deletar)}")
    logger.info("-" * 70)

    cookies = autenticar(args.apic, usuario, senha, verbose=args.verbose)

    deletados = []
    pulados = []
    falhas = []
    tenants_processados = set()

    for item in bds_para_deletar:
        tenant = item["tenant"]
        bd = item["bd"]

        if tenant not in tenants_processados:
            tenants_processados.add(tenant)

        if not bridge_domain_existe(args.apic, tenant, bd, cookies, verbose=args.verbose):
            logger.warning(f"⚠️  '{tenant}/{bd}' não existe. Pulando.")
            pulados.append(f"{tenant}/{bd}")
            continue

        sucesso, erro, resposta = deletar_bridge_domain(
            args.apic, tenant, bd, cookies, verbose=args.verbose
        )
        if sucesso:
            logger.info(f"✅ '{tenant}/{bd}' deletado com sucesso.")
            deletados.append(f"{tenant}/{bd}")
        else:
            logger.error(f"❌ '{tenant}/{bd}' falhou: {erro}")
            falhas.append((f"{tenant}/{bd}", erro))

    logger.info("-" * 70)
    logger.info("RESUMO")
    logger.info("-" * 70)
    logger.info(f"Tenants processados: {len(tenants_processados)}")
    for t in sorted(tenants_processados):
        logger.info(f"  📦 {t}")
    logger.info(f"Deletados : {len(deletados)}")
    for b in deletados:
        logger.info(f"  🗑️  {b}")
    logger.info(f"Pulados   : {len(pulados)} (não existiam)")
    for b in pulados:
        logger.info(f"  ⚠️  {b}")
    logger.info(f"Falhas    : {len(falhas)}")
    for b, e in falhas:
        logger.info(f"  ❌ {b} -> {e}")
    logger.info("=" * 70)

    if falhas:
        sys.exit(1)


if __name__ == "__main__":
    main()
