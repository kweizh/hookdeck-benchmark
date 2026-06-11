export default function (request) {
  if (!request.body || typeof request.body.required_field === "undefined") {
    throw new Error("Missing required_field");
  }
  return request;
}
