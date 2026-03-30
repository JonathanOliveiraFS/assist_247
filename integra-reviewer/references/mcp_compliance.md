# MCP Contract Compliance Review

## 1. Tool Definitions
- [ ] Every tool in an MCP server has a clear `name`, `description`, and `inputSchema` (JSON Schema).
- [ ] Tool descriptions are semantic and clear for the LLM to understand when to invoke them.
- [ ] Arguments follow standard types (string, number, boolean, array, object).

## 2. Server Handshake & Lifecycle
- [ ] MCP Server correctly handles `initialize` request with capabilities.
- [ ] Error responses are standard JSON-RPC format with relevant error codes.
- [ ] Tool execution results are returned as structured data (text, images, or JSON).

## 3. Client Interaction (FastAPI Bot)
- [ ] Client uses `mcp-sdk` or a robust `async` implementation.
- [ ] Connection timeouts are enforced to prevent WhatsApp webhook expiration (e.g., < 30 seconds).
- [ ] Security: Server endpoints (URLs) are fetched from `MCP_SERVERS_CONFIG`.

## 4. Best Practices
- [ ] Keep tools focused (e.g., `get_agenda` vs. `manage_entire_clinic`).
- [ ] Always return helpful error messages for the LLM to recover from.
