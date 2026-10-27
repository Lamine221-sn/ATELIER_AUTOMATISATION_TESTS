"""Tests "as code" pour l'API Frankfurter (taux de change, sans authentification).

Chaque test reçoit un contexte, lève AssertionError s'il échoue
et retourne la réponse principale utilisée (pour la latence).
Tous les appels sont des GET : aucun test n'est destructif.
"""
import re

NUMBER = (int, float)


def _ok(resp):
    assert resp["error"] is None, f"erreur réseau : {resp['error']}"
    return resp


class Context:
    """Garde en cache l'appel /latest pour ne pas surcharger l'API."""

    def __init__(self, client):
        self.client = client
        self._latest = None

    def latest(self):
        if self._latest is None:
            self._latest = self.client.get("/latest", {"from": "EUR"})
        return self._latest


# ---------- A. Contrat ----------
def test_latest_status_et_content_type(ctx):
    r = _ok(ctx.latest())
    assert r["status"] == 200, f"statut {r['status']} au lieu de 200"
    assert "json" in r["content_type"].lower(), f"Content-Type = {r['content_type']}"
    return r


def test_latest_champs_obligatoires(ctx):
    r = _ok(ctx.latest())
    body = r["json"]
    assert isinstance(body, dict), "la réponse n'est pas un objet JSON"
    manquants = [c for c in ("amount", "base", "date", "rates") if c not in body]
    assert not manquants, f"champs manquants : {manquants}"
    return r


def test_latest_types(ctx):
    r = _ok(ctx.latest())
    b = r["json"]
    assert isinstance(b["amount"], NUMBER), "amount doit être un nombre"
    assert isinstance(b["base"], str), "base doit être une chaîne"
    assert isinstance(b["date"], str), "date doit être une chaîne"
    assert isinstance(b["rates"], dict) and b["rates"], "rates doit être un objet non vide"
    assert all(isinstance(v, NUMBER) and v > 0 for v in b["rates"].values()), \
        "chaque taux doit être un nombre > 0"
    return r


def test_latest_base_et_format_date(ctx):
    r = _ok(ctx.latest())
    b = r["json"]
    assert b["base"] == "EUR", f"base = {b['base']}"
    assert "EUR" not in b["rates"], "la devise de base ne doit pas figurer dans rates"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", b["date"]), f"format de date inattendu : {b['date']}"
    return r


def test_filtre_to(ctx):
    r = _ok(ctx.client.get("/latest", {"from": "EUR", "to": "USD"}))
    assert r["status"] == 200, f"statut {r['status']}"
    assert set(r["json"]["rates"]) == {"USD"}, f"devises reçues : {list(r['json']['rates'])}"
    ctx.usd_rate = r["json"]["rates"]["USD"]
    return r


def test_amount_proportionnel(ctx):
    r = _ok(ctx.client.get("/latest", {"from": "EUR", "to": "USD", "amount": 10}))
    assert r["status"] == 200, f"statut {r['status']}"
    assert r["json"]["amount"] == 10, f"amount = {r['json']['amount']}"
    unitaire = getattr(ctx, "usd_rate", None)
    if unitaire:  # le taux peut bouger légèrement entre deux appels : 5 % de tolérance
        ratio = r["json"]["rates"]["USD"] / (unitaire * 10)
        assert 0.95 <= ratio <= 1.05, f"10 EUR ne vaut pas ~10x le taux unitaire (ratio {ratio:.3f})"
    return r


def test_endpoint_currencies(ctx):
    r = _ok(ctx.client.get("/currencies"))
    assert r["status"] == 200, f"statut {r['status']}"
    b = r["json"]
    assert isinstance(b, dict) and "EUR" in b and "USD" in b, "EUR/USD absents de /currencies"
    assert all(isinstance(v, str) for v in b.values()), "les libellés doivent être des chaînes"
    return r


def test_date_historique(ctx):
    r = _ok(ctx.client.get("/2020-01-02", {"from": "EUR", "to": "USD"}))
    assert r["status"] == 200, f"statut {r['status']}"
    assert r["json"]["date"] == "2020-01-02", f"date reçue : {r['json']['date']}"
    return r


# ---------- Cas d'erreur attendus ----------
def test_devise_invalide(ctx):
    r = _ok(ctx.client.get("/latest", {"from": "XXX"}))
    assert r["status"] in (400, 404, 422), f"statut {r['status']} (erreur 4xx attendue)"
    return r


def test_date_invalide(ctx):
    r = _ok(ctx.client.get("/pas-une-date"))
    assert r["status"] in (400, 404, 422), f"statut {r['status']} (erreur 4xx attendue)"
    return r


TESTS = [
    test_latest_status_et_content_type,
    test_latest_champs_obligatoires,
    test_latest_types,
    test_latest_base_et_format_date,
    test_filtre_to,
    test_amount_proportionnel,
    test_endpoint_currencies,
    test_date_historique,
    test_devise_invalide,
    test_date_invalide,
]
