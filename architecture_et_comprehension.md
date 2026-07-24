# Architecture et compréhension des workflows principaux

Ce document accompagne `Makefile.useful`.

Il contient uniquement les workflows principaux réellement exécutés et validés.
Il doit être mis à jour chaque fois qu'une nouvelle commande est ajoutée à
`Makefile.useful`.

## Vue d'ensemble

```text
verify
  -> vérifie le projet sans reconstruire les données

historical-data
  -> reconstruit et contrôle l'historique propre

modeling-data
  -> reconstruit les données, les features et le dataset d'entraînement

database-history
  -> reconstruit l'historique et le synchronise vers PostgreSQL

application
  -> démarre l'API Express et l'interface React
```

## 1. `verify`

### Commande

```bash
make -f Makefile.useful verify
```

### Rôle

Vérifier que la configuration, le code Python, l'API Express et l'application
React fonctionnent ensemble sans reconstruire les données ni entraîner de
modèle.

### Cibles Make appelées

```text
verify
  -> config-check
  -> compile-check
  -> inference-check
  -> test-python
  -> test-server
  -> test-client
  -> git diff --check
```

### Fonctions et composants principaux

- `electricity_predictor.config.load_configuration` charge et valide la
  configuration YAML.
- `compileall` vérifie la syntaxe de tous les modules sous `src/`.
- Pytest exécute les tests Python, notamment le serving, les modèles, le
  lifecycle, le stockage et le worker.
- Jest teste les routes, services, repositories et utilitaires Express.
- Vitest teste les contrats API, pages et composants React.
- Oxlint vérifie statiquement le code frontend.
- Vite construit l'application de production.

### Effets

- Peut créer des caches de test et `app/client/dist/`.
- Ne modifie pas PostgreSQL.
- N'entraîne et n'active aucun modèle.

## 2. `historical-data`

### Commande

```bash
make -f Makefile.useful historical-data
```

### Rôle

Reconstruire l'historique horaire propre à partir du CSV officiel et des
données AESO récentes, puis vérifier sa qualité.

### Cibles Make appelées

```text
historical-data
  -> refresh-data
  -> data-quality
```

### Point d'entrée principal

```text
src/electricity_predictor/data/pipeline.py
```

### Cascade des fonctions

```text
build_current_historical_dataset
  -> get_pipeline_paths
     -> load_configuration
  -> load_historical_data
     -> validate_historical_data
  -> get_api_start_date_for_history_overlap
  -> get_current_api_end_date
  -> fetch_pool_price_report
  -> normalize_pool_price_report
     -> validate_pool_price_data
  -> combine_historical_and_api_data
  -> DataFrame.to_csv
```

Le contrôle qualité utilise principalement :

```text
summarize_dataset
find_missing_hourly_timestamps
find_rows_with_missing_values
count_recent_incomplete_price_rows
print_quality_summary
```

### Logique importante

- Les prix réels historiques finalisés ne sont pas remplacés.
- Les données AESO complètent les prix réels manquants.
- Les prévisions AESO récentes ont priorité sur les anciennes prévisions.
- Les timestamps UTC dupliqués ou discontinus sont signalés.
- Un prix égal à zéro est une valeur valide, pas une valeur manquante.

### Entrées et sortie

```text
Entrées:
  data/raw/Hourly_Metered_Volumes_and_Pool_Price_and_AIL_2020-Jul2025.csv
  API AESO

Sortie:
  data/interim/current_historical_prices_clean.csv
```

### Effets

- Écrit un CSV intermédiaire ignoré par Git.
- Ne touche pas PostgreSQL.
- N'entraîne aucun modèle.

## 3. `modeling-data`

### Commande

```bash
make -f Makefile.useful modeling-data
```

### Rôle

Reconstruire toutes les données nécessaires à la modélisation, depuis
l'historique AESO jusqu'au dataset d'entraînement complet.

### Cibles Make appelées

```text
modeling-data
  -> historical-data
  -> features
  -> feature-quality
  -> training-data
```

### Point d'entrée des features

```text
src/electricity_predictor/features/feature_engineering.py
```

### Cascade des fonctions de features

```text
load_current_historical_dataset
build_basic_modeling_dataset
  -> validate_continuous_hourly_utc_timestamps
  -> add_time_features
  -> add_lag_features
  -> add_rolling_features
  -> add_horizon_target_features
     -> build_target_column_name
  -> build_target_column_names
write_modeling_dataset
```

### Features principales

```text
Temps local:
  hour, day_of_week, month, is_weekend

Valeurs passées:
  actual_price_lag_1h
  actual_price_lag_24h
  forecast_price_lag_1h

Fenêtres mobiles:
  actual_price_rolling_24h_mean
  actual_price_rolling_24h_max
  actual_price_rolling_7d_mean

Cibles futures:
  actual_price_target_1h
  actual_price_target_3h
  actual_price_target_6h
  actual_price_target_12h
  actual_price_target_24h
```

### Formules essentielles

```text
lag_1h(t) = actual_price(t - 1h)
lag_24h(t) = actual_price(t - 24h)
target_h(t) = actual_price(t + h)
```

Les fenêtres mobiles utilisent d'abord `shift(1)`. Elles ne voient donc jamais
le prix réel de l'heure qu'elles tentent de décrire.

### Construction du training dataset

Point d'entrée :

```text
src/electricity_predictor/features/training_data.py
```

Cascade :

```text
load_modeling_dataset
  -> build_training_dataset
     -> dropna(TRAINING_REQUIRED_COLUMNS)
  -> write_training_dataset
```

Une ligne est conservée seulement si toutes ses features et ses cinq cibles
futures sont connues. La cible à 24 heures explique pourquoi le training dataset
s'arrête 24 heures avant le dernier prix réel finalisé.

### Sorties

```text
data/processed/modeling_dataset.csv
data/processed/training_dataset.csv
```

### Effets

- Écrit deux CSV ignorés par Git.
- Ne touche pas PostgreSQL.
- N'entraîne aucun modèle.

## 4. `database-history`

### Commande

```bash
make -f Makefile.useful database-history
```

### Rôle

Reconstruire l'historique propre puis synchroniser chaque heure avec la table
PostgreSQL `hourly_prices`.

### Cibles Make appelées

```text
database-history
  -> historical-data
  -> sync-history
```

### Point d'entrée PostgreSQL

```text
src/electricity_predictor/worker/research_history_sync.py
```

### Cascade des fonctions

```text
synchronize_current_history
  -> load_current_history
  -> upsert_hourly_prices
     -> get_database_connection
     -> cursor.executemany
     -> connection.commit
```

### Logique de l'upsert

```text
Heure absente:
  -> insertion

Heure existante:
  -> compléter un actual_price manquant
  -> ne jamais remplacer un actual_price finalisé
  -> respecter la priorité des prévisions AESO
  -> ne jamais créer une deuxième ligne pour la même heure
```

### Entrée et table modifiée

```text
Entrée:
  data/interim/current_historical_prices_clean.csv

Table modifiée:
  hourly_prices

Tables non modifiées:
  prediction_runs
  predictions
```

### Propriété d'idempotence

Répéter la synchronisation avec le même CSV conserve le même nombre de lignes
et ne crée aucun doublon.

## 5. `application`

### Commande

```bash
make -f Makefile.useful application
```

### Rôle

Démarrer l'API Express et l'interface React pour le développement local.
`Ctrl+C` arrête les deux processus grâce au nettoyage du script.

### Cascade principale

```text
application
  -> dev
  -> scripts/dev-app.sh
     -> npm --prefix app/server run dev
        -> nodemon
        -> app/server/src/server.js
        -> createApp
     -> npm --prefix app/client run dev
        -> Vite
        -> app/client/src/main.jsx
        -> App
        -> router
```

### Chemin API

```text
PostgreSQL
  -> repositories
  -> now-service / today-service
  -> routes /api/v1/health, /now, /today
  -> hooks React
  -> pages Now et Today
```

### Comportement sans prédictions

- Health répond `200` et confirme la connexion PostgreSQL.
- Now répond `200` à partir du dernier prix réel finalisé.
- Today répond `404 PREDICTIONS_NOT_FOUND` sans inventer de prévisions.

### Effets

- Écoute temporairement sur les ports `8000` et `5173`.
- Ne crée aucune donnée ni aucun modèle.
- Les deux ports sont libérés après l'arrêt.

## Barrière Data Science avant la modélisation

Les commandes d'entraînement, de calibration et d'évaluation ne sont pas encore
exposées dans `Makefile.useful`. Elles seront ajoutées seulement après validation
complète de leur séparation chronologique.

### Les trois zones temporelles

```text
Train
  -> apprend les paramètres des modèles

Validation
  -> compare les candidats et calibre les règles de décision

Protected test
  -> mesure une seule fois le résultat final après la sélection
```

Analogie : le train correspond aux exercices, la validation à l'examen blanc et
le protected test à l'examen final. Consulter l'examen final pour choisir une
méthode rendrait sa note non fiable.

### Correction validée pour la calibration des décisions

Point d'entrée :

```text
src/electricity_predictor/modeling/decision/calibrate_decision_policy.py
```

La calibration cherchait auparavant les meilleurs quantiles et multiplicateurs
sur des données appartenant au protected test. Une première correction l'avait
déplacée sur validation, mais les artefacts chargés avaient déjà été réentraînés
sur `train + validation`. La correction complète entraîne maintenant une copie
du modèle sélectionné uniquement sur train, puis produit des prédictions hors
échantillon sur validation.

```text
split_calibration_data
  -> split_time_series_data_from_config
     -> train_data       entraîne le modèle sélectionné
     -> validation_data  reçoit les prédictions et calibre la politique
     -> test_data        ignoré et non exposé

load_selected_regression_models
  -> lit reports/best_regression_model.csv
  -> train_selected_regression_model(train_data)
  -> predict_selected_regression_model(validation_data)
```

Les artefacts finaux sous `models/regression/` ne sont pas utilisés pour cette
calibration, car ils sont entraînés sur `train + validation` et rendraient les
mesures de validation artificiellement optimistes.

Pour chaque horizon, la grille compare :

```text
recommended_quantile = 0.10, 0.15, 0.20 ou 0.25
avoid_iqr_multiplier = 1.5, 2.0, 2.5 ou 3.0
```

Les politiques sont ordonnées en minimisant d'abord les fausses recommandations,
puis les faux évitements, et en maximisant enfin l'accord exact. Le rapport de
calibration ne doit contenir que la période `validation`.

Le protected test reste fermé jusqu'à l'évaluation finale des modèles déjà
sélectionnés. Le stress test et les autres commandes qui l'utilisent ne doivent
donc pas être exécutés pendant la recherche ou la calibration.

### Séparation de l'orchestration des décisions

La cible `decision-analysis` enchaîne uniquement les analyses exploratoires, le
backtest et la calibration sur validation :

```text
decision-analysis
  -> decision-window-analysis
  -> decision-regime-analysis
  -> decision-policy-backtest
  -> decision-policy-calibration
```

La cible `predicted-decision-stress-test` reste séparée. Elle ouvre explicitement
le protected test et ne pourra être exécutée qu'après sélection définitive des
modèles et autorisation de l'évaluation finale.

### Séparation des orchestrateurs de recherche

`research-rebuild` est maintenant limité au travail répétable : reconstruction
des données, recherche des candidats, sélection sur validation et calibration
des décisions sur validation. Il n'appelle ni évaluation finale, ni sauvegarde
d'artefacts finaux, ni publication.

```text
research-rebuild
  -> données et features
  -> candidats de régression
  -> sélection de régression sur validation
  -> candidats de classification
  -> sélection de classification sur validation
  -> decision-analysis sur validation
  -> contrôles techniques
```

`research-rebuild-all` constitue la phase finale explicite :

```text
research-rebuild-all
  -> research-rebuild
  -> évaluations finales régression et classification
  -> sauvegarde des modèles sélectionnés sur train + validation
  -> stress test final des décisions
  -> synchronisation et publication des prédictions
```

Cette seconde commande ouvre le protected test et possède des effets sur les
artefacts et PostgreSQL. Elle est donc exclue de `Makefile.useful` et ne doit
être exécutée qu'une seule fois après approbation explicite.

### Sauvegarde finale des classificateurs

La sauvegarde des modèles de classification prépare uniquement train et
validation :

```text
prepare_classification_training_splits
  -> calcule le seuil de spike sur train seulement
  -> ajoute les cibles binaires à train
  -> applique le même seuil à validation
  -> n'accède pas au protected test

final_training_data = prepared_train + prepared_validation
```

La fonction plus large `prepare_classification_splits`, qui prépare également
le test, reste réservée au module d'évaluation finale protégée. Cette séparation
évite qu'une opération de sauvegarde ordinaire ne lise inutilement les réponses
de l'examen final.

### Analyses exploratoires des spikes

`spike-definition-analysis` compare les méthodes IQR, quantile 95 % et quantile
99 %. `spike-regime-analysis` décrit l'évolution annuelle des prix et des spikes.
Les seuils sont toujours calculés sur train, puis les rapports exploratoires
comparent uniquement train et validation.

```text
train
  -> calcule les seuils candidats
  -> produit les statistiques d'apprentissage

validation
  -> mesure la stabilité hors échantillon

protected test
  -> absent des deux analyses exploratoires
```

Les statistiques de prix, taux de spikes, maximums et quantiles du protected
test ne sont donc plus visibles pendant la conception ou la sélection.

### Entraînement et tuning des classificateurs

Les entrypoints de baseline, régression logistique, forêt aléatoire et gradient
boosting utilisent tous la même frontière :

```text
prepare_classification_training_splits
  -> seuil de spike appris sur train
  -> modèles entraînés ou tunés sur train
  -> candidats mesurés sur validation
  -> protected test ignoré
```

Les tuners appliquent `TimeSeriesSplit` uniquement à train avec le gap temporel
configuré. La validation fixe sert ensuite à comparer le candidat tuné aux autres
modèles. Le protected test n'est préparé que dans l'évaluation finale dédiée.

### Entraînement et tuning des régressions

Les baselines, modèles linéaires, Ridge, Lasso, Elastic Net et forêts aléatoires
respectent le même contrat :

```text
train
  -> entraînement des paramètres
  -> TimeSeriesSplit(gap configuré) pour les hyperparamètres

validation
  -> calcul de MAE et RMSE
  -> sélection du gagnant par horizon

protected test
  -> explicitement ignoré dans tous les entrypoints de recherche
```

Dans le code, le troisième résultat du split est affecté à `_`. Cette convention
rend visible qu'il existe, mais qu'aucun workflow de recherche ne doit le lire.

### Sélection des gagnants

Les deux sélecteurs filtrent d'abord les résultats sur `split == "validation"` :

```text
Régression
  -> plus faible MAE par horizon
  -> RMSE disponible comme métrique autorisée alternative

Classification
  -> plus fort F1 par horizon
  -> recall, precision et accuracy départagent les égalités
```

Les tests injectent également des résultats artificiels du protected test. Même
si leurs métriques sont parfaites, ces lignes sont rejetées avant le classement.

### Évaluation finale protégée

Les modules `final_test_evaluation.py` sont les seuls chemins de modélisation
autorisés à calculer les métriques finales du protected test.

```text
Régression
  -> charge le gagnant sélectionné sur validation
  -> entraîne sur train + validation
  -> calcule MAE et RMSE une fois sur test

Classification
  -> charge le gagnant sélectionné sur validation
  -> entraîne sur train pour choisir le seuil de probabilité sur validation
  -> réentraîne sur train + validation avec ce seuil gelé
  -> calcule les métriques, matrices de confusion et intervalles sur test
```

Les lignes finales portent explicitement `split="test"`. Ces résultats servent à
documenter la performance finale, jamais à changer de modèle, d'hyperparamètre,
de feature, de seuil ou de politique de décision.

### Lifecycle et comparaison champion/challenger

Le lifecycle utilise un nouveau plan temporel à chaque cycle autorisé. Ses trois
splits sont gelés dans un manifeste contenant les bornes, nombres de lignes et
empreinte SHA-256 du dataset. Le manifeste décrit les données; il ne calcule pas
de métriques.

```text
train + validation gelés
  -> réentraînent les designs déjà sélectionnés

lifecycle_test gelé
  -> évalue le candidat
  -> réévalue le champion sur exactement les mêmes lignes
  -> permet une comparaison équitable par horizon
```

La régression exige que le candidat ne dégrade ni MAE ni RMSE. La classification
compare recall, F1 et PR-AUC avec une définition de spike commune. La sortie est
seulement une recommandation `promotion_ready`; le runner interdit la promotion
automatique et `lifecycle-promote` exige une action manuelle séparée.

### Parité entre entraînement et serving

Les modèles et le worker partagent `MODEL_FEATURE_COLUMNS` ainsi que les mêmes
fonctions `add_time_features`, `add_lag_features` et `add_rolling_features`.

```text
PostgreSQL
  -> 168 heures historiques + la ligne candidate
  -> validation des heures, doublons, actuals finalisés et forecasts
  -> mêmes transformations que pendant l'entraînement
  -> une ligne candidate ordonnée selon les métadonnées de l'artefact
  -> prédictions régression et classification
```

Les lags utilisent toujours les heures précédentes. Les fenêtres mobiles font
`shift(1)` avant leur calcul : le prix réel de la ligne candidate n'entre jamais
dans ses propres features. Le worker refuse les valeurs manquantes et ne remplace
jamais silencieusement la candidate par une heure plus ancienne.

L'ordre des colonnes est enregistré dans les métadonnées de chaque artefact puis
reconstruit par `prepare_feature_row`. Une feature absente provoque un échec au
lieu d'une prédiction avec un contrat différent de l'entraînement.

## Règle de mise à jour

Un nouveau workflow est ajouté à `Makefile.useful`, puis documenté ici,
uniquement après avoir :

1. été exécuté manuellement;
2. produit un rapport lisible;
3. réussi avec un code de sortie nul;
4. été confirmé comme sûr pour son usage prévu.

Les workflows bloqués, destructifs ou non testés ne figurent pas comme commandes
validées. Une règle de sécurité découverte pendant l'audit peut néanmoins être
documentée immédiatement afin d'éviter sa réintroduction.
