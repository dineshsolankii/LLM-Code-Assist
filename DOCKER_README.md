# Docker Setup for LLM-Code-Assist

This document provides instructions for sharing and running the LLM-Code-Assist application using Docker.

## Prerequisites for Running the Application

- [Docker](https://docs.docker.com/get-docker/) (version 20.10.0 or higher)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0.0 or higher)

## Quick Start (For the Recipient)

1. Extract the project files to a directory on your machine.

2. Open a terminal and navigate to the extracted project directory.

3. Start the application using Docker Compose:

   ```bash
   docker-compose up -d
   ```

   This will:
   - Build the LLM-Code-Assist container
   - Pull and start the Ollama container
   - Create necessary networks and volumes
   - Start both services in detached mode

4. Access the application in your web browser at:

   ```
   http://localhost:8001
   ```

5. The first time you run the application, Ollama will need to download the LLM model (deepseek-coder-v2:16b). This may take some time depending on your internet connection.

## Important Notes

- The application data will be persisted in Docker volumes and the `./projects` and `./data` directories.
- The Ollama service runs on port 11434 and the LLM-Code-Assist web interface runs on port 8001.
- If you need to change ports, edit the `docker-compose.yml` file.

## Stopping the Application

To stop the application:

```bash
docker-compose down
```

To stop and remove all data (including volumes):

```bash
docker-compose down -v
```

## Troubleshooting

### Common Issues

1. **Ollama Model Download Issues**
   - If you encounter issues with the LLM model, you can manually pull it using:
     ```bash
     docker exec -it ollama-server ollama pull deepseek-coder-v2:16b
     ```

2. **Viewing Application Logs**
   - To view logs for all services:
     ```bash
     docker-compose logs -f
     ```
   - To view logs for a specific service:
     ```bash
     docker-compose logs -f llm-code-assist
     ```

3. **Restarting Services**
   - To restart a specific service:
     ```bash
     docker-compose restart llm-code-assist
     ```
   - To restart all services:
     ```bash
     docker-compose restart
     ```

4. **Port Conflicts**
   - If ports 8001 or 11434 are already in use, edit the `docker-compose.yml` file to change the port mappings.

5. **Container Not Starting**
   - Check the container status:
     ```bash
     docker-compose ps
     ```
   - If a container is not running, check its logs for errors.

### Advanced Troubleshooting

- **Rebuilding the Application**
  ```bash
  docker-compose down
  docker-compose build --no-cache
  docker-compose up -d
  ```

- **Checking Resource Usage**
  ```bash
  docker stats
  ```

- **Accessing Container Shell**
  ```bash
  docker exec -it llm-code-assist bash
  ```
