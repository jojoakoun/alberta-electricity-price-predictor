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

  pages: {
    now: {
      title: "Should I use electricity now?",
      todayLink: "See the rest of the day",
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

  footer: {
    disclaimer:
      "Your final bill depends on your retailer and electricity plan.",
  },
} as const;
