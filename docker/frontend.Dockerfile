# ─── MemoryLeak Frontend Dockerfile ──────────────────────────────────────────
# Multi-stage build:
#   deps     — installs Node dependencies
#   builder  — builds Next.js production bundle
#   runtime  — minimal production image with the built app
#
# Development: the docker-compose.yml mounts the source as a volume
# and uses `npm run dev` for hot reload.

# ─── Stage 1: deps ────────────────────────────────────────────────────────────
FROM node:20-slim AS deps

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json* ./

# Install all dependencies (including devDependencies for building)
RUN npm ci


# ─── Stage 2: builder ─────────────────────────────────────────────────────────
FROM node:20-slim AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build environment variable required at build time
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

RUN npm run build


# ─── Stage 3: runtime ─────────────────────────────────────────────────────────
FROM node:20-slim AS runtime

WORKDIR /app

ENV NODE_ENV=production

# Create a non-root user
RUN groupadd --gid 1001 nextjs \
    && useradd --uid 1001 --gid nextjs --shell /bin/bash --create-home nextjs

# Copy only the files needed to run the built app
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

CMD ["node", "server.js"]
