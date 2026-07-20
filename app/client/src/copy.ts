import type { RecommendationLevel } from "./types/recommendation";

export const copy = {
  brand: {
    name: "WattWise",
    tagline: "Use electricity at a smarter time.",
  },

  navigation: {
    now: "Now",
    today: "Today",
    learn: "Learn",
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
        "Prices are reasonable, but a better time may be coming.",
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
  } satisfies Record<
    RecommendationLevel,
    {
      label: string;
      defaultExplanation: string;
    }
  >,

  actions: {
    run_heavy_appliances:
      "This may be a good time to run flexible appliances.",
    use_if_needed:
      "Use electricity now if you need to.",
    wait_if_possible:
      "Wait for a better time if your task can be delayed.",
  },

  context: {
    lower_than_usual: "Lower than usual for the recent market.",
    about_average: "About average for the recent market.",
    higher_than_usual: "Higher than usual for the recent market.",
  },

  temporal: {
    very_soon: "Very soon",
    in_a_few_hours: "In a few hours",
    this_afternoon: "This afternoon",
    this_evening: "This evening",
    overnight: "Overnight",
    later_today: "Later today",
    tomorrow_around_this_time: "Tomorrow around this time",
  },

  learnPage: {
    hero: {
      title: "Understand WattWise",
      description:
        "See how official Alberta electricity data becomes a simple recommendation you can use.",
    },

    process: {
      title: "How WattWise works",
      description:
        "WattWise turns hourly electricity market information into five forecasts and one clear planning recommendation.",

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
          title: "Five genuine forecasts",
          description:
            "Prices are estimated for 1, 3, 6, 12, and 24 hours ahead. WattWise does not invent points between those forecasts.",
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
        public: "Public Alberta electricity market information",
      },
    },

    confidence: {
      title: "Why forecast confidence changes",
      description:
        "Near-term forecasts usually have more recent information available. Forecasts become less certain as the time horizon increases.",

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
          detail: "More uncertainty is expected",
        },
        twentyFour: {
          label: "24 hours ahead",
          detail: "Use as a planning guide",
        },
      },
    },

    limits: {
      title: "Important limits",
      introduction:
        "WattWise supports planning, but it cannot guarantee a future electricity price.",

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
  },

  pages: {
    now: {
      title: "Should I use electricity now?",
      todayLink: "See today's forecast",
    },

    today: {
      title: "When would be a better time?",
      description:
        "Five genuine forecasts show how prices may change.",
    },

    learn: {
      title: "How WattWise works",
      description:
        "Plain-language details about the data, forecasts, and limits.",
    },
  },

  freshness: {
    updated: "Updated",
    delayed: "Data delayed",
  },

  forecast: {
    bestTimeTitle: "Best forecast time",
    expectedPrice: "Expected price",
    bestTimeExplanation: "Lowest predicted price in the next 24 hours.",
    tomorrowCaution: "The 24-hour forecast is less reliable. Use it as a planning guide, not a guarantee.",
    timelineLabel: "Five forecast points for today",
    viewForecasts: "Forecast details",
    priceComparison: "Price comparison",
    forecastDetails: "Forecast details",
    hideDetails: "Hide details",
  },

  explanations: {
    lower_than_usual: "The predicted price is favourable compared with the recent market.",
    acceptable_market_risk: "The predicted price is acceptable, but market risk is increasing.",
    higher_than_usual: "The predicted price is high compared with the recent market.",
  },

  states: {
    loading: "Checking the latest electricity data…",
    errorTitle: "WattWise could not load the latest update.",
    retry: "Try again",
  },

  price: {
    label: "Current electricity price",
  },

  confidence: {
    high: "Latest recommendation available",
    moderate: "The latest update may be delayed",
    low: "Recommendation unavailable",
  },

  creator: {
    label: "Created by",
    name: "Joël-Hervé Akoun",
    initials: "JA",
    photoPath: "/joel.png",
    linkedInUrl: "https://www.linkedin.com/in/joelakoun/",
    linkedInLabel: "View LinkedIn profile",
  },

  footer: {
    disclaimer:
      "Your final bill depends on your retailer and electricity plan.",
  },
} as const;
