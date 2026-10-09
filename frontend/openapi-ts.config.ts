import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "../api/openapi.yaml",
  output: "lib/api/generated",
});
