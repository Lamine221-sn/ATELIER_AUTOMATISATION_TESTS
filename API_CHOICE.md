# API Choice

- Étudiant : Lamine Mbengue
- API choisie : Frankfurter (taux de change)
- URL base : https://api.frankfurter.app
- Documentation officielle / README : https://frankfurter.dev (et fiche dans la liste public-apis)
- Auth : None
- Endpoints testés :
  - GET /latest?from=EUR (+ variantes `to=USD`, `amount=10`)
  - GET /currencies
  - GET /2020-01-02?from=EUR&to=USD (taux historique)
  - GET /latest?from=XXX et GET /pas-une-date (cas d'erreur attendus)
- Hypothèses de contrat (champs attendus, types, codes) :
  - 200 + `application/json` ; objet avec `amount` (nombre), `base` (string), `date` (string AAAA-MM-JJ), `rates` (objet devise -> nombre > 0)
  - `rates` ne contient pas la devise de base ; `to=USD` limite `rates` à `USD`
  - `/currencies` : objet code -> libellé (string), contient EUR et USD
  - Devise ou date invalide : erreur 4xx (400, 404 ou 422 acceptés)
- Limites / rate limiting connu : pas de clé ; usage raisonnable demandé. Le projet limite à 20 requêtes par run et 1 run / 5 min.
- Risques (instabilité, downtime, CORS, etc.) : taux mis à jour seulement les jours ouvrés (la date peut reculer), service gratuit sans SLA, changement possible de domaine (api.frankfurter.dev).
