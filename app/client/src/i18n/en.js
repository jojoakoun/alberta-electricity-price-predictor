export const en = {
  brand: {
    name: "WattWise",
    tagline: "Use electricity at a smarter time.",
  },

  navigation: {
    now: "Now",
    today: "Today",
    learn: "Learn",
    project: "Project",
  },

  language: {
    selector: "Language",
    english: "English",
    french: "Français",
    mainNavigation: "Main navigation",
    mobileNavigation: "Mobile navigation",
    openMenu: "Open menu",
    closeMenu: "Close menu",
  },

  audience: {
    compactTitle: "Designed for variable electricity plans.",
    compactText:
      "WattWise is most useful for Alberta households whose electricity rate changes with the market.",
    fixedCompact:
      "With a fixed-rate plan, changing the time of use will usually not change your energy rate.",
    title: "Who WattWise is for",
    primary:
      "Alberta households on variable or floating electricity plans.",
    detail:
      "WattWise is most useful when flexible tasks such as laundry, dishwashing, or EV charging can be moved to another hour.",
    fixedTitle: "On a fixed-rate plan?",
    fixedDetail:
      "Changing when you use electricity will usually not change the electricity rate charged on your bill.",
    project:
      "WattWise is primarily designed for Alberta households on variable or floating electricity plans who can move flexible electricity use to another hour.",
  },

  recommendations: {
    recommended: {
      label: "Good time",
      defaultExplanation:
        "Electricity prices are favourable right now.",
    },
    acceptable: {
      label: "Okay time",
      defaultExplanation:
        "Electricity use is acceptable, but this is not the best time.",
    },
    avoid: {
      label: "Better to wait",
      defaultExplanation:
        "Prices are higher than usual right now.",
    },
    unavailable: {
      label: "Recommendation unavailable",
      defaultExplanation:
        "We cannot make a confident recommendation right now.",
    },
  },

  actions: {
    run_heavy_appliances:
      "This may be a good time to run flexible appliances.",
    use_if_needed:
      "Use electricity now if you need to.",
    wait_if_possible:
      "Wait for a better time if your task can be delayed.",
  },

  context: {
    lower_than_usual:
      "Lower than usual for the recent market.",
    about_average:
      "About average for the recent market.",
    higher_than_usual:
      "Higher than usual for the recent market.",
  },

  temporal: {
    recently_passed: "Recently passed",
    very_soon: "Very soon",
    in_a_few_hours: "In a few hours",
    this_afternoon: "This afternoon",
    this_evening: "This evening",
    overnight: "Overnight",
    later_today: "Later today",
    tomorrow_around_this_time:
      "Tomorrow around this time",
  },

  learnPage: {
    hero: {
      title: "Understand WattWise",
      description:
        "See how official Alberta electricity data becomes a simple recommendation you can use.",
      chips: {
        data: "Official data",
        forecasts: "Five horizons",
        recommendations: "Clear recommendations",
      },
    },

    process: {
      title: "How WattWise works",
      description:
        "WattWise turns hourly electricity market information into five forecasts and one clear planning recommendation.",
      modelReview:
        "Models are periodically re-evaluated with newer market data and are used only after review and approval.",
      stepLabel: "Step",

      steps: {
        data: {
          title: "Official electricity data",
          description:
            "WattWise starts with public hourly electricity prices and Alberta electricity demand.",
        },
        patterns: {
          title: "Historical patterns",
          description:
            "The system compares current conditions with patterns found in several years of historical data.",
        },
        forecasts: {
          title: "Five forecast horizons",
          description:
            "Models estimate prices 1, 3, 6, 12, and 24 hours ahead. The interface displays only these five forecast horizons.",
        },
        recommendation: {
          title: "A clear recommendation",
          description:
            "The predicted prices are translated into Good time, Okay time, or Better to wait.",
        },
      },
    },

    recommendations: {
      title: "What the recommendations mean",
      description:
        "The recommendation helps you decide whether a flexible task should happen now or later.",

      good: {
        title: "Good time",
        description:
          "Prices are favourable compared with recent market conditions. This may be a useful time for flexible appliances.",
      },
      okay: {
        title: "Okay time",
        description:
          "Prices are acceptable. You can use electricity if needed, although a better forecast time may be available.",
      },
      wait: {
        title: "Better to wait",
        description:
          "Prices or market risk are elevated. Delaying a flexible task may be the safer choice.",
      },
    },

    dataSource: {
      title: "Where the data comes from",
      organization:
        "Alberta Electric System Operator (AESO)",
      description:
        "The Alberta Electric System Operator is responsible for the safe and reliable operation of Alberta's interconnected electricity system. AESO publishes the official hourly market information used by WattWise.",
      websiteLabel: "Visit the official AESO website",
      websiteUrl: "https://www.aeso.ca",

      items: {
        prices: "Hourly Alberta pool prices",
        forecastPrices: "AESO forecast prices",
        load: "Alberta Internal Load (AIL)",
        public:
          "Public Alberta electricity market information",
      },
    },

    confidence: {
      title: "How to use each forecast horizon",
      description:
        "Each horizon supports a different planning decision. Near-term forecasts are best for immediate choices, while longer horizons provide broader planning context.",

      horizons: {
        one: {
          label: "1 hour ahead",
          detail: "Most useful for immediate decisions",
        },
        three: {
          label: "3 hours ahead",
          detail: "Useful for short-term planning",
        },
        six: {
          label: "6 hours ahead",
          detail: "Useful for planning later today",
        },
        twelve: {
          label: "12 hours ahead",
          detail: "Use as a broader guide with more uncertainty",
        },
        twentyFour: {
          label: "24 hours ahead",
          detail: "Use as a reference for next-day planning",
        },
      },
    },

    limits: {
      eyebrow: "Planning responsibly",
      title: "Important limits",
      introduction:
        "WattWise supports planning, but it cannot guarantee a future electricity price.",
      detailsLabel: "What can change a forecast?",

      items: {
        prediction:
          "Forecasts are estimates based on historical and current market information.",
        events:
          "Unexpected outages, weather, demand, and market events can change prices quickly.",
        bill:
          "The displayed market price is not the same as your complete electricity bill.",
        planning:
          "Use WattWise as a planning aid rather than a financial guarantee.",
      },
    },

    cta: {
      eyebrow: "Next step",
      title: "Use the forecast in context",
      description:
        "Open Today to compare the current market price with WattWise’s five future forecast horizons.",
      label: "View today’s outlook",
    },
  },

  projectPage: {
    hero: {
      eyebrow: "Project",
      title: "WattWise",
      description:
        "An end-to-end machine learning application that turns Alberta electricity market data into clear, practical recommendations.",
      byline: "Built in Alberta",
      ctaTitle: "See WattWise in action",
      ctaDescription:
        "Compare the current price with five forecast horizons and get a clear recommendation.",
      ctaLabel: "View forecasts",
      disciplines: {
        data: "Data engineering",
        machineLearning: "Machine learning",
        product: "Full-stack product",
      },
    },

    story: {
      eyebrow: "Why WattWise",
      title: "The story",
      introduction:
        "Alberta electricity prices can change significantly from one hour to the next.",
      problem:
        "Most people do not have the time or technical background to interpret market prices, electricity demand, and forecasting data.",
      solution:
        "WattWise converts that complexity into simple recommendations that help users decide whether to use electricity now or consider waiting.",
    },

    highlights: {
      title: "Project highlights",
      description:
        "WattWise combines data engineering, machine learning, backend development, and responsive product design.",
      records: {
        value: "57,000+",
        label: "Hourly market records",
      },
      horizons: {
        value: "5",
        label: "Forecast horizons",
      },
      window: {
        value: "24 h",
        label: "Planning window",
      },
      system: {
        value: "End-to-end",
        label: "Data-to-interface system",
      },
    },

    journey: {
      title: "From data to decisions",
      description:
        "Each layer has a clear responsibility, from collecting official market data to presenting a practical recommendation.",
      startLabel: "Market data enters WattWise",
      endLabel:
        "A clear recommendation reaches the user",
      stepLabel: "Step",

      steps: {
        source: {
          title: "AESO market data",
          description:
            "Official hourly pool prices, forecast prices, and Alberta Internal Load provide the foundation.",
        },
        data: {
          title: "Data engineering",
          description:
            "Historical and recent records are cleaned, validated, standardized, and combined.",
        },
        features: {
          title: "Feature engineering",
          description:
            "Time, price history, market behaviour, and load signals become model-ready features.",
        },
        models: {
          title: "Machine learning",
          description:
            "Models estimate future prices and identify periods of elevated market risk.",
        },
        api: {
          title: "Prediction API",
          description:
            "PostgreSQL and Express provide normalized prediction responses to the application.",
        },
        product: {
          title: "React experience",
          description:
            "The interface converts predictions into clear recommendations for everyday planning.",
        },
      },
    },

    principles: {
      title: "Engineering principles",
      description:
        "WattWise was designed around reliable data, honest evaluation, and understandable product behaviour.",

      items: [
        {
          title: "Chronological validation",
          description:
            "Models are trained on earlier data and then evaluated on more recent periods.",
        },
        {
          title: "Leakage-aware evaluation",
          description:
            "Temporal boundaries prevent models from using information that would not yet be available when a forecast is produced.",
        },
        {
          title: "Leakage-safe threshold selection",
          description:
            "Thresholds were selected from training and validation data before the final model refit.",
        },
        {
          title: "Explainable recommendations",
          description:
            "Users receive clear guidance with understandable context instead of unexplained raw model outputs.",
        },
        {
          title: "Modular architecture",
          description:
            "Data, models, the worker, the API, and the interface are organized as separate responsibilities.",
        },
        {
          title: "Automated verification",
          description:
            "Python, API, and frontend tests protect the application through every change.",
        },
      ],
    },

    stack: {
      title: "Technology stack",
      description:
        "The application combines tools from data engineering, machine learning, backend systems, and frontend development.",

      technologies: [
        "Python",
        "Pandas",
        "scikit-learn",
        "PostgreSQL",
        "Node.js",
        "Express",
        "React",
        "JavaScript",
        "Docker",
        "Vite",
        "Vitest",
        "Jest",
        "Git",
      ],
    },

    developer: {
      title: "Meet the developer",
      name: "Joël-Hervé Akoun",
      roles:
        "Data Analyst · BI Developer · Data Engineer",
      location: "Edmonton, Alberta",
      education:
        "Artificial Intelligence and Data Analytics · Red Deer Polytechnic",
      description:
        "I build complete data products, from data engineering and machine learning to backend APIs and responsive web applications that help people make better decisions.",
      linkedInLabel: "View LinkedIn profile",
      linkedInUrl:
        "https://www.linkedin.com/in/joelakoun/",
      photoPath: "/joel.png",
      initials: "JHA",
      photoFallbackLabel: "Joël-Hervé Akoun initials",
    },

    reflection: {
      eyebrow: "Reflection",
      title: "What this project taught me",
      description:
        "Building WattWise taught me how to turn a predictive model into a product people can actually use. The work did not stop at model training: I had to organize the data, prevent temporal leakage, automate predictions, build a reliable API, and make the results understandable to users.",
    },

    signature: {
      label: "Designed and developed in Alberta by",
      name: "Joël-Hervé Akoun",
    },
  },

  pages: {
    now: {
      eyebrow: "Live decision",
      title: "Should I use electricity now?",
      description:
        "A clear recommendation based on the latest available Alberta electricity market conditions.",
      todayLink: "See today's forecast",
      todayLinkDescription:
        "Compare all five forecast horizons.",
    },

    today: {
      eyebrow: "Today planning",
      title: "When would be a better time?",
      description:
        "Five genuine forecasts show how prices may change over the next 24 hours.",
      exploreTitle: "Explore each forecast",
      exploreDescription:
        "Open the detailed forecasts to compare the recommendation at every horizon.",
    },

    learn: {
      title: "How WattWise works",
      description:
        "Plain-language details about the data, forecasts, and limits.",
    },
  },

  freshness: {
    forecastsCalculatedThrough:
      "Forecasts calculated from market data up to",
    observed: "Price observed at",

    observedPrice: {
      moderate: {
        title: "Observed price delayed",
        description:
          "The latest finalized price is older than usual. The recommendation below still uses that observed price.",
      },
      low: {
        title: "Observed price is stale",
        description:
          "This recommendation uses an older finalized price. Check its observation time before acting.",
      },
    },

    forecasts: {
      moderate: {
        title: "Forecasts delayed",
        description:
          "These forecasts use an older market-data hour than usual.",
      },
      low: {
        title: "Forecasts are stale",
        description:
          "These forecasts use old market data. Check the source-data time before acting.",
      },
    },
  },

  forecast: {
    bestTimeTitle: "Best forecast time",
    bestOpportunity: "Best opportunity",
    futurePriceLabel: "Lowest comparable forecast",
    currentObservedPriceLabel:
      "Current AESO market price",
    currentPriceSourceHour:
      "Market price hour",

    futureStatus: {
      available:
        "A best-time comparison is unavailable. Forecast details remain visible below.",
      none_remaining:
        "No future forecast targets remain. The five-point forecast remains visible below for context.",
      reference_only:
        "Only the +24-hour persistence reference remains in the future. It is context, not a savings opportunity.",
      provenance_unavailable:
        "Forecast provenance cannot support a best-time claim. The five points remain visible below.",
    },

    horizons: {
      one: "1 hour",
      three: "3 hours",
      six: "6 hours",
      twelve: "12 hours",
      twentyFour: "24 hours",
    },

    comparison: {
      lowerEyebrow: "Possible saving",
      lowerTitle: "A lower price is forecast",
      lowerBefore: "The lowest forecast is",
      lowerAfter:
        "¢/kWh below the current AESO market price.",

      sameEyebrow: "No expected saving",
      sameTitle:
        "Waiting is not expected to lower the price",
      sameDescription:
        "The lowest future forecast matches the current AESO market price.",
      sameBadge: "Same as now",

      currentEyebrow: "Current price is better",
      currentTitle:
        "The current price is already lower",
      currentBefore:
        "The current AESO market price is",
      currentAfter:
        "¢/kWh below the lowest future forecast.",
      currentBadge: "Now is lower",

      unavailableEyebrow:
        "Comparison unavailable",
      unavailableTitle:
        "A lower price cannot be confirmed",
      unavailableDescription:
        "The current AESO market price is unavailable, so WattWise cannot determine whether waiting would lower the price.",
      unavailableBadge:
        "Current price unavailable",
    },

    currentPriceReference: "Current price",
    nowLabel: "Now",
    observedPriceAt: "Observed price at",
    sameAsObservedPrice: "Same as observed price",
    todayLabel: "Today",
    tomorrowLabel: "Tomorrow",
    expectedPrice: "Expected price",
    bestTimeExplanation:
      "Lowest predicted price in the next 24 hours.",
    tomorrowCaution:
      "The 24-hour forecast is less reliable. Use it as a planning guide, not a guarantee.",
    persistenceReferenceTitle:
      "Persistence reference",
    persistenceReferenceDescription:
      "This value uses the previous-hour observed-price feature as a persistence reference. It remains visible for transparency and is not treated as a savings opportunity.",
    timelineLabel:
      "Five forecast points for today",
    viewForecasts: "Forecast details",
    priceComparison: "Price comparison",
    forecastDetails: "Forecast details",
    hideDetails: "Hide details",
    priceTrendTitle: "Price trend",
    priceTrendDescription:
      "The first point is the current AESO market price. The next five points are model forecasts. The smooth line is only a visual guide.",
  },

  explanations: {
    lower_than_usual:
      "The predicted price is favourable compared with the recent market.",
    about_average:
      "The observed price is within the recent market's normal range.",
    acceptable_market_risk:
      "The predicted price is acceptable, but market risk is increasing.",
    higher_than_usual:
      "The predicted price is high compared with the recent market.",
  },

  states: {
    loading:
      "Checking the latest electricity data…",
    errorTitle:
      "WattWise could not load the latest update.",
    retry: "Try again",
  },

  price: {
    label: "Price now",
    currentTime: "Current Alberta time",
    marketHour: "Market hour",
    kinds: {
      actual:
        "Finalized AESO price for the current market hour.",
      forecast:
        "AESO estimate for the current market hour.",
      fallback_actual:
        "Latest finalized AESO price because current-hour data is unavailable.",
    },
  },

  confidence: {
    high: "Latest data is current",
    moderate: "Latest data may be delayed",
    low: "Latest data is stale",
  },

  creator: {
    label: "Created by",
    name: "Joël-Hervé Akoun",
    initials: "JA",
    photoPath: "/joel.png",
    linkedInUrl:
      "https://www.linkedin.com/in/joelakoun/",
    linkedInLabel: "View LinkedIn profile",
  },

  footer: {
    disclaimer:
      "Your final bill depends on your retailer and electricity plan.",
  },
};
