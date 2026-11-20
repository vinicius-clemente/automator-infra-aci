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

logger = logging.getLogger("delete-tenant-vrf")


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


def tenant_existe(apic_url, tenant_name, cookies, verbose=False):
    """Retorna True se o Tenant já existir."""
    url = f"{apic_url}/api/node/mo/uni/tn-{tenant_name}.json?query-target=self"
    try:
        request_delay()
        response = requests.get(url, cookies=cookies, headers=HEADERS, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()
        imdata = data.get("imdata", [])
        if verbose:
            status = "encontrado" if imdata else "não encontrado"
            logger.info(f"🔎 Verificando Tenant '{tenant_name}' -> {status}")
        return len(imdata) > 0
    except requests.RequestException as e:
        logger.warning(f"⚠️  Erro ao verificar existência do Tenant '{tenant_name}': {e}")
        return False


def vrf_existe(apic_url, tenant_name, vrf_name, cookies, verbose=False):
    """Retorna True se a VRF já existir no tenant."""
    url = (
        f"{apic_url}/api/node/mo/uni/tn-{tenant_name}/ctx-{vrf_name}.json"
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
            logger.info(f"🔎 Verificando VRF '{tenant_name}/{vrf_name}' -> {status}")
        return len(imdata) > 0
    except requests.RequestException as e:
        logger.warning(f"⚠️  Erro ao verificar existência da VRF '{tenant_name}/{vrf_name}': {e}")
        return False


def deletar_vrf(apic_url, tenant_name, vrf_name, cookies, verbose=False):
    url = f"{apic_url}/api/mo/uni/tn-{tenant_name}/ctx-{vrf_name}.json"
    try:
        request_delay()
        response = requests.delete(url, cookies=cookies, headers=HEADERS, verify=False, timeout=10)
    except requests.RequestException as e:
        logger.error(f"❌ Erro de rede ao deletar VRF '{tenant_name}/{vrf_name}': {e}")
        return False, str(e), None

    if verbose:
        logger.info(f"🗑️  Deletando VRF '{tenant_name}/{vrf_name}'... Status: {response.status_code}")
        logger.debug(f"   Resposta: {response.text}")

    if response.status_code in (200, 201, 204):
        if verbose:
            logger.info(f"✅ VRF '{tenant_name}/{vrf_name}' deletada com sucesso.")
        return True, None, response.text
    else:
        if verbose:
            logger.error(f"❌ Erro ao deletar VRF '{tenant_name}/{vrf_name}': {response.text}")
        return False, response.text, response.text


def deletar_tenant(apic_url, tenant_name, cookies, verbose=False):
    url = f"{apic_url}/api/mo/uni/tn-{tenant_name}.json"
    try:
        request_delay()
        response = requests.delete(url, cookies=cookies, headers=HEADERS, verify=False, timeout=10)
    except requests.RequestException as e:
        logger.error(f"❌ Erro de rede ao deletar Tenant '{tenant_name}': {e}")
        return False, str(e), None

    if verbose:
        logger.info(f"🗑️  Deletando Tenant '{tenant_name}'... Status: {response.status_code}")
        logger.debug(f"   Resposta: {response.text}")

    if response.status_code in (200, 201, 204):
        if verbose:
            logger.info(f"✅ Tenant '{tenant_name}' deletado com sucesso.")
        return True, None, response.text
    else:
        if verbose:
            logger.error(f"❌ Erro ao deletar Tenant '{tenant_name}': {response.text}")
        return False, response.text, response.text


def ler_arquivo_tenants_vrfs(caminho):
    """Lê arquivo texto com formato: tenant,vrf (uma por linha).
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
            if len(partes) < 1:
                logger.warning(f"⚠️  Linha {linha_num} ignorada (formato inválido): {linha}")
                continue
            tenant = partes[0]
            vrf = partes[1] if len(partes) > 1 else None
            if not tenant:
                logger.warning(f"⚠️  Linha {linha_num} ignorada (tenant vazio): {linha}")
                continue
            itens.append({"tenant": tenant, "vrf": vrf})

    if not itens:
        logger.error("❌ Nenhum Tenant válido encontrado no arquivo.")
        sys.exit(1)

    return itens


def main():
    parser = argparse.ArgumentParser(
        description="Deleta VRFs e Tenants no Cisco ACI com relatório."
    )
    parser.add_argument("--arquivo", default="delete-tenant-vrf.txt", help="Arquivo texto com lista (padrão: delete-tenant-vrf.txt)")
    parser.add_argument("--tenant", help="Nome do tenant (modo simples, sem --arquivo)")
    parser.add_argument("--vrf", help="Nome da VRF (modo simples, sem --arquivo)")
    parser.add_argument("--apic", default=APIC_URL, help="URL do APIC")
    parser.add_argument("--user", default=None, help="Usuário do APIC (se omitir, pedirá na tela)")
    parser.add_argument("--pass", dest="password", default=None, help="Senha do APIC (se omitir, pedirá na tela)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Saída detalhada")
    parser.add_argument("--log-file", help="Caminho para arquivo de log")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose, log_file=args.log_file)

    # Solicita credenciais na tela se não foram passadas por argumento
    usuario, senha = solicitar_credenciais(args.user, args.password)

    # Define a lista de Tenant/VRF a deletar
    itens = []

    # Prioridade: se passou --tenant na linha de comando, usa modo simples
    # e ignora o arquivo padrão. Só usa arquivo se não houver --tenant.
    if args.tenant:
        itens.append({"tenant": args.tenant, "vrf": args.vrf})
        logger.info(f"🎯 Modo linha de comando: Tenant '{args.tenant}'")
    else:
        # Tenta usar arquivo padrão delete-tenant-vrf.txt
        arquivo_para_usar = args.arquivo
        if not os.path.exists(arquivo_para_usar):
            caminho_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), arquivo_para_usar)
            if os.path.exists(caminho_script):
                arquivo_para_usar = caminho_script
            else:
                arquivo_para_usar = None

        if arquivo_para_usar:
            itens = ler_arquivo_tenants_vrfs(arquivo_para_usar)
            logger.info(f"📄 Lidos {len(itens)} itens do arquivo: {arquivo_para_usar}")
        else:
            logger.error("❌ Informe --arquivo OU use --tenant")
            sys.exit(1)

    logger.info("=" * 70)
    logger.info("REPORT - EXCLUSÃO DE TENANT E VRF")
    logger.info("=" * 70)
    logger.info(f"APIC   : {args.apic}")
    logger.info(f"Usuário: {usuario}")
    logger.info(f"Qtd itens: {len(itens)}")
    logger.info("-" * 70)

    cookies = autenticar(args.apic, usuario, senha, verbose=args.verbose)

    deletados_vrf = []
    deletados_tenant = []
    pulados_vrf = []
    pulados_tenant = []
    falhas = []
    tenants_processados = set()

    for item in itens:
        tenant = item["tenant"]
        vrf = item["vrf"]

        # Primeiro tenta deletar VRF (se informada)
        if vrf:
            if not vrf_existe(args.apic, tenant, vrf, cookies, verbose=args.verbose):
                logger.warning(f"⚠️  VRF '{tenant}/{vrf}' não existe. Pulando.")
                pulados_vrf.append(f"{tenant}/{vrf}")
            else:
                sucesso, erro, resposta = deletar_vrf(
                    args.apic, tenant, vrf, cookies, verbose=args.verbose
                )
                if sucesso:
                    logger.info(f"✅ VRF '{tenant}/{vrf}' deletada com sucesso.")
                    deletados_vrf.append(f"{tenant}/{vrf}")
                else:
                    logger.error(f"❌ VRF '{tenant}/{vrf}' falhou: {erro}")
                    falhas.append((f"VRF {tenant}/{vrf}", erro))

        # Depois tenta deletar Tenant (só uma vez por tenant)
        if tenant not in tenants_processados:
            tenants_processados.add(tenant)

            if not tenant_existe(args.apic, tenant, cookies, verbose=args.verbose):
                logger.warning(f"⚠️  Tenant '{tenant}' não existe. Pulando.")
                pulados_tenant.append(tenant)
            else:
                sucesso, erro, resposta = deletar_tenant(
                    args.apic, tenant, cookies, verbose=args.verbose
                )
                if sucesso:
                    logger.info(f"✅ Tenant '{tenant}' deletado com sucesso.")
                    deletados_tenant.append(tenant)
                else:
                    logger.error(f"❌ Tenant '{tenant}' falhou: {erro}")
                    falhas.append((f"Tenant {tenant}", erro))

    logger.info("-" * 70)
    logger.info("RESUMO")
    logger.info("-" * 70)
    logger.info(f"Tenants processados: {len(tenants_processados)}")
    for t in sorted(tenants_processados):
        logger.info(f"  📦 {t}")
    logger.info(f"VRFs deletadas   : {len(deletados_vrf)}")
    for v in deletados_vrf:
        logger.info(f"  🗑️  {v}")
    logger.info(f"VRFs puladas     : {len(pulados_vrf)} (não existiam)")
    for v in pulados_vrf:
        logger.info(f"  ⚠️  {v}")
    logger.info(f"Tenants deletados: {len(deletados_tenant)}")
    for t in deletados_tenant:
        logger.info(f"  🗑️  {t}")
    logger.info(f"Tenants pulados  : {len(pulados_tenant)} (não existiam)")
    for t in pulados_tenant:
        logger.info(f"  ⚠️  {t}")
    logger.info(f"Falhas           : {len(falhas)}")
    for b, e in falhas:
        logger.info(f"  ❌ {b} -> {e}")
    logger.info("=" * 70)

    if falhas:
        sys.exit(1)


if __name__ == "__main__":
    main()
