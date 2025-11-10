# Use the official Node.js 20 image
FROM node:20

# Set the working directory in the container
WORKDIR /app

# Enable corepack to use pnpm
RUN corepack enable
RUN corepack prepare pnpm --activate

# Copy package.json and pnpm-lock.yaml
COPY package.json pnpm-lock.yaml ./
COPY prisma ./prisma/

# Install dependencies
RUN pnpm install

# Copy the rest of the application code
COPY . .

# Run the style-dictionary build
RUN pnpm style-dictionary

# Expose the port the app runs on
EXPOSE 3000

# The command to run when the container starts
CMD ["pnpm", "dev"]