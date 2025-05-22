FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy only package files to install dependencies first (for cache)
COPY package.json package-lock.json* ./

# Install both app and test dependencies
RUN npm install && \
    npm install --save-dev jest @testing-library/react @testing-library/jest-dom @testing-library/user-event

# Copy the rest of the app files
COPY . .

# Run unit tests (will fail the build if any test fails)
RUN npm test -- --watchAll=false

# Build the production version of the app
RUN npm run build

# Expose port
EXPOSE 3000

# Serve the built app
CMD ["npx", "serve", "-s", "build"]
