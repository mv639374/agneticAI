# Frontend

```bash
# From agenticAI root directory
cd agenticAI

# Create Next.js app with TypeScript, Tailwind, App Router, ESLint
npx create-next-app@latest frontend --typescript --tailwind --app --eslint

# When prompted, answer:
# ✓ Would you like to use `src/` directory? → Yes
# ✓ Would you like to use App Router? → Yes
# ✓ Would you like to use Turbopack? → No (optional)
# ✓ Would you like to customize the import alias? → No

# Navigate to frontend
cd frontend

# Initialize shadcn/ui
npx shadcn@latest init

# When prompted, answer:
# ✓ Preflight checks
# ✓ Which style would you like to use? → New York (or Default)
# ✓ Which color would you like to use as base color? → Slate (or your choice)
# ✓ Would you like to use CSS variables for colors? → Yes

# Install initial shadcn/ui components
npx shadcn@latest add button card input label textarea badge avatar
npx shadcn@latest add dropdown-menu popover dialog alert
```

---

### frontend/next.config.ts (Update for standalone output)

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker optimization
  output: 'standalone',
  
  // Disable telemetry
  telemetry: false,
  
  // API proxy configuration (optional - for avoiding CORS in production)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL 
          ? `${process.env.NEXT_PUBLIC_API_URL}/:path*`
          : 'http://backend:8000/:path*', // Docker service name
      },
    ];
  },
};

export default nextConfig;
```