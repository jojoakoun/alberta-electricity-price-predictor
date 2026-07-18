function errorHandler(error, req, res, next) {
  if (res.headersSent) {
    return next(error);
  }

  req.log.error({ err: error }, "Unhandled request error");

  return res.status(error.statusCode || 500).json({
    error: {
      code: error.code || "INTERNAL_SERVER_ERROR",
      message:
        error.statusCode && error.statusCode < 500
          ? error.message
          : "An unexpected error occurred.",
    },
  });
}

module.exports = { errorHandler };
