// frontend/src/app/page.tsx

/**
 * Main Page Component
 * 
 * NEXT.JS APP ROUTER:
 * - Files in src/app/ become routes
 * - page.tsx = the page content
 * - layout.tsx = wrapper around all pages
 * 
 * This file renders the Dashboard on the home page (/).
 */

import { Dashboard } from '@/components/Dashboard';

/**
 * Home page.
 * 
 * In Next.js App Router, page components can be async or regular functions.
 * This one is simple - just render the Dashboard.
 * 
 * export default makes this the default export (what gets rendered).
 */
export default function Home() {
  return <Dashboard />;
}
