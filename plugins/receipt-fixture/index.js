export default function register(api) {
  api.registerTool({
    name: "receipt_fixture_status",
    description: "Return a fixed readiness response for this inert demo.",
    parameters: { type: "object", properties: {}, additionalProperties: false },
    async execute() {
      return { content: [{ type: "text", text: "ready" }] };
    },
  });
}
