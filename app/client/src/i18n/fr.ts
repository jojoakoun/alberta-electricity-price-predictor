import type { RecommendationLevel } from "../types/recommendation";

export const fr = {
  brand: {
    name: "WattWise",
    tagline: "Utilisez l’électricité au meilleur moment.",
  },

  navigation: {
    now: "Maintenant",
    today: "Aujourd’hui",
    learn: "Comprendre",
    project: "Projet",
  },

  language: {
    selector: "Langue",
    english: "English",
    french: "Français",
    mainNavigation: "Navigation principale",
    mobileNavigation: "Navigation mobile",
    openMenu: "Ouvrir le menu",
    closeMenu: "Fermer le menu",
  },

  audience: {
    compactTitle:
      "Conçu pour les tarifs d’électricité variables.",
    compactText:
      "WattWise est surtout utile aux ménages de l’Alberta dont le tarif change selon le marché.",
    fixedCompact:
      "Avec un tarif fixe, changer l’heure d’utilisation ne modifiera généralement pas votre tarif d’énergie.",
    title: "À qui s’adresse WattWise?",
    primary:
      "Aux ménages de l’Alberta qui ont un tarif d’électricité variable ou flottant.",
    detail:
      "WattWise est surtout utile lorsque certaines tâches, comme la lessive, le lave-vaisselle ou la recharge d’un véhicule électrique, peuvent être déplacées à une autre heure.",
    fixedTitle: "Vous avez un tarif fixe?",
    fixedDetail:
      "Changer l’heure à laquelle vous utilisez l’électricité ne modifiera généralement pas le tarif d’énergie indiqué sur votre facture.",
    project:
      "WattWise est principalement conçu pour les ménages de l’Alberta ayant un tarif variable ou flottant et capables de déplacer certaines utilisations de l’électricité à une autre heure.",
  },

  recommendations: {
    recommended: {
      label: "Bon moment",
      defaultExplanation:
        "Le prix de l’électricité est avantageux en ce moment.",
    },
    acceptable: {
      label: "Moment acceptable",
      defaultExplanation:
        "Le prix est raisonnable, mais un meilleur moment pourrait arriver.",
    },
    avoid: {
      label: "Mieux vaut attendre",
      defaultExplanation:
        "Le prix est plus élevé que d’habitude en ce moment.",
    },
    unavailable: {
      label: "Recommandation indisponible",
      defaultExplanation:
        "Nous ne pouvons pas fournir une recommandation suffisamment fiable en ce moment.",
    },
  } satisfies Record<
    RecommendationLevel,
    {
      label: string;
      defaultExplanation: string;
    }
  >,

  actions: {
    run_heavy_appliances:
      "Ce pourrait être un bon moment pour utiliser les appareils que vous pouvez démarrer plus tard.",
    use_if_needed:
      "Vous pouvez utiliser l’électricité maintenant si nécessaire.",
    wait_if_possible:
      "Attendez un meilleur moment si cette tâche peut être reportée.",
  },

  context: {
    lower_than_usual:
      "Prix inférieur aux conditions récentes du marché.",
    about_average:
      "Prix semblable aux conditions récentes du marché.",
    higher_than_usual:
      "Prix supérieur aux conditions récentes du marché.",
  },

  temporal: {
    very_soon: "Très bientôt",
    in_a_few_hours: "Dans quelques heures",
    this_afternoon: "Cet après-midi",
    this_evening: "Ce soir",
    overnight: "Pendant la nuit",
    later_today: "Plus tard aujourd’hui",
    tomorrow_around_this_time:
      "Demain à peu près à la même heure",
  },

  learnPage: {
    hero: {
      title: "Comprendre WattWise",
      description:
        "Découvrez comment les données officielles du marché de l’électricité en Alberta deviennent une recommandation simple à utiliser.",
      chips: {
        data: "Données officielles",
        forecasts: "Cinq prévisions",
        recommendations: "Conseils faciles à comprendre",
      },
    },

    process: {
      title: "Comment fonctionne WattWise",
      description:
        "WattWise transforme les données horaires du marché en cinq prévisions et en une recommandation claire pour planifier votre consommation.",
      modelReview:
        "Les modèles sont réévalués périodiquement avec des données plus récentes et sont utilisés seulement après révision et approbation.",
      stepLabel: "Étape",

      steps: {
        data: {
          title: "Données officielles sur l’électricité",
          description:
            "WattWise commence avec les prix horaires publics de l’électricité et la demande totale en Alberta.",
        },
        patterns: {
          title: "Tendances historiques",
          description:
            "Le système compare les conditions actuelles aux tendances observées dans plusieurs années de données.",
        },
        forecasts: {
          title: "Cinq véritables prévisions",
          description:
            "Les prix sont estimés pour les prochaines 1, 3, 6, 12 et 24 heures. WattWise n’invente pas de valeurs entre ces prévisions.",
        },
        recommendation: {
          title: "Une recommandation claire",
          description:
            "Les prix prévus sont convertis en Bon moment, Moment acceptable ou Mieux vaut attendre.",
        },
      },
    },

    recommendations: {
      title: "Comprendre les recommandations",
      description:
        "La recommandation vous aide à décider si une tâche flexible devrait être effectuée maintenant ou plus tard.",

      good: {
        title: "Bon moment",
        description:
          "Le prix est avantageux par rapport aux conditions récentes. Ce pourrait être un bon moment pour utiliser certains appareils flexibles.",
      },
      okay: {
        title: "Moment acceptable",
        description:
          "Le prix est acceptable. Vous pouvez utiliser l’électricité si nécessaire, même si un meilleur moment pourrait être prévu.",
      },
      wait: {
        title: "Mieux vaut attendre",
        description:
          "Le prix ou le risque du marché est élevé. Reporter une tâche flexible pourrait être préférable.",
      },
    },

    dataSource: {
      title: "Origine des données",
      organization:
        "Alberta Electric System Operator (AESO)",
      description:
        "L’Alberta Electric System Operator assure le fonctionnement sécuritaire et fiable du réseau électrique interconnecté de l’Alberta. L’AESO publie les données officielles du marché utilisées par WattWise.",
      websiteLabel: "Consulter le site officiel de l’AESO",
      websiteUrl: "https://www.aeso.ca",

      items: {
        prices: "Prix horaires du marché albertain",
        forecastPrices: "Prévisions de prix de l’AESO",
        load: "Demande interne de l’Alberta (AIL)",
        public: "Données publiques du marché de l’électricité",
      },
    },

    confidence: {
      title: "Pourquoi la fiabilité change",
      description:
        "Les prévisions à court terme utilisent généralement des renseignements plus récents. L’incertitude augmente lorsque la prévision regarde plus loin dans le temps.",

      horizons: {
        one: {
          label: "Dans 1 heure",
          detail: "Plus utile pour une décision immédiate",
        },
        three: {
          label: "Dans 3 heures",
          detail: "Utile pour planifier à court terme",
        },
        six: {
          label: "Dans 6 heures",
          detail: "Utile pour planifier plus tard aujourd’hui",
        },
        twelve: {
          label: "Dans 12 heures",
          detail: "Une plus grande incertitude est normale",
        },
        twentyFour: {
          label: "Dans 24 heures",
          detail: "À utiliser comme guide de planification",
        },
      },
    },

    limits: {
      eyebrow: "Planifier de façon responsable",
      title: "Limites importantes",
      introduction:
        "WattWise facilite la planification, mais ne peut pas garantir le prix futur de l’électricité.",

      items: {
        prediction:
          "Les prévisions sont des estimations basées sur les données historiques et les conditions actuelles.",
        events:
          "Les pannes, la météo, la demande et les événements imprévus peuvent rapidement modifier les prix.",
        bill:
          "Le prix du marché affiché ne correspond pas à la totalité de votre facture d’électricité.",
        planning:
          "Utilisez WattWise comme outil de planification, et non comme garantie financière.",
      },
    },
  },

  projectPage: {
    hero: {
      eyebrow: "Projet",
      title: "WattWise",
      description:
        "Une application complète d’apprentissage automatique qui transforme les données du marché albertain de l’électricité en recommandations claires et pratiques.",
      byline: "Conçu et développé par",
      developer: "Joël-Hervé Akoun",
      linkedInLabel: "Communiquer sur LinkedIn",
      linkedInUrl: "https://www.linkedin.com/in/joelakoun/",
      disciplines: {
        data: "Ingénierie des données",
        machineLearning: "Apprentissage automatique",
        product: "Produit web complet",
      },
    },

    story: {
      eyebrow: "Pourquoi WattWise",
      title: "L’histoire du projet",
      introduction:
        "Le prix de l’électricité en Alberta peut changer considérablement d’une heure à l’autre.",
      problem:
        "La plupart des gens n’ont ni le temps ni les connaissances techniques nécessaires pour analyser les prix, la demande et les prévisions du marché.",
      solution:
        "WattWise transforme cette complexité en recommandations simples pour aider les utilisateurs à décider s’ils devraient utiliser l’électricité maintenant ou attendre.",
    },

    highlights: {
      title: "Le projet en chiffres",
      description:
        "WattWise réunit l’ingénierie des données, l’apprentissage automatique, le développement backend et une interface responsive.",
      records: {
        value: "57 000+",
        label: "Observations horaires du marché",
      },
      horizons: {
        value: "5",
        label: "Périodes de prévision",
      },
      window: {
        value: "24 h",
        label: "Période de planification",
      },
      system: {
        value: "Complet",
        label: "Des données jusqu’à l’interface",
      },
    },

    journey: {
      title: "Des données à la décision",
      description:
        "Chaque partie remplit un rôle clair, de la collecte des données officielles jusqu’à la recommandation présentée à l’utilisateur.",
      startLabel:
        "Les données du marché entrent dans WattWise",
      endLabel:
        "Une recommandation claire arrive à l’utilisateur",
      stepLabel: "Étape",

      steps: {
        source: {
          title: "Données du marché de l’AESO",
          description:
            "Les prix horaires, les prévisions de prix et la demande interne de l’Alberta constituent la base du système.",
        },
        data: {
          title: "Ingénierie des données",
          description:
            "Les données historiques et récentes sont nettoyées, vérifiées, normalisées et réunies.",
        },
        features: {
          title: "Création des variables",
          description:
            "L’heure, l’historique des prix, les comportements du marché et la demande deviennent utilisables par les modèles.",
        },
        models: {
          title: "Apprentissage automatique",
          description:
            "Les modèles estiment les prix futurs et détectent les périodes où le risque du marché est plus élevé.",
        },
        api: {
          title: "API de prévision",
          description:
            "PostgreSQL et Express fournissent des réponses de prévision normalisées à l’application.",
        },
        product: {
          title: "Interface React",
          description:
            "L’interface transforme les prévisions en recommandations claires pour la planification quotidienne.",
        },
      },
    },

    principles: {
      title: "Principes d’ingénierie",
      description:
        "WattWise a été conçu autour de données fiables, d’une évaluation honnête et de résultats faciles à comprendre.",

      items: [
        {
          title: "Validation dans l’ordre du temps",
          description:
            "Les anciennes données servent à entraîner les modèles et les données plus récentes à vérifier leurs résultats.",
        },
        {
          title: "Protection contre les informations futures",
          description:
            "Les séparations temporelles empêchent l’utilisation accidentelle de renseignements futurs.",
        },
        {
          title: "Seuils calculés avec les données d’entraînement",
          description:
            "Les seuils sont définis sans consulter les données protégées du test final.",
        },
        {
          title: "Recommandations explicables",
          description:
            "L’utilisateur reçoit une indication claire plutôt qu’un résultat brut difficile à interpréter.",
        },
        {
          title: "Architecture modulaire",
          description:
            "Les données, les modèles, le worker, l’API et l’interface restent séparés.",
        },
        {
          title: "Vérification automatisée",
          description:
            "Des tests Python, API et frontend protègent l’application pendant son évolution.",
        },
      ],
    },

    stack: {
      title: "Technologies utilisées",
      description:
        "L’application réunit des outils d’ingénierie des données, d’apprentissage automatique, de backend et de frontend.",

      technologies: [
        "Python",
        "Pandas",
        "scikit-learn",
        "PostgreSQL",
        "Express",
        "React",
        "TypeScript",
        "Docker",
        "Vite",
        "Vitest",
        "Jest",
        "Git",
      ],
    },

    developer: {
      title: "Rencontrer le développeur",
      name: "Joël-Hervé Akoun",
      roles:
        "Analyste de données · Développeur BI · Ingénieur de données",
      location: "Edmonton, Alberta",
      education:
        "Intelligence artificielle et analyse de données · Red Deer Polytechnic",
      description:
        "Je construis des produits de données complets, de l’ingénierie des données et de l’apprentissage automatique jusqu’aux API backend et aux interfaces web qui facilitent les décisions.",
      linkedInLabel: "Voir le profil LinkedIn",
      linkedInUrl: "https://www.linkedin.com/in/joelakoun/",
      photoPath: "/joel.png",
    },

    reflection: {
      eyebrow: "Réflexion",
      title: "Ce que j’ai appris",
      description:
        "La création de WattWise m’a confirmé qu’un bon produit d’apprentissage automatique dépend de beaucoup plus que la performance du modèle. La fiabilité des données, l’évaluation, les tests, l’architecture logicielle et l’expérience utilisateur déterminent si une prévision devient réellement utile.",
    },

    signature: {
      label: "Conçu et développé en Alberta par",
      name: "Joël-Hervé Akoun",
    },
  },

  pages: {
    now: {
      eyebrow: "Décision immédiate",
      title:
        "Est-ce un bon moment pour utiliser l’électricité?",
      description:
        "Une recommandation claire basée sur les plus récentes conditions disponibles du marché albertain de l’électricité.",
      todayLink: "Voir les prévisions d’aujourd’hui",
      todayLinkDescription:
        "Comparer les cinq périodes de prévision.",
    },

    today: {
      eyebrow: "Planification d’aujourd’hui",
      title: "Quel serait un meilleur moment?",
      description:
        "Cinq véritables prévisions montrent comment le prix pourrait évoluer au cours des prochaines 24 heures.",
      exploreTitle: "Comparer chaque prévision",
      exploreDescription:
        "Ouvrez les détails pour comparer la recommandation de chaque période.",
    },

    learn: {
      title: "Comment fonctionne WattWise",
      description:
        "Des explications simples sur les données, les prévisions et les limites.",
    },
  },

  freshness: {
    updated: "Recommandation mise à jour à",
    observed: "Prix observé à",
    delayed: "Données retardées",
  },

  forecast: {
    bestTimeTitle: "Meilleur moment prévu",
    bestOpportunity: "Meilleure occasion",
    futurePriceLabel:
      "Prévision future la plus basse",
    currentObservedPriceLabel:
      "Prix actuel observé sur le marché",

    horizons: {
      one: "1 heure",
      three: "3 heures",
      six: "6 heures",
      twelve: "12 heures",
      twentyFour: "24 heures",
    },

    comparison: {
      lowerEyebrow: "Économie possible",
      lowerTitle: "Un prix plus bas est prévu",
      lowerBefore:
        "La prévision la plus basse est de",
      lowerAfter:
        "¢/kWh sous le prix actuel observé.",

      sameEyebrow: "Aucune économie prévue",
      sameTitle:
        "Attendre ne devrait pas réduire le prix",
      sameDescription:
        "La prévision future la plus basse est identique au prix actuel observé sur le marché.",
      sameBadge: "Même prix que maintenant",

      currentEyebrow:
        "Le prix actuel est plus avantageux",
      currentTitle:
        "Le prix actuel est déjà plus bas",
      currentBefore:
        "Le prix actuel observé est de",
      currentAfter:
        "¢/kWh sous la prévision future la plus basse.",
      currentBadge: "Le prix actuel est plus bas",
    },

    currentPriceReference: "Prix actuel",
    observedPriceAt: "Prix observé à",
    sameAsObservedPrice:
      "Même valeur que le prix observé",
    todayLabel: "Aujourd’hui",
    tomorrowLabel: "Demain",
    expectedPrice: "Prix prévu",
    bestTimeExplanation:
      "Prix prévu le plus bas au cours des prochaines 24 heures.",
    tomorrowCaution:
      "La prévision à 24 heures est moins fiable. Utilisez-la comme guide de planification, et non comme garantie.",
    timelineLabel:
      "Cinq points de prévision pour aujourd’hui",
    viewForecasts: "Voir toutes les prévisions",
    priceComparison: "Comparaison des prix",
    forecastDetails: "Détails des prévisions",
    hideDetails: "Masquer les détails",
    priceTrendTitle: "Évolution prévue du prix",
    priceTrendDescription:
      "La courbe lissée est seulement un repère visuel reliant cinq prévisions distinctes. Les valeurs entre les points ne sont pas prédites par les modèles.",
  },

  explanations: {
    lower_than_usual:
      "Le prix prévu est avantageux par rapport aux conditions récentes du marché.",
    acceptable_market_risk:
      "Le prix prévu est acceptable, mais le risque du marché augmente.",
    higher_than_usual:
      "Le prix prévu est élevé par rapport aux conditions récentes du marché.",
  },

  states: {
    loading:
      "Vérification des plus récentes données sur l’électricité…",
    errorTitle:
      "WattWise n’a pas pu charger la dernière mise à jour.",
    retry: "Réessayer",
  },

  price: {
    label: "Prix actuel de l’électricité",
  },

  confidence: {
    high: "La recommandation la plus récente est disponible",
    moderate: "La dernière mise à jour pourrait être retardée",
    low: "Recommandation indisponible",
  },

  creator: {
    label: "Créé par",
    name: "Joël-Hervé Akoun",
    initials: "JA",
    photoPath: "/joel.png",
    linkedInUrl: "https://www.linkedin.com/in/joelakoun/",
    linkedInLabel: "Voir le profil LinkedIn",
  },

  footer: {
    disclaimer:
      "Votre facture finale dépend de votre détaillant et de votre forfait d’électricité.",
  },
} as const;
