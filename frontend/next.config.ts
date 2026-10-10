import type { NextConfig } from "next";

// В образе (ADR-004) frontend собирается статически и отдаётся backend с того же origin.
const isStaticExport = process.env.NEXT_OUTPUT === "export";

const staticExport: NextConfig = { output: "export" };

// В разработке браузер ходит в API через тот же origin: CORS на backend не нужен.
const proxiedToBackend: NextConfig = {
  async rewrites() {
    const apiUrl = process.env.API_URL ?? "http://localhost:8000";
    return [
      { source: "/api/v1/:path*", destination: `${apiUrl}/api/v1/:path*` },
    ];
  },
};

const nextConfig: NextConfig = {
  ...(isStaticExport ? staticExport : proxiedToBackend),
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
