# ══════════════════════════════════════════════════════════════
# ATHIVE SISTEMA v1.3 — Motor de Sincronização
# Envia alterações locais ao Supabase a cada 30 minutos.
# Offline-first: falhas são silenciosas, retentativa automática.
# ══════════════════════════════════════════════════════════════

import threading, sqlite3, json, datetime, time
from config import DB_PATH, SUPABASE_URL, SUPABASE_KEY, SYNC_INTERVAL_SECONDS

_sync_thread = None
_stop_event  = threading.Event()
_status      = {"online": False, "ultimo_sync": None, "pendentes": 0, "erro": None}
_listeners   = []   # callbacks para atualizar UI

def get_status() -> dict:
    return _status.copy()

def add_listener(fn):
    """Registra callback chamado após cada sync."""
    _listeners.append(fn)

def _notify():
    for fn in _listeners:
        try: fn(_status.copy())
        except: pass

def _get_conn():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c

def _contar_pendentes() -> int:
    try:
        c = _get_conn()
        row = c.execute("SELECT COUNT(*) as n FROM sync_queue WHERE enviado_em IS NULL").fetchone()
        c.close()
        return row["n"] if row else 0
    except:
        return 0

def _verificar_online() -> bool:
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/",
            headers={"apikey": SUPABASE_KEY},
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status in (200, 404)
    except:
        return False

def _enviar_item(item: dict) -> bool:
    """Envia um item da fila ao Supabase via REST."""
    try:
        import urllib.request, urllib.error
        tabela    = item["tabela"]
        operacao  = item["operacao"]
        reg_id    = item["registro_id"]
        payload   = json.loads(item["payload"]) if item["payload"] else {}

        base = f"{SUPABASE_URL}/rest/v1/{tabela}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

        if operacao == "DELETE":
            url = f"{base}?id=eq.{reg_id}"
            req = urllib.request.Request(url, headers=headers, method="DELETE")
        elif operacao == "INSERT":
            payload["id"] = reg_id
            data = json.dumps(payload).encode()
            req = urllib.request.Request(base, data=data, headers={
                **headers, "Prefer": "resolution=merge-duplicates,return=minimal"
            }, method="POST")
        else:  # UPDATE
            url  = f"{base}?id=eq.{reg_id}"
            data = json.dumps(payload).encode()
            req  = urllib.request.Request(url, data=data, headers=headers, method="PATCH")

        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status in (200, 201, 204)
    except Exception as e:
        _status["erro"] = str(e)[:120]
        return False

def _executar_sync():
    inicio = datetime.datetime.now().isoformat()
    enviados = 0
    erros    = 0

    try:
        c = _get_conn()
        items = c.execute("""
            SELECT * FROM sync_queue
            WHERE enviado_em IS NULL AND tentativas < 5
            ORDER BY id ASC LIMIT 100
        """).fetchall()
        c.close()

        for item in items:
            item = dict(item)
            ok = _enviar_item(item)
            c = _get_conn()
            if ok:
                c.execute(
                    "UPDATE sync_queue SET enviado_em=?, tentativas=tentativas+1 WHERE id=?",
                    (datetime.datetime.now().isoformat(), item["id"])
                )
                enviados += 1
            else:
                c.execute(
                    "UPDATE sync_queue SET tentativas=tentativas+1 WHERE id=?",
                    (item["id"],)
                )
                erros += 1
            c.commit()
            c.close()

        # Marcar synced nas tabelas
        tabelas = ["usuarios","alunos","equipamentos","manutencao","financeiro","compras","frequencia"]
        c = _get_conn()
        for tab in tabelas:
            c.execute(f"UPDATE {tab} SET synced=1 WHERE synced=0")
        c.commit()
        c.close()

        # Gravar log
        c = _get_conn()
        c.execute("""
            INSERT INTO sync_log (inicio,fim,status,enviados,erros,mensagem)
            VALUES (?,?,?,?,?,?)
        """, (inicio, datetime.datetime.now().isoformat(),
              "success" if erros == 0 else "partial",
              enviados, erros,
              f"{enviados} enviados, {erros} erros"))
        c.commit()
        c.close()

        _status["ultimo_sync"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        _status["pendentes"]   = _contar_pendentes()
        _status["erro"]        = None if erros == 0 else f"{erros} item(s) com erro"

    except Exception as e:
        _status["erro"] = f"Sync falhou: {str(e)[:100]}"

    _notify()

def _loop():
    while not _stop_event.is_set():
        _status["pendentes"] = _contar_pendentes()
        online = _verificar_online()
        _status["online"] = online
        if online and _status["pendentes"] > 0:
            _executar_sync()
        else:
            _notify()
        _stop_event.wait(SYNC_INTERVAL_SECONDS)

def iniciar():
    global _sync_thread
    _stop_event.clear()
    _status["pendentes"] = _contar_pendentes()
    _sync_thread = threading.Thread(target=_loop, daemon=True, name="SyncEngine")
    _sync_thread.start()

def parar():
    _stop_event.set()

def forcar_agora():
    """Força sync imediato em thread separada."""
    threading.Thread(target=_executar_sync, daemon=True, name="SyncForced").start()
