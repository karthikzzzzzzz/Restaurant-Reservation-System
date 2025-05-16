# Use a lightweight Node.js image
FROM node:22-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json into the container
COPY package.json /app/package.json
COPY package-lock.json /app/package-lock.json

# Install the dependencies
RUN npm install

# Copy the rest of the application files (including your src folder) into the container
COPY . /app

# Run the build command
RUN npm run build

# Expose the port for the frontend service
EXPOSE 3000

# Start the app
CMD ["npm", "start"]