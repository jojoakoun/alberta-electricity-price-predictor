function logUnhandledError(error, req) {
  if (
    req.log
    && typeof req.log.error === "function"
  ) {
    req.log.error(
      { err: error },
      "Unhandled request error",
    );
    return;
  }

  console.error(
    "Unhandled request error",
    error,
  );
}

function isExposedClientError(error) {
  return Boolean(
    error
    && error.expose === true
    && Number.isInteger(error.statusCode)
    && error.statusCode >= 400
    && error.statusCode < 500,
  );
}

function errorHandler(error, req, res, next) {
  if (res.headersSent) {
    return next(error);
  }

  logUnhandledError(error, req);

  // Database and unexpected errors stay internal. Only an explicitly exposed
  // client error may provide its public status, code, and message.
  if (isExposedClientError(error)) {
    return res.status(error.statusCode).json({
      error: {
        code: error.code || "INVALID_REQUEST",
        message: error.message,
      },
    });
  }

  return res.status(500).json({
    error: {
      code: "INTERNAL_SERVER_ERROR",
      message: "An unexpected error occurred.",
    },
  });
}

module.exports = { errorHandler };
