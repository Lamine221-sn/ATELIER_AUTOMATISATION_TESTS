"""Wrapper HTTP : timeout strict, 1 retry max, gestion 429/5xx, mesure de latence."""
import os
import time

import requests

BASE_URL = os.environ.get("API_BASE_URL", "https://api.frankfurter.app")
TIMEOUT = 3          # secondes, strict
MAX_REQUESTS = 20    # budget de requêtes par run (anti-spam)
MAX_BACKOFF = 3      # on n'attend jamais plus de 3 s après un 429


class ApiClient:
    def __init__(self, base_url=BASE_URL, timeout=TIMEOUT, max_requests=MAX_REQUESTS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_requests = max_requests
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "api-tests-atelier/1.0"
        self.calls = []  # une entrée par requête réellement envoyée

    def get(self, path, params=None):
        """GET avec 1 retry max (timeout, 429, 5xx). Retourne toujours un dict."""
        result = {"status": None, "latency_ms": None, "json": None,
                  "content_type": "", "error": None, "retried": False}
        for attempt in range(2):
            if len(self.calls) >= self.max_requests:
                result["error"] = "budget de requêtes atteint"
                return result
            start = time.perf_counter()
            retry_wait = None
            try:
                r = self.session.get(self.base_url + path, params=params,
                                     timeout=self.timeout)
                latency = round((time.perf_counter() - start) * 1000, 1)
                result.update(status=r.status_code, latency_ms=latency, error=None,
                              content_type=r.headers.get("Content-Type", ""))
                try:
                    result["json"] = r.json()
                except ValueError:
                    result["json"] = None
                self.calls.append({"status": r.status_code, "latency_ms": latency,
                                   "error": None})
                if r.status_code == 429:
                    try:
                        retry_wait = min(float(r.headers.get("Retry-After", 1)), MAX_BACKOFF)
                    except ValueError:
                        retry_wait = 1
                elif r.status_code >= 500:
                    retry_wait = 0.5
            except requests.RequestException as exc:
                latency = round((time.perf_counter() - start) * 1000, 1)
                result.update(status=None, latency_ms=latency,
                              error=type(exc).__name__, json=None)
                self.calls.append({"status": None, "latency_ms": latency,
                                   "error": type(exc).__name__})
                retry_wait = 0.5
            if retry_wait is None or attempt == 1:
                return result
            result["retried"] = True
            time.sleep(retry_wait)
        return result
