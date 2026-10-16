FROM node:22-alpine
WORKDIR /app

# Install dependencies and code
COPY package*.json ./
RUN npm install
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start the Vite development server
CMD ["npm", "run", "dev"]