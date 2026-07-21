const {
  errorHandler,
} = require("../src/middleware/error-handler");

function createResponse() {
  return {
    headersSent: false,
    status: jest.fn().mockReturnThis(),
    json: jest.fn().mockReturnThis(),
  };
}

describe("Error handler", () => {
  let consoleError;

  beforeEach(() => {
    consoleError = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});
  });

  afterEach(() => {
    consoleError.mockRestore();
  });

  test("returns a generic response when request logging is disabled", () => {
    const error = Object.assign(
      new Error("duplicate key detail"),
      { code: "23505" },
    );
    const response = createResponse();

    expect(() =>
      errorHandler(
        error,
        {},
        response,
        jest.fn(),
      ),
    ).not.toThrow();

    expect(consoleError).toHaveBeenCalledWith(
      "Unhandled request error",
      error,
    );
    expect(response.status).toHaveBeenCalledWith(500);
    expect(response.json).toHaveBeenCalledWith({
      error: {
        code: "INTERNAL_SERVER_ERROR",
        message: "An unexpected error occurred.",
      },
    });
  });

  test("preserves an explicitly exposed client error", () => {
    const error = Object.assign(
      new Error("The request value is invalid."),
      {
        code: "INVALID_REQUEST",
        expose: true,
        statusCode: 422,
      },
    );
    const response = createResponse();
    const request = {
      log: {
        error: jest.fn(),
      },
    };

    errorHandler(
      error,
      request,
      response,
      jest.fn(),
    );

    expect(request.log.error).toHaveBeenCalledWith(
      { err: error },
      "Unhandled request error",
    );
    expect(consoleError).not.toHaveBeenCalled();
    expect(response.status).toHaveBeenCalledWith(422);
    expect(response.json).toHaveBeenCalledWith({
      error: {
        code: "INVALID_REQUEST",
        message: "The request value is invalid.",
      },
    });
  });

  test("does not trust a client status without an explicit exposure marker", () => {
    const error = Object.assign(
      new Error("Internal validation detail"),
      {
        code: "INTERNAL_VALIDATION_CODE",
        statusCode: 400,
      },
    );
    const response = createResponse();

    errorHandler(
      error,
      {},
      response,
      jest.fn(),
    );

    expect(response.status).toHaveBeenCalledWith(500);
    expect(response.json).toHaveBeenCalledWith({
      error: {
        code: "INTERNAL_SERVER_ERROR",
        message: "An unexpected error occurred.",
      },
    });
  });

  test("delegates after response headers have been sent", () => {
    const error = new Error("stream failed");
    const response = {
      headersSent: true,
    };
    const next = jest.fn();

    errorHandler(error, {}, response, next);

    expect(next).toHaveBeenCalledWith(error);
    expect(consoleError).not.toHaveBeenCalled();
  });
});
