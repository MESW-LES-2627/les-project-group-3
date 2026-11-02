import { betterAuth } from "better-auth";
import { nextCookies } from "better-auth/next-js";
import { jwt } from "better-auth/plugins";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  // Better-Auth tables live in their own schema, isolated from the domain's `patas`.
  options: "-c search_path=patas_auth",
});

export const auth = betterAuth({
  baseURL: process.env.BETTER_AUTH_URL,
  secret: process.env.BETTER_AUTH_SECRET,
  database: pool,
  emailAndPassword: { enabled: true },
  // Real UUID ids, so the JWT `sub` can be the primary key of patas.users.
  advanced: { database: { generateId: "uuid" } },
  plugins: [
    jwt({
      jwt: {
        // Only identity goes in the token. Authority (e.g. admin) is never a claim.
        definePayload: ({ user }) => ({ email: user.email, name: user.name }),
      },
    }),
    nextCookies(), // must stay the last plugin
  ],
});

