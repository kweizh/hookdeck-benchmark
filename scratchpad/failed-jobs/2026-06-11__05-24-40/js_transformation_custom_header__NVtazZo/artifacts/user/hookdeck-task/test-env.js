addHandler("transform", (request, context) => {
  request.headers["x-process-env"] = (typeof process !== 'undefined' && process.env && process.env.MY_SECRET_ENV) || "no process";
  request.headers["x-context-env"] = (context && context.env && context.env.MY_SECRET_ENV) || "no context env";
  return request;
});
