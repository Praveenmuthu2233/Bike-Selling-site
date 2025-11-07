# Use Node.js 18
FROM node:18

# Create app directory
WORKDIR /app

# Copy root package files (if needed)
COPY package*.json ./

# Install dependencies (for root if used)
RUN npm install || true

# Copy entire project
COPY . .

# Move into the folder where server.js exists
WORKDIR /app/my-node-app

# Install dependencies of my-node-app
COPY my-node-app/package*.json ./
RUN npm install

# Expose port
EXPOSE 8080

# Start your server
CMD ["node", "server.js"]
