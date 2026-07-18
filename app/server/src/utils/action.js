const ACTION_KEYS = Object.freeze({
  recommended: "run_heavy_appliances",
  acceptable: "use_if_needed",
  avoid: "wait_if_possible",
});

function getActionKey(recommendation) {
  const actionKey = ACTION_KEYS[recommendation];

  if (!actionKey) {
    throw new Error(`Unsupported public recommendation: ${recommendation}`);
  }

  return actionKey;
}

module.exports = {
  getActionKey,
};
